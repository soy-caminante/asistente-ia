import  datetime
import  gridfs
import  os
import  pathlib
import  subprocess
import  time

from    bson                        import  ObjectId
from    contextlib                  import  contextmanager
from    logger                      import  Logger
from    models.models               import  ClienteInfo, SrcDocInfo, IaDcoInfo, BIaDcoInfo, ExpedienteSummary
from    pymongo                     import  MongoClient, ReturnDocument
from    pymongo.database            import  Database
from    pymongo.errors              import  ServerSelectionTimeoutError
from    urllib.parse                import  quote_plus
#--------------------------------------------------------------------------------------------------

# Abrir el shell de mongo en el docker:
#    docker exec -it mongodb mongosh

class ClientesDocumentStore:
    def __init__(self, log:             Logger,
                       docker_file:     pathlib.Path,
                       db_port:         int,
                       db_host:         str,
                       db_user:         str,
                       db_pwd:          str,
                       db_name:         str):
        
        self._log           = log
        self._docker_file   = docker_file
        self._mongo_uri     = f"mongodb://{db_user}:{quote_plus(db_pwd)}@{db_host}:{db_port}"
        self._client        = MongoClient(self._mongo_uri)
        self._db: Database  = self._client[db_name]
        self._fs            = gridfs.GridFS(self._db)
    #----------------------------------------------------------------------------------------------

    def get_mongo_uri(self, port: str):
        # Detecta si estás dentro de Docker por entorno o rutas típicas
        if os.path.exists("/.dockerenv") or os.environ.get("IN_DOCKER") == "1":

            return f"mongodb://mongo:{port}"
        return f"mongodb://localhost:{port}"
    #----------------------------------------------------------------------------------------------

    # ------------------ Mongo Ready ---------------------

    def is_mongo_ready(self, uri=None, timeout=3):
        try:
            self._client.admin.command("ping")
            return True
        except Exception as ex:
            self._log.error(ex)
            return False
    #----------------------------------------------------------------------------------------------

    def setup_db(self):
        self._db.pretrained_docs.create_index("filename", unique=True)
        if self._db.counters.find_one({"_id": "file_id"}) is None:
            self._db.counters.insert_one({"_id": "file_id", "seq": 0})
    #----------------------------------------------------------------------------------------------

    @contextmanager
    def transaction(self):
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

    def add_cliente(self,
                    nombre:                         str,
                    apellidos:                      str,
                    sexo:                           str,
                    fecha_nacimiento:               datetime.datetime,
                    dni:                            str,
                    id_interno:                     str,
                    antecedentes_familiares:        str,
                    factores_riesgo_cardiovascular: str,
                    medicacion:                     str,
                    alergias:                       str,
                    ingresos:                       str,
                    ultimas_visitas:                str,
                    src_docs:                       list[dict],
                    iadocs:                         list[dict],
                    biadocs:                        list[dict]):

        with self.transaction() as session:
            # 1. Insertar el cliente
            cliente_doc = {
                "owner":            id_interno,
                "nombre":           nombre,
                "apellidos":        apellidos,
                "sexo":             sexo,
                "fecha_nacimiento": fecha_nacimiento,
                "dni":              dni
            }
            res = self._db.clientes.insert_one(cliente_doc, session=session)
            if not res.inserted_id:
                self._log.error("❌ No se pudo insertar el cliente")
                return False
            
            owner_id = res.inserted_id

            expediente_doc = {
                "owner":                            owner_id,    
                "antecedentes_familiares":          antecedentes_familiares,
                "factores_riesgo_cardiovascular":   factores_riesgo_cardiovascular,
                "medicacion":                       medicacion,
                "alergias":                         alergias,                   
                "ingresos":                         ingresos,                     
                "ultimas_visitas":                  ultimas_visitas
            }
            res = self._db.expedientes.insert_one(expediente_doc, session=session)
            if not res.inserted_id:
                self._log.error("❌ No se pudo insertar el cliente")
                return False

            # 2. Insertar source_docs
            for index in range(len(src_docs)):
                creation_ts = datetime.datetime.now(datetime.timezone.utc)
                src         = src_docs[index]
                content     = src["content"]
                file_id     = self._fs.put(content, filename=src["filename"], type="source")
                doc = {
                        "owner":                owner_id,
                        "filename":             src["filename"],
                        "mime":                 src.get("mime", "application/octet-stream"),
                        "gridfs_file_id":       file_id,
                        "source_created_at":    src["ts"],
                        "created_at":           creation_ts,
                        "size_bytes":           len(content)
                }
                res = self._db.source_docs.insert_one(doc, session=session)
                if not res.inserted_id:
                    self._log.error(f"❌ No se pudo insertar source_doc '{src['filename']}'")
                    return False
                souce_ref = res.inserted_id
                
                if index < len(iadocs):
                    iadoc   = iadocs[index]
                    content = iadoc["content"]
                    file_id = self._fs.put(content, filename=iadoc["filename"], type="iadoc")
                    doc = {
                        "owner":                owner_id,
                        "filename":             iadoc["filename"],
                        "gridfs_file_id":       file_id,
                        "source_ref":           self._validate_object_id(souce_ref),
                        "source_mime":          iadoc["source_mime"],
                        "source_created_at":    iadoc["ts"],
                        "created_at":           creation_ts,
                        "size_bytes":           len(content),
                        "tokens":               iadoc["tokens"]
                    }
                    res = self._db.iadocs.insert_one(doc, session=session)
                    if not res.inserted_id:
                        self._log.error(f"❌ No se pudo insertar iadoc '{src['filename']}'")
                        return False

                    iadoc_ref   = res.inserted_id
                    biadoc      = biadocs[index]
                    content     = biadoc["content"]
                    file_id     = self._fs.put(content, filename=biadoc["filename"], type="biadoc")
                    doc = {
                        "owner":                owner_id,
                        "filename":             biadoc["filename"],
                        "gridfs_file_id":       file_id,
                        "source_ref":           self._validate_object_id(souce_ref),
                        "iadoc_ref":            self._validate_object_id(iadoc_ref),
                        "source_mime":          biadoc["source_mime"],
                        "source_created_at":    biadoc["ts"],
                        "created_at":           creation_ts,
                        "size_bytes":           len(content),
                        "tokens":               biadoc["tokens"]
                    }
                    res = self._db.biadocs.insert_one(doc, session=session)
                    if not res.inserted_id:
                        self._log.error(f"❌ No se pudo insertar biadoc '{src['filename']}'")
                        return False

            self._log.info(f"✅ Cliente '{id_interno}' creado con todos sus documentos")
            return True
    #----------------------------------------------------------------------------------------------

    def update_cliente( self,
                        db_id:                          str,
                        nombre:                         str                 = None,
                        apellidos:                      str                 = None,
                        sexo:                           str                 = None,
                        fecha_nacimiento:               datetime.datetime   = None,
                        dni:                            str                 = None,
                        antecedentes_familiares:        str                 = None,
                        factores_riesgo_cardiovascular: str                 = None,
                        medicacion:                     str                 = None,
                        alergias:                       str                 = None,
                        ingresos:                       str                 = None,
                        ultimas_visitas:                str                 = None,
                        src_docs:                       list[dict]          = [],
                        iadocs:                         list[dict]          = [],
                        biadocs:                        list[dict]          = []) -> bool:
        """Actualiza los campos no None de un cliente y su expediente, usando el _id del cliente."""

        cliente_obj_id = self._validate_object_id(db_id)

        update_fields_cliente = {}

        if nombre is not None:              update_fields_cliente["nombre"]             = nombre
        if apellidos is not None:           update_fields_cliente["apellidos"]          = apellidos
        if sexo is not None:                update_fields_cliente["sexo"]               = sexo
        if fecha_nacimiento is not None:    update_fields_cliente["fecha_nacimiento"]   = fecha_nacimiento
        if dni is not None:                 update_fields_cliente["dni"]                = dni

        update_fields_expediente = {}

        if antecedentes_familiares is not None:         update_fields_expediente["antecedentes_familiares"]         = antecedentes_familiares
        if factores_riesgo_cardiovascular is not None:  update_fields_expediente["factores_riesgo_cardiovascular"]  = factores_riesgo_cardiovascular
        if medicacion is not None:                      update_fields_expediente["medicacion"]                      = medicacion
        if alergias is not None:                        update_fields_expediente["alergias"]                        = alergias
        if ingresos is not None:                        update_fields_expediente["ingresos"]                        = ingresos
        if ultimas_visitas is not None:                 update_fields_expediente["ultimas_visitas"]                 = ultimas_visitas

        with self.transaction() as session:
            result = None
            if update_fields_cliente:
                result = self._db.clientes.update_one(
                    {"_id": cliente_obj_id},
                    {"$set": update_fields_cliente},
                    session=session
                )
                if result.matched_count == 0:
                    self._log.warning(f"⚠️ Cliente con _id {db_id} no encontrado.")
                    return False

            if update_fields_expediente:
                result = self._db.expedientes.update_one(
                    {"owner": db_id},
                    {"$set": update_fields_expediente},
                    session=session
                )

            # SRC Docs
            for src in src_docs:
                creation_ts = datetime.datetime.now(datetime.timezone.utc)
                file_id = self._fs.put(src["content"], filename=src["filename"], type="source")

                doc_data = {
                    "owner":                db_id,
                    "filename":             src["filename"],
                    "mime":                 src.get("mime", "application/octet-stream"),
                    "gridfs_file_id":       file_id,
                    "created_at":           creation_ts,
                    "source_created_at":    src.get("source_created_at", creation_ts),
                    "size_bytes":           len(src["content"])
                }

                if "_id" in src:
                    src_id = self._validate_object_id(src["_id"])
                    if self._db.source_docs.find_one({"_id": src_id}):
                        self._db.source_docs.update_one({"_id": src_id}, {"$set": doc_data}, session=session)
                        continue

                self._db.source_docs.insert_one(doc_data, session=session)

            # IADOCs
            for iadoc in iadocs:
                creation_ts = datetime.datetime.now(datetime.timezone.utc)
                file_id = self._fs.put(iadoc["content"], filename=iadoc["filename"], type="iadoc")

                doc_data = {
                    "owner":                db_id,
                    "filename":             iadoc["filename"],
                    "gridfs_file_id":       file_id,
                    "source_ref":           self._validate_object_id(iadoc["source_ref"]),
                    "source_mime":          iadoc["source_mime"],
                    "source_created_at":    iadoc["source_created_at"],
                    "created_at":           creation_ts,
                    "size_bytes":           len(iadoc["content"]),
                    "tokens":               iadoc["tokens"]
                }

                if "_id" in iadoc:
                    iadoc_id = self._validate_object_id(iadoc["_id"])
                    if self._db.iadocs.find_one({"_id": iadoc_id}):
                        self._db.iadocs.update_one({"_id": iadoc_id}, {"$set": doc_data}, session=session)
                        continue

                self._db.iadocs.insert_one(doc_data, session=session)

            # BIADOCs
            for biadoc in biadocs:
                creation_ts = datetime.datetime.now(datetime.timezone.utc)
                file_id = self._fs.put(biadoc["content"], filename=biadoc["filename"], type="biadoc")

                doc_data = {
                    "owner":                db_id,
                    "filename":             biadoc["filename"],
                    "gridfs_file_id":       file_id,
                    "source_ref":           self._validate_object_id(biadoc["source_ref"]),
                    "iadoc_ref":            self._validate_object_id(biadoc["iadoc_ref"]),
                    "source_mime":          biadoc["source_mime"],
                    "source_created_at":    biadoc["source_created_at"],
                    "created_at":           creation_ts,
                    "size_bytes":           len(biadoc["content"]),
                    "tokens":               biadoc["tokens"]
                }

                if "_id" in biadoc:
                    biadoc_id = self._validate_object_id(biadoc["_id"])
                    if self._db.biadocs.find_one({"_id": biadoc_id}):
                        self._db.biadocs.update_one({"_id": biadoc_id}, {"$set": doc_data}, session=session)
                        continue

                self._db.biadocs.insert_one(doc_data, session=session)

            return True
    #----------------------------------------------------------------------------------------------

    def get_all_clientes(self) -> list[ClienteInfo]:
        ret = []
        for record in self._db.clientes.find({}):
            ret.append(ClienteInfo(record["nombre"],
                                   record["apellidos"],
                                   record["fecha_nacimiento"],
                                   record["sexo"],
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
                               record["fecha_nacimiento"],
                               record["sexo"],
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
                               record["fecha_nacimiento"],
                               record["sexo"],
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
                self._db.expedientes.delete_many({"owner": owner}, session=session)

                # 5. Borrar cliente
                self._db.clientes.delete_many({"owner": owner}, session=session)

            except Exception as e:
                self._log.error(f"❌ Error durante eliminación del cliente: {e}")
                raise

        return True
    #----------------------------------------------------------------------------------------------

    # ------------------ Expedientes ---------------------
    
    def get_expediente_by_cliente_db_id(self, db_id: str) -> ExpedienteSummary | None:
        record = self._db.expedientes.find_one({"owner": self._validate_object_id(db_id)})
        if record:
            return ExpedienteSummary(   record["antecedentes_familiares"],
                                        record["factores_riesgo_cardiovascular"],
                                        record["medicacion"],
                                        record["alergias"],
                                        record["ingresos"],
                                        record["ultimas_visitas"],
                                        record["_id"])
        return None
    #----------------------------------------------------------------------------------------------

    # ------------------ Source Docs ---------------------

    def get_all_source_docs(self, owner) -> list[SrcDocInfo]:
        ret = []
        for record in self._db.source_docs.find({"owner": self._validate_object_id(db_id)}):
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
        for record in self._db.source_docs.find({"owner": self._validate_object_id(owner)}, {"gridfs_file_id": 0}):
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

    def get_source_doc_content_by_id(self, db_id: str) -> bytes | None:
        """Devuelve el contenido en bytes de un documento en source_docs dado su _id."""
        obj_id  = self._validate_object_id(db_id)
        doc     = self._db.source_docs.find_one({"_id": obj_id})
        if not doc:
            self._log.warning(f"⚠️ Documento con _id {db_id} no encontrado en source_docs.")
            return None
        return self._fs.get(doc["gridfs_file_id"]).read()
    #----------------------------------------------------------------------------------------------

    # ------------------ IADOCs ---------------------

    def get_all_iadocs(self, owner) -> list[IaDcoInfo]:
        ret = []
        for record in self._db.iadocs.find({"owner": self._validate_object_id(owner)}):
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
        for record in self._db.iadocs.find({"owner": self._validate_object_id(owner)}, {"gridfs_file_id": 0}):
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

    def get_iadoc_content_by_id(self, db_id: str) -> bytes | None:
        """Devuelve el contenido en bytes de un documento en source_docs dado su _id."""
        obj_id  = self._validate_object_id(db_id)
        doc     = self._db.iadocs.find_one({"_id": obj_id})
        if not doc:
            self._log.warning(f"⚠️ Documento con _id {db_id} no encontrado en source_docs.")
            return None
        return self._fs.get(doc["gridfs_file_id"]).read()
    #----------------------------------------------------------------------------------------------

    # ------------------ BIADOCs ---------------------

    def get_all_biadocs(self, owner) -> list[BIaDcoInfo]:
        ret = []
        for record in self._db.biadocs.find({"owner": self._validate_object_id(owner)}):
            binary_content = self._fs.get(record["gridfs_file_id"])
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
        for record in self._db.biadocs.find({"owner": self._validate_object_id(owner)}, {"gridfs_file_id": 0}):
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

    def get_biadoc_content_by_id(self, db_id: str) -> bytes | None:
        """Devuelve el contenido en bytes de un documento en source_docs dado su _id."""
        obj_id  = self._validate_object_id(db_id)
        doc     = self._db.biadocs.find_one({"_id": obj_id})
        if not doc:
            self._log.warning(f"⚠️ Documento con _id {db_id} no encontrado en source_docs.")
            return None
        return self._fs.get(doc["gridfs_file_id"])
    #----------------------------------------------------------------------------------------------

    # ------------------ Tmp docs ---------------------

    def add_tmp_biadoc(self, name:str, content) -> str:
        return str(self._fs.put(content, filename=name, type="biadoc", metadata={"consolidado": False}))
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