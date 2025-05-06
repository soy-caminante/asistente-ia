import  datetime
import  json
import  mimetypes
import  os
import  pathlib
import  tiktoken

from    dataclasses                 import  dataclass, asdict
from    models.models               import  ClienteInfo
from    tools.tools                 import  file_size_to_str
#--------------------------------------------------------------------------------------------------

@dataclass 
class ExpedienteFileInfo:
    src:        pathlib.Path
    path:       pathlib.Path
    date:       str
    mime:       str
    size:       int
    tokens:     int
    content:    str = None
    #----------------------------------------------------------------------------------------------

    @property
    def name(self): return self.path.stem
    #----------------------------------------------------------------------------------------------

    @property
    def size_str(self): return file_size_to_str(self.size)
    #----------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------

def get_file_info(path: pathlib.Path, encoding_model="cl100k_base") -> ExpedienteFileInfo:
    def file_size(bytes_int):
        if bytes_int < 1024:
            return f"{bytes_int} B"
        elif bytes_int < 1024**2:
            return f"{bytes_int / 1024:.2f} kB"
        else:
            return f"{bytes_int / (1024**2):.2f} MB"

    if not path.exists:
        raise FileNotFoundError(f"No se encontró el archivo: {path}")

    # Tipo MIME
    mime, _ = mimetypes.guess_type(str(path))

    # Tamaño en bytes
    size_bytes      = os.path.getsize(str(path))
    readable_size   = file_size(size_bytes)

    # Leer contenido para contar tokens
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        contenido = f.read()

        
    # Tokenización
    tokenizer   = tiktoken.get_encoding(encoding_model)
    num_tokens  = len(tokenizer.encode(contenido))
    
    if path.suffix != ".txt" and path.suffix != "iadoc":
        contenido = None
    return ExpedienteFileInfo(path, contenido, mime, size_bytes, readable_size, num_tokens)
#--------------------------------------------------------------------------------------------------

def get_iadoc_src(file: pathlib.Path):
    base_path   = file.parent
    base_name   = file.stem  # nombre sin extensión
    src         = None
    for f in base_path.glob(f"{base_name}.*"):
        if f.suffix != ".iadoc":
            src = f
            break
    return src
#--------------------------------------------------------------------------------------------------

def get_src_iadoc(file: pathlib.Path):
    base_path   = file.parent
    base_name   = file.stem  # nombre sin extensión
    src         = None
    for f in base_path.glob(f"{base_name}.*"):
        if f.suffix == ".iadoc":
            src = f
            break
    return src
#--------------------------------------------------------------------------------------------------

