import  datetime
import  pathlib
import  shutil
import  subprocess
import  time

from    bson                import  ObjectId
from    logger              import  Logger
from    models.models       import  *
from    pymongo             import  MongoClient
from    pymongo.database    import  Database
from    pymongo.errors      import  ServerSelectionTimeoutError
from    tools.tools         import  is_plaintext_mime, is_plaint_text_file
#--------------------------------------------------------------------------------------------------

class PacientesDocumentStore:
    def __init__(self,  log: Logger,
                        base_path, 
                        docker_file     = None,
                        mongo_uri       = "mongodb://localhost:27017", 
                        db_name         = "docstore"):
        self._log           = log
        self._docker_file   = docker_file
        self._mongo_uri     = mongo_uri
        self._client        = MongoClient(mongo_uri)
        self._db: Database  = self._client[db_name]
        self._base_path     = pathlib.Path(base_path) / "consolidated"
        self._base_path.mkdir(parents=True, exist_ok=True)
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

    def ensure_mongo_ready(self, uri):
        if self.is_mongo_ready(uri):
            self._log.info("✅ MongoDB ya está disponible.")
            return True
        
        self._log.info("🚀 MongoDB no está disponible. Iniciando con Docker Compose...")

        if self._docker_file:
            subprocess.run(["docker-compose", "-f", self._docker_file, "up", "-d", "mongo"], check=True)
        else:
            subprocess.run(["docker-compose", "up", "-d", "mongo"], check=True)
        
        for i in range(20):
            if self._is_mongo_ready(uri):
                self._log.info("✅ MongoDB está listo.")
                return True
            
            self._log.info(f"⏳ Esperando que MongoDB arranque... ({i+1}/20)")
            time.sleep(2)
            
        return False
    # ------------------ Helpers ---------------------

    def _save_file(self, scr_file: pathlib.Path, dest_file: pathlib.Path):
        dest_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(scr_file, dest_file)
        return dest_file
    #----------------------------------------------------------------------------------------------

    def _read_text(self, file_path: pathlib.Path):
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    #----------------------------------------------------------------------------------------------

    def _read_binary(self, file_path: pathlib.Path):
        with open(file_path, 'rb') as f:
            return f.read()
    #----------------------------------------------------------------------------------------------

    def _remove_file(self, file_path):
        if file_path.exists():
            file_path.unlink()
    #----------------------------------------------------------------------------------------------

    def _doc_path(self, owner, tipo, filename):
        return self._base_path / owner / tipo / filename
    #----------------------------------------------------------------------------------------------

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

    # ------------------ Pacientes -----------------------

    def add_cliente(self, nombre:str, apellidos:str, sexo:str, fecha_nacimiento: datetime.datetime, dni:str, id_interno:str):
        doc = {
            "owner":            id_interno,
            "nombre":           nombre,
            "apellidos":        apellidos,
            "sexo":             sexo,
            "fecha_nacimiento": fecha_nacimiento,
            "dni":              dni
        }

        return self._db.clientes.insert_one(doc).inserted_id
    #----------------------------------------------------------------------------------------------

    def get_all_clientes(self) -> list[ClienteInfo]:
        ret = [ ]
        for record in self._db.clientes.distinct("owner"):
            record: dict
            ret.append(ClienteInfo(record["nombre"],
                                    record["apellidos"],
                                    record["sexo"],
                                    record["fecha_nacimiento"],
                                    record["dni"],
                                    record["owner"],
                                    record["_id"]))
        return ret
    #----------------------------------------------------------------------------------------------

    def get_cliente_by_id_interno(self, id: str):
        cursor = self._db.source_docs.find({"owner": id})
        if len(cursor):
            return ClienteInfo(cursor["nombre"],
                                cursor["apellidos"],
                                cursor["sexo"],
                                cursor["fecha_nacimiento"],
                                cursor["dni"],
                                cursor["owner"],
                                cursor["_id"])
        return None
    #----------------------------------------------------------------------------------------------

    def get_paciente_by_db_id(self, db_id:str):
        cursor = self._db.source_docs.find({"_id": db_id})
        if len(cursor):
            return ClienteInfo(cursor["nombre"],
                                cursor["apellidos"],
                                cursor["sexo"],
                                cursor["fecha_nacimiento"],
                                cursor["dni"],
                                cursor["owner"],
                                cursor["_id"])
        return None
    #----------------------------------------------------------------------------------------------

    # ------------------ Source Docs ---------------------


    def add_source_doc(self, owner, filename, file_path: pathlib.Path, source_created_at: datetime.datetime):
        content     = None
        db_path     = self._doc_path(owner, 'source', filename)

        is_plain, mime = is_plaint_text_file(file_path)
        if is_plain:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        
        self._save_file(file_path, db_path)

        doc = {
            "owner":                owner,
            "filename":             filename,
            "mime":                 mime,
            "path":                 str(db_path),
            "created_at":           datetime.datetime.now(datetime.timezone.utc),
            "source_created_at":    source_created_at,
            "size_bytes":           file_path.stat().st_size
        }
        if content is not None:
            doc["content"] = content

        return self._db.source_docs.insert_one(doc).inserted_id
    #----------------------------------------------------------------------------------------------

    def get_all_source_docs(self, owner) -> list[SrcDocInfo]:
        ret = [ ]
        for record in self._db.source_docs.find({"owner": owner}):
            record: dict
            ret.append(SrcDocInfo(  record["_id"],
                                    record["owner"],
                                    record["filename"],
                                    record["path"],
                                    record["mime"],
                                    record["created_at"],
                                    record["source_created_at"],
                                    record["size_bytes"],
                                    record.get("content", None)))
        return ret
    #----------------------------------------------------------------------------------------------

    def get_all_source_meta(self, owner) -> list[SrcDocInfo]:
        ret = [ ]
        for record in self._db.source_docs.find({"owner": owner}):
            record: dict
            ret.append(SrcDocInfo(  record["_id"],
                                    record["owner"],
                                    record["filename"],
                                    record["path"],
                                    record["mime"],
                                    record["created_at"],
                                    record["source_created_at"],
                                    record["size_bytes"]))
        return ret
    #----------------------------------------------------------------------------------------------

    # ------------------ IADOCs ---------------------

    def add_iadoc(self, owner, filename, file_path: pathlib.Path, source_id, source_mime, source_created_at: datetime.datetime, tokens):
        source_id   = self._check_source_exists(source_id)
        db_path     = self._doc_path(owner, 'iadoc', filename)

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        self._save_file(file_path, db_path)
        doc = {
            "owner":                owner,
            "filename":             filename,
            "path":                 str(db_path),
            "source_ref":           source_id,
            "source_mime":          source_mime,
            "source_created_at":    source_created_at,
            "created_at":           datetime.datetime.now(datetime.timezone.utc),
            "size_bytes":           file_path.stat().st_size,
            "tokens":               tokens,
            "content":              content
        }
        return self._db.iadocs.insert_one(doc).inserted_id
    #----------------------------------------------------------------------------------------------

    def get_all_iadocs(self, owner) -> list[IaDcoInfo]:
        ret = [ ]
        for record in self._db.iadocs.find({"owner": owner}):
            record: dict
            ret.append(IaDcoInfo(   record["_id"],
                                    record["owner"],
                                    record["filename"],
                                    record["path"],
                                    record["source_ref"],
                                    record["source_mime"],
                                    record["source_created_at"],
                                    record["created_at"],
                                    record["size_bytes"],
                                    record["tokens"],
                                    record.get("content", None)))
        return ret
    #----------------------------------------------------------------------------------------------

    def get_all_iadoc_meta(self, owner) -> list[IaDcoInfo]:
        ret = [ ]
        for record in self._db.iadocs.find({"owner": owner}):
            record: dict
            ret.append(IaDcoInfo(   record["_id"],
                                    record["owner"],
                                    record["filename"],
                                    record["path"],
                                    record["source_ref"],
                                    record["source_mime"],
                                    record["source_created_at"],
                                    record["created_at"],
                                    record["size_bytes"],
                                    record["tokens"]))
        return ret
    #----------------------------------------------------------------------------------------------

    # ------------------ BIADOCs ---------------------

    def add_biadoc(self, owner, filename, file_path: pathlib.Path, source_id, source_mime, source_created_at: datetime.datetime, tokens):
        source_id   = self._check_source_exists(source_id)
        iadoc_id    = self._check_iadoc_exists(iadoc_id)
        db_path     = self._doc_path(owner, 'biadoc', filename)

        self._save_file(file_path, db_path)

        doc = {
            "owner":                owner,
            "filename":             filename,
            "path":                 str(db_path),
            "source_ref":           source_id,
            "iadoc_ref":            iadoc_id,
            "source_mime":          source_mime,
            "source_created_at":    source_created_at,
            "created_at":           datetime.datetime.now(datetime.timezone.utc),
            "size_bytes":           file_path.stat().st_size,
            "tokens":               tokens
        }
        return self._db.biadocs.insert_one(doc).inserted_id
    #----------------------------------------------------------------------------------------------

    def get_all_biadocs(self, owner) -> list[BIaDcoInfo]:
        ret = []
        for record in self._db.biadocs.find({"owner": owner}):
            path            = pathlib.Path(record["path"])
            binary_content  = self._read_binary(path)
            ret.append(BIaDcoInfo(  record["_id"],
                                    record["owner"],
                                    record["filename"],
                                    record["path"],
                                    record["source_ref"],
                                    record["iadoc_ref"],
                                    record["source_mime"],
                                    record["source_created_at"],
                                    record["created_at"],
                                    record["size_bytes"],
                                    record["tokens"],
                                    binary_content))
        return ret
    #----------------------------------------------------------------------------------------------

    def get_all_biadoc_meta(self, owner) -> list[BIaDcoInfo]:
        ret = []
        for record in self._db.biadocs.find({"owner": owner}):
            path            = pathlib.Path(record["path"])
            binary_content  = self._read_binary(path)
            ret.append(BIaDcoInfo(  record["_id"],
                                    record["owner"],
                                    record["filename"],
                                    record["path"],
                                    record["source_ref"],
                                    record["iadoc_ref"],
                                    record["source_mime"],
                                    record["source_created_at"],
                                    record["created_at"],
                                    record["size_bytes"],
                                    record["tokens"]))
        return ret
    #----------------------------------------------------------------------------------------------

    # ------------------ Eliminación ---------------------

    def delete_doc(self, tipo, owner, filename):
        collection = {
            "source": self._db.source_docs,
            "iadoc": self._db.iadocs,
            "biadoc": self._db.biadocs
        }.get(tipo)

        if not collection:
            raise ValueError(f"Tipo no válido: {tipo}")

        doc = collection.find_one({"owner": owner, "filename": filename})
        if doc:
            path = pathlib.Path(doc["path"])
            self._remove_file(path)
            collection.delete_one({"_id": doc["_id"]})
            return True
        return False
    #----------------------------------------------------------------------------------------------

    # ------------------ Usuarios ---------------------

    def get_doc(self, mongo_db_id):
        iadocs_collection       = self._db["iadocs"]
        biadocs_collection      = self._db["biadocs"]
        sourcedocs_collection   = self._db["sourcedocs"]

        doc = iadocs_collection.find_one({"_id": mongo_db_id})
        if not doc:
            doc = biadocs_collection.find_one({"_id": mongo_db_id})
        if not doc:
            doc = sourcedocs_collection.find_one({"_id": mongo_db_id})
        return doc
    #----------------------------------------------------------------------------------------------

    # ------------------ Usuarios ---------------------

    def get_all_owners(self):
        owners = set()
        owners.update(self._db.source_docs.distinct("owner"))
        owners.update(self._db.iadocs.distinct("owner"))
        owners.update(self._db.biadocs.distinct("owner"))
        return sorted(owners)
    #----------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------