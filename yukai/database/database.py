import  datetime
import  gridfs
import  pathlib
import  subprocess
import  time

from    bson                        import  ObjectId
from    contextlib                  import  contextmanager
from    logger                      import  Logger
from    models.models               import  ClienteInfo, SrcDocInfo, IaDcoInfo, BIaDcoInfo
from    pymongo                     import  MongoClient, ReturnDocument
from    pymongo.database            import  Database
from    pymongo.errors              import  ServerSelectionTimeoutError
from    tools.tools                 import  is_plaint_text_file
#--------------------------------------------------------------------------------------------------

class ClientesDocumentStore:
    def __init__(self, log: Logger,
                       docker_file  = None,
                       mongo_uri    = "mongodb://localhost:27017",
                       db_name      = "docstore"):
        self._log           = log
        self._docker_file   = docker_file
        self._mongo_uri     = mongo_uri
        self._client        = MongoClient(mongo_uri)
        self._db: Database  = self._client[db_name]
        self._fs            = gridfs.GridFS(self._db)
    #----------------------------------------------------------------------------------------------

    # ------------------ Mongo Ready ---------------------

    def is_mongo_ready(self, uri=None, timeout=1):
        try:
            if uri is None: uri = self._mongo_uri
            client = MongoClient(uri, serverSelectionTimeoutMS=timeout * 1000)
            client.admin.command('ping')
            return True
        except ServerSelectionTimeoutError:
            return False
    #----------------------------------------------------------------------------------------------

    def ensure_mongo_ready(self, uri=None):
        if uri is None: uri = self._mongo_uri
        else: self._mongo_uri = uri

        self._log.info("Comprobando el estado de MongoDB")
        if self.is_mongo_ready(uri):
            self._log.info("✅ MongoDB ya está disponible.")
            return True

        self._log.info("🚀 MongoDB no está disponible. Iniciando con Docker Compose...")

        if self._docker_file:
            subprocess.run(["docker", "compose", "-f", self._docker_file, "up", "-d", "mongo"], check=True)
        else:
            subprocess.run(["docker", "compose", "up", "-d", "mongo"], check=True)

        for i in range(20):
            if self.is_mongo_ready(uri):
                self._log.info("✅ MongoDB está listo.")
                return True
            self._log.info(f"⏳ Esperando que MongoDB arranque... ({i+1}/20)")
            time.sleep(2)

        return False
    #----------------------------------------------------------------------------------------------

    def setup_db(self):
        self._db.pretrained_docs.create_index("filename", unique=True)
        if self._db.counters.find_one({"_id": "file_id"}) is None:
            self._db.counters.insert_one({"_id": "file_id", "seq": 0})
    #----------------------------------------------------------------------------------------------

    @contextmanager
    def transaction(self):
        self.ensure_mongo_ready()
        with self._client.start_session() as session:
            try:
                with session.start_transaction():
                    yield session
            except Exception as e:
                self._log.error(f"❌ Error en transacción: {e}")
                raise
    #----------------------------------------------------------------------------------------------

    # ------------------ Helpers ---------------------
    def _validate_object_id(self, value):
        try:
            return ObjectId(value)
        except Exception:
            raise ValueError(f"ID inválido: {value}")
    #----------------------------------------------------------------------------------------------

    def _check_source_exists(self, source_id):
        source_id = self._validate_object_id(source_id)
        if not self._db.source_docs.find_one({"_id": source_id}):
            raise ValueError(f"Documento fuente con id {source_id} no existe.")
        return source_id
    #----------------------------------------------------------------------------------------------

    def _check_iadoc_exists(self, iadoc_id):
        iadoc_id = self._validate_object_id(iadoc_id)
        if not self._db.iadocs.find_one({"_id": iadoc_id}):
            raise ValueError(f"IADOC con id {iadoc_id} no existe.")
        return iadoc_id
    #----------------------------------------------------------------------------------------------

    # ------------------ Contadores ---------------------

    def get_next_file_id(self):
        counter = self._db.counters.find_one_and_update(
            {"_id": "file_id"},
            {"$inc": {"seq": 1}},
            upsert=True,
            return_document=ReturnDocument.AFTER
        )
        return counter["seq"]
    #----------------------------------------------------------------------------------------------

    # ------------------ Clientes -----------------------

    def add_cliente(self,   nombre: str, 
                            apellidos: str, 
                            sexo: str, 
                            fecha_nacimiento: datetime.datetime, 
                            dni: str, 
                            id_interno: str,
                            src_docs: list[dict],
                            iadocs: list[dict],
                            biadocs: list[dict]):
        doc = {
            "owner": id_interno,
            "nombre": nombre,
            "apellidos": apellidos,
            "sexo": sexo,
            "fecha_nacimiento": fecha_nacimiento,
            "dni": dni
        }
        return self._db.clientes.insert_one(doc).inserted_id
    #----------------------------------------------------------------------------------------------

    def get_all_clientes(self) -> list[ClienteInfo]:
        ret = []
        for record in self._db.clientes.find({}):
            ret.append(ClienteInfo(record["nombre"],
                                   record["apellidos"],
                                   record["sexo"],
                                   record["fecha_nacimiento"],
                                   record["dni"],
                                   record["owner"],
                                   record["_id"]))
        return ret
    #----------------------------------------------------------------------------------------------

    def get_cliente_by_id_interno(self, id: str) -> ClienteInfo | None:
        record = self._db.clientes.find_one({"owner": id})
        if record:
            return ClienteInfo(record["nombre"],
                               record["apellidos"],
                               record["sexo"],
                               record["fecha_nacimiento"],
                               record["dni"],
                               record["owner"],
                               record["_id"])
        return None
    #----------------------------------------------------------------------------------------------

    def get_cliente_by_db_id(self, db_id: str) -> ClienteInfo | None:
        record = self._db.clientes.find_one({"_id": self._validate_object_id(db_id)})
        if record:
            return ClienteInfo(record["nombre"],
                               record["apellidos"],
                               record["sexo"],
                               record["fecha_nacimiento"],
                               record["dni"],
                               record["owner"],
                               record["_id"])
        return None
    #----------------------------------------------------------------------------------------------

    def delete_cliente(self, owner):
        with self.transaction() as session:
            try:
                # 1. Eliminar GridFS asociado a source_docs
                for record in self._db.source_docs.find({"owner": owner}, {"gridfs_file_id": 1}):
                    gridfs_id = record.get("gridfs_file_id")
                    if gridfs_id:
                        self._fs.delete(gridfs_id)

                # 2. Eliminar GridFS asociado a iadocs
                for record in self._db.iadocs.find({"owner": owner}, {"gridfs_file_id": 1}):
                    gridfs_id = record.get("gridfs_file_id")
                    if gridfs_id:
                        self._fs.delete(gridfs_id)

                # 3. Eliminar GridFS asociado a biadocs
                for record in self._db.biadocs.find({"owner": owner}, {"gridfs_file_id": 1}):
                    gridfs_id = record.get("gridfs_file_id")
                    if gridfs_id:
                        self._fs.delete(gridfs_id)

                # 4. Borrar documentos de las colecciones
                self._db.source_docs.delete_many({"owner": owner}, session=session)
                self._db.iadocs.delete_many({"owner": owner}, session=session)
                self._db.biadocs.delete_many({"owner": owner}, session=session)

                # 5. Borrar cliente
                self._db.clientes.delete_many({"owner": owner}, session=session)

            except Exception as e:
                self._log.error(f"❌ Error durante eliminación del cliente: {e}")
                raise

        return True
    #----------------------------------------------------------------------------------------------

    # ------------------ Source Docs ---------------------

    def add_source_doc(self, owner, filename, file_input: pathlib.Path | bytes, source_created_at: datetime.datetime):
        is_plain = False
        mime = None

        if isinstance(file_input, pathlib.Path):
            is_plain, mime = is_plaint_text_file(file_input)
            with open(file_input, "rb") as f:
                content_data = f.read()
        elif isinstance(file_input, bytes):
            content_data = file_input
            mime = "application/octet-stream"
        else:
            raise TypeError("file_input debe ser pathlib.Path o bytes")

        file_id = self._fs.put(content_data, filename=filename, owner=owner, mime=mime, type="source")

        doc = {
            "owner": owner,
            "filename": filename,
            "mime": mime,
            "gridfs_file_id": file_id,
            "created_at": datetime.datetime.now(datetime.timezone.utc),
            "source_created_at": source_created_at,
            "size_bytes": len(content_data)
        }
        return self._db.source_docs.insert_one(doc).inserted_id
    #----------------------------------------------------------------------------------------------

    def get_all_source_docs(self, owner) -> list[SrcDocInfo]:
        ret = []
        for record in self._db.source_docs.find({"owner": owner}):
            binary_content = self._fs.get(record["gridfs_file_id"]).read()
            ret.append(SrcDocInfo(
                record["_id"],
                record["owner"],
                record["filename"],
                None,
                record["mime"],
                record["created_at"],
                record["source_created_at"],
                record["size_bytes"],
                binary_content
            ))
        return ret
    #----------------------------------------------------------------------------------------------

    def get_all_source_meta(self, owner) -> list[SrcDocInfo]:
        ret = []
        for record in self._db.source_docs.find({"owner": owner}, {"gridfs_file_id": 0}):
            ret.append(SrcDocInfo(
                record["_id"],
                record["owner"],
                record["filename"],
                None,
                record["mime"],
                record["created_at"],
                record["source_created_at"],
                record["size_bytes"]
            ))
        return ret
    #----------------------------------------------------------------------------------------------

    # ------------------ IADOCs ---------------------

    def add_iadoc(self, owner, filename, file_input: pathlib.Path | bytes, source_id, source_mime, source_created_at: datetime.datetime, tokens):
        source_id = self._check_source_exists(source_id)

        if isinstance(file_input, pathlib.Path):
            with open(file_input, "rb") as f:
                content_data = f.read()
        elif isinstance(file_input, bytes):
            content_data = file_input
        else:
            raise TypeError("file_input debe ser pathlib.Path o bytes")

        file_id = self._fs.put(content_data, filename=filename, owner=owner, type="iadoc")

        doc = {
            "owner": owner,
            "filename": filename,
            "gridfs_file_id": file_id,
            "source_ref": source_id,
            "source_mime": source_mime,
            "source_created_at": source_created_at,
            "created_at": datetime.datetime.now(datetime.timezone.utc),
            "size_bytes": len(content_data),
            "tokens": tokens
        }
        return self._db.iadocs.insert_one(doc).inserted_id
    #----------------------------------------------------------------------------------------------

    def get_all_iadocs(self, owner) -> list[IaDcoInfo]:
        ret = []
        for record in self._db.iadocs.find({"owner": owner}):
            binary_content = self._fs.get(record["gridfs_file_id"]).read()
            ret.append(IaDcoInfo(
                record["_id"],
                record["owner"],
                record["filename"],
                None,
                record["source_ref"],
                record["source_mime"],
                record["source_created_at"],
                record["created_at"],
                record["size_bytes"],
                record["tokens"],
                binary_content
            ))
        return ret
    #----------------------------------------------------------------------------------------------

    def get_all_iadoc_meta(self, owner) -> list[IaDcoInfo]:
        ret = []
        for record in self._db.iadocs.find({"owner": owner}, {"gridfs_file_id": 0}):
            ret.append(IaDcoInfo(
                record["_id"],
                record["owner"],
                record["filename"],
                None,
                record["source_ref"],
                record["source_mime"],
                record["source_created_at"],
                record["created_at"],
                record["size_bytes"],
                record["tokens"]
            ))
        return ret
    #----------------------------------------------------------------------------------------------

    # ------------------ BIADOCs ---------------------

    def add_biadoc(self, owner, filename, file_input: pathlib.Path | bytes, source_id, iadoc_id, source_mime, source_created_at: datetime.datetime, tokens):
        source_id = self._check_source_exists(source_id)
        iadoc_id = self._check_iadoc_exists(iadoc_id)

        if isinstance(file_input, pathlib.Path):
            with open(file_input, "rb") as f:
                content_data = f.read()
        elif isinstance(file_input, bytes):
            content_data = file_input
        else:
            raise TypeError("file_input debe ser pathlib.Path o bytes")

        file_id = self._fs.put(content_data, filename=filename, owner=owner, type="biadoc")

        doc = {
            "owner": owner,
            "filename": filename,
            "gridfs_file_id": file_id,
            "source_ref": source_id,
            "iadoc_ref": iadoc_id,
            "source_mime": source_mime,
            "source_created_at": source_created_at,
            "created_at": datetime.datetime.now(datetime.timezone.utc),
            "size_bytes": len(content_data),
            "tokens": tokens
        }
        return self._db.biadocs.insert_one(doc).inserted_id
    #----------------------------------------------------------------------------------------------

    def get_all_biadocs(self, owner) -> list[BIaDcoInfo]:
        ret = []
        for record in self._db.biadocs.find({"owner": owner}):
            binary_content = self._fs.get(record["gridfs_file_id"]).read()
            ret.append(BIaDcoInfo(
                record["_id"],
                record["owner"],
                record["filename"],
                None,
                record["source_ref"],
                record["iadoc_ref"],
                record["source_mime"],
                record["source_created_at"],
                record["created_at"],
                record["size_bytes"],
                record["tokens"],
                binary_content
            ))
        return ret
    #----------------------------------------------------------------------------------------------

    def get_all_biadoc_meta(self, owner) -> list[BIaDcoInfo]:
        ret = []
        for record in self._db.biadocs.find({"owner": owner}, {"gridfs_file_id": 0}):
            ret.append(BIaDcoInfo(
                record["_id"],
                record["owner"],
                record["filename"],
                None,
                record["source_ref"],
                record["iadoc_ref"],
                record["source_mime"],
                record["source_created_at"],
                record["created_at"],
                record["size_bytes"],
                record["tokens"]
            ))
        return ret
    #----------------------------------------------------------------------------------------------

    # ------------------ Pretrained ---------------------

    def add_pretrained(self, filename: str, file_content: bytes):
        """ Almacena un documento pretrained como binario en GridFS, sobrescribiendo si existe. """
        with self.transaction() as session:
            # Buscar si ya existe un pretrained con ese filename
            existing = self._db.pretrained_docs.find_one({"filename": filename})

            if existing:
                self._log.info(f"ℹ️ Pretrained '{filename}' ya existe. Sobrescribiendo...")
                if "gridfs_file_id" in existing:
                    self._fs.delete(existing["gridfs_file_id"])
                self._db.pretrained_docs.delete_one({"_id": existing["_id"]}, session=session)

            # Guardar el nuevo contenido
            file_id = self._fs.put(file_content, filename=filename, type="pretrained")

            doc = {
                "filename": filename,
                "gridfs_file_id": file_id,
                "created_at": datetime.datetime.now(datetime.timezone.utc),
                "size_bytes": len(file_content)
            }
        return self._db.pretrained_docs.insert_one(doc, session=session).inserted_id
    #----------------------------------------------------------------------------------------------

    def get_pretrained_by_filename(self, filename: str) -> bytes | None:
        """ Recupera el contenido binario de un pretrained dado su owner y filename. """
        record = self._db.pretrained_docs.find_one({"filename": filename})

        if not record:
            self._log.warning(f"⚠️ No se encontró pretrained '{filename}'")
            return None

        return self._fs.get(record["gridfs_file_id"]).read()
    #----------------------------------------------------------------------------------------------

    def delete_pretrained_by_filename(self, filename: str) -> bool:
        """ Elimina un pretrained por su owner y filename, incluyendo su binario en GridFS. """
        record = self._db.pretrained_docs.find_one({"filename": filename})

        if not record:
            self._log.warning(f"⚠️ No se encontró pretrained '{filename}'")
            return False

        with self.transaction() as session:
            if "gridfs_file_id" in record:
                self._fs.delete(record["gridfs_file_id"])
            self._db.pretrained_docs.delete_one({"_id": record["_id"]}, session=session)

        self._log.info(f"✅ Pretrained '{filename}' eliminado")
        return True
    #----------------------------------------------------------------------------------------------

    # ------------------ Docs management ---------------------

    def delete_doc_by_id(self, collection_name: str, document_id: str):
        """ Elimina un documento y su binario GridFS dado su _id. """
        collection = {
            "source": self._db.source_docs,
            "iadoc": self._db.iadocs,
            "biadoc": self._db.biadocs
        }.get(collection_name)

        if not collection:
            raise ValueError(f"❌ Tipo de colección no válido: {collection_name}")

        doc_id = self._validate_object_id(document_id)
        record = collection.find_one({"_id": doc_id})

        if not record:
            self._log.warning(f"⚠️ No se encontró documento en {collection_name} con _id {document_id}")
            return False

        with self.transaction() as session:
            if "gridfs_file_id" in record:
                self._fs.delete(record["gridfs_file_id"])
            collection.delete_one({"_id": doc_id}, session=session)

        self._log.info(f"✅ Documento {document_id} eliminado de {collection_name}")
        return True
    #----------------------------------------------------------------------------------------------

    def get_doc_by_id(self, collection_name: str, document_id: str) -> dict | None:
        """ Recupera un documento y su contenido binario desde su _id. """
        collection = {
            "source": self._db.source_docs,
            "iadoc": self._db.iadocs,
            "biadoc": self._db.biadocs
        }.get(collection_name)

        if not collection:
            raise ValueError(f"❌ Tipo de colección no válido: {collection_name}")

        doc_id = self._validate_object_id(document_id)
        record = collection.find_one({"_id": doc_id})

        if not record:
            self._log.warning(f"⚠️ No se encontró documento en {collection_name} con _id {document_id}")
            return None

        if "gridfs_file_id" in record:
            record["binary_content"] = self._fs.get(record["gridfs_file_id"]).read()
        else:
            record["binary_content"] = None

        return record
    #----------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------