class CompactEncoder:
    # Mapeo de campos con sus índices
    FIELD_MAP = \
    {
        "documento": 0,
        "fecha": 1,
        "motivo": 2,
        "síntomas": 3,
        "estado físico": 4,
        "medicación": 5,
        "tratamiento": 6,
        "recomendaciones": 7,
        "ingresos": 8,
        "comentarios": 9,
        "diagnósticos": 10,
        "antecedentes familiares": 11,
        "factores riesgo cardivascular": 12,
        "alergias": 13,
        "operaciones": 14,
        "implantes": 15,
        "otros": 16
    }
    #----------------------------------------------------------------------------------------------

    # Delimitadores
    FIELD_DELIM = "|"
    LIST_DELIM = ";"
    ESCAPE_CHAR = "¬"
    #----------------------------------------------------------------------------------------------

    # Campos que deben tratarse como listas
    LIST_FIELDS = \
    {
        "síntomas", 
        "estado físico", 
        "medicación", 
        "tratamiento",
        "recomendaciones", 
        "ingresos", 
        "comentarios", 
        "diagnósticos",
        "antecedentes familiares", 
        "factores riesgo cardivascular", 
        "alergias", 
        "operaciones", 
        "implantes", 
        "otros"
    }
    #----------------------------------------------------------------------------------------------

    def __init__(self):
        # Invertimos el FIELD_MAP para decodificación
        self._index_to_field = {v: k for k, v in self.FIELD_MAP.items()}
    #----------------------------------------------------------------------------------------------

    def _sanitize(self, text):
        if not isinstance(text, str):
            text = str(text)
        return text.replace(self.FIELD_DELIM, self.ESCAPE_CHAR).replace(self.LIST_DELIM, self.ESCAPE_CHAR)
    #----------------------------------------------------------------------------------------------

    def _desanitize(self, text):
        return text.replace(self.ESCAPE_CHAR, self.FIELD_DELIM).replace(self.ESCAPE_CHAR, self.LIST_DELIM)
    #----------------------------------------------------------------------------------------------

    def encode(self, data: dict, doc_id) -> str:
        data["documento"]   = doc_id
        parts               = [ ]
        for field, index in self.FIELD_MAP.items():
            if field in data:
                value = data[field]
                if value is None: continue
                if isinstance(value, list):
                    encoded = self.LIST_DELIM.join(self._sanitize(v) for v in value)
                else:
                    encoded = self._sanitize(value)
                if encoded != "":
                    parts.append(f"{index}.{encoded}")
        return self.FIELD_DELIM.join(parts)
    #----------------------------------------------------------------------------------------------

    def decode(self, encoded_str: str) -> dict:
        result = {}
        parts = encoded_str.split(self.FIELD_DELIM)
        for part in parts:
            if "." not in part:
                continue
            idx_str, value_str = part.split(".", 1)
            try:
                idx = int(idx_str)
            except ValueError:
                continue
            field = self._index_to_field.get(idx)
            if not field:
                continue
            if field in self.LIST_FIELDS:
                items = value_str.split(self.LIST_DELIM)
                result[field] = [item.replace(self.ESCAPE_CHAR, self.LIST_DELIM).replace(self.ESCAPE_CHAR, self.FIELD_DELIM) for item in items]
            else:
                result[field] = value_str.replace(self.ESCAPE_CHAR, self.FIELD_DELIM).replace(self.ESCAPE_CHAR, self.LIST_DELIM)
        return result
    #----------------------------------------------------------------------------------------------

    def get_alergias(self, json_obj: dict):
        return json_obj.get("alergias", [])
    #----------------------------------------------------------------------------------------------

    def get_riesgo_cardio(self, json_obj: dict):
        return json_obj.get("factores riesgo cardivascular", [])
    #----------------------------------------------------------------------------------------------

    def get_antecedentes(self, json_obj: dict):
        return json_obj.get("antecedentes familiares", [])
    #----------------------------------------------------------------------------------------------

    def get_ingresos(self, json_obj: dict):
        return json_obj.get("ingresos", [])
    #----------------------------------------------------------------------------------------------

    def get_visitas(self, json_obj: dict):
        if "fecha" in json_obj.keys(): return [ json_obj["fecha"] ]
        return [ ]
    #----------------------------------------------------------------------------------------------

    def get_medicacion(self, json_obj: dict):
        return json_obj.get("medicación", [])
    #----------------------------------------------------------------------------------------------

#--------------------------------------------------------------------------------------------------

class PacienteContext:
    NAME        = "nombre"
    APELLIDOS   = "apellidos"
    ID          = "id"
    ID_INTERNO  = "id-interno"
    BDATE       = "fecha-nacimiento"
    SEX         = "sexo"
    IADOCS      = "documentos-ia"
    SRCDOCS     = "documentos"
    #----------------------------------------------------------------------------------------------

    def __init__(self, info: ClienteInfo, iadocs: dict[str:ExpedienteFileInfo]={}, srcdocs: dict[str:ExpedienteFileInfo]={}):
        self.nombre             = info.nombre
        self.apellidos          = info.apellidos
        self.id                 = info.dni
        self.id_interno         = info.id_interno
        self.sexo               = info.sexo
        self.fecha_nacimiento   = info.fecha_nacimiento
        self.iadocs             = iadocs
        self.srcdocs            = srcdocs
    #----------------------------------------------------------------------------------------------

    def get_id_json(self):
        return asdict(ClienteInfo(self.nombre, self.apellidos, self.fecha_nacimiento, self.sexo, self.id))
    #----------------------------------------------------------------------------------------------

    def add_ia_doc(self, k, v): self.iadocs[k] = v
    #----------------------------------------------------------------------------------------------

    def add_src_doc(self, k, v): self.srcdocs[k] = v
    #----------------------------------------------------------------------------------------------

    def get_context(self):
        context = ""
        for _, c in self.iadocs.items():
            context += c
        return context
    #----------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------

class PacienteContextFactory:
    @staticmethod
    def get_patient_id(target_dir: pathlib.Path):
        id_file = target_dir / "id.json"

        if not id_file.exists():
            return None
        else:
            with open(id_file, "r", encoding="utf-8") as f:
                return ClienteInfo(**json.loads(f.read()))
    #----------------------------------------------------------------------------------------------
    
    def __init__(self, log_fcn=None):
        self._log_fcn   = log_fcn if log_fcn is not None else self.dummy_log
    #----------------------------------------------------------------------------------------------

    def dummy_log(self, *args): pass
    #----------------------------------------------------------------------------------------------

    def load_src_paciente(self, patient: str|pathlib.Path) -> tuple[ClienteInfo, dict[str:ExpedienteFileInfo]]:
        ret = (None, None)

        try:
            patient         = pathlib.Path(patient)
            patient_info    = None
            src_docs        = { }

            if not patient.exists():
                self._log_fcn(f"El paciente {patient} no existe en el sistema")
            else:
                id_file     = patient / "id.json"
                meta_file   = patient / "meta.json"

                if not id_file.exists():
                    self._log_fcn(f"El paciente {patient} no tiene fichero de identificación")

                if not meta_file.exists():
                    self._log_fcn(f"El paciente {patient} no tiene fichero de metainformación")

                if id_file.exists() and meta_file.exists():
                    with    open(id_file, "r", encoding="utf-8") as f_id, \
                            open(meta_file, "r", encoding="utf-8") as f_meta:
                        patient_info    = ClienteInfo(**json.loads(f.read()))
                        meta_data       = json.load(f_meta)
                        for item in meta_data:
                            src = pathlib.Path(item['src'])

                            if src.suffix == ".txt":
                                with open(src, "r", encoding="utf-8") as f_src:
                                    content = f_src.read()
                            else:
                                content = None
                            src_docs[src.stem]  = ExpedienteFileInfo(   src     = src,
                                                                        path    = pathlib.Path(item['path']),
                                                                        date    = item['date'],
                                                                        mime    = item['mime'],
                                                                        size    = item['size'],
                                                                        tokens  = item['tokens'],
                                                                        content = content)
                    ret = (patient_info, src_docs)
        except Exception as ex:
            self._log_fcn(ex)
        finally:
            return ret
    #----------------------------------------------------------------------------------------------

    def load_consolidated_paciente(self, patient: str|pathlib.Path) -> PacienteContext:
        ret = None

        try:
            patient         = pathlib.Path(patient)
            patient_info    = None
            ia_docs         = { }
            src_docs        = { }

            if not patient.exists():
                self._log_fcn(f"El paciente {patient} no existe en el sistema")
            else:
                id_file     = patient / "id.json"
                meta_file   = patient / "meta.json"

                if not id_file.exists():
                    self._log_fcn(f"El paciente {patient} no tiene fichero de identificación")

                if not meta_file.exists():
                    self._log_fcn(f"El paciente {patient} no tiene fichero de metainformación")

                if id_file.exists() and meta_file.exists():
                    with    open(id_file, "r", encoding="utf-8") as f_id, \
                            open(meta_file, "r", encoding="utf-8") as f_meta:
                        patient_info    = ClienteInfo(**json.loads(f_id.read()))
                        meta_data       = json.load(f_meta)
                        for item in meta_data:
                            src = pathlib.Path(item['src'])

                            if src.suffix == ".txt" or src.suffix == ".iadoc":
                                with open(src, "r", encoding="utf-8") as f_src:
                                    content = f_src.read()
                            else:
                                content = None
                            expediente_file = ExpedienteFileInfo(   src     = src,
                                                                    path    = pathlib.Path(item['path']),
                                                                    date    = item['date'],
                                                                    mime    = item['mime'],
                                                                    size    = item['size'],
                                                                    tokens  = item['tokens'],
                                                                    content = content)
                            if src.suffix == ".iadoc":
                                ia_docs[src.stem] = expediente_file
                            else:
                                src_docs[src.stem] = expediente_file
                    ret = PacienteContext(patient_info, ia_docs, src_docs)
        except Exception as ex:
            self._log_fcn(ex)
        finally:
            return ret
    #----------------------------------------------------------------------------------------------

    def consolidate_context(self, context: PacienteContext, location: str|pathlib.Path) -> bool:
        try:
            location = pathlib.Path(location)

            if location.exists():
                if location.is_dir():
                    timestamp   = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
                    bck_path    = location.parent / f"{location.name}_{timestamp}"
                    src_path    = pathlib.Path(location)
                    src_path.rename(bck_path)
                else:
                    self._log_fcn(f"{location} no es un directorio")
                    return False
            location.mkdir(parents=True, exist_ok=True)

            id_json     = context.get_id_json()
            file_path   = location / "id.json"
            with open(file_path, "w", encoding="utf-8") as f:
                with open(file_path, "w") as f:
                    f.write(json.dumps(id_json))

            for doc_name, doc_text in context.srcdocs.items():
                file_path = location / f"{doc_name}.txt"
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(doc_text)
            
            for doc_name, doc_text in context.iadocs.items():
                file_path = location / f"{doc_name}.iadoc"
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(doc_text)

            return True
        except Exception as ex:
            self._log_fcn(ex)
            return False
    #----------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------
