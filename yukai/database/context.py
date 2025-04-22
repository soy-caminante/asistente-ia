import  datetime
import  json
import  pathlib

from    dataclasses                 import  dataclass, asdict
#--------------------------------------------------------------------------------------------------

@dataclass
class PatitnetInfo:
    nombre: str
    apellidos: str
    fecha_nacimiento: str
    sexo: str
    id: str
    id_interno: str
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
        "síntomas", "estado físico", "medicación", "tratamiento",
        "recomendaciones", "ingresos", "comentarios", "diagnósticos",
        "antecedentes familiares", "factores riesgo cardivascular", "alergias", 
        "operaciones", "implantes", "otros"
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

class PatientContext:
    NAME        = "nombre"
    APELLIDOS   = "apellidos"
    ID          = "id"
    ID_INTERNO  = "id-interno"
    BDATE       = "fecha-nacimiento"
    SEX         = "sexo"
    IADOCS      = "documentos-ia"
    SRCDOCS     = "documentos"
    #----------------------------------------------------------------------------------------------

    def __init__(self, info: PatitnetInfo, iadocs: dict[str:str]={}, srcdocs: dict[str:str]={}):
        self.name               = info.nombre
        self.apellidos          = info.apellidos
        self.id                 = info.id
        self.id_interno         = info.id_interno
        self.sexo               = info.sexo
        self.fecha_nacimiento   = info.fecha_nacimiento
        self.iadocs             = iadocs
        self.srcdocs            = srcdocs
    #----------------------------------------------------------------------------------------------

    def get_id_json(self):
        return asdict(PatitnetInfo(self.name, self.apellidos, self.fecha_nacimiento, self.sexo, self.id))
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

class PatientContextFactory:
    @staticmethod
    def get_patient_id(target_dir: pathlib.Path):
        id_file = target_dir / "id.json"

        if not id_file.exists():
            return None
        else:
            with open(id_file, "r", encoding="utf-8") as f:
                return PatitnetInfo(**json.loads(f.read()))
    #----------------------------------------------------------------------------------------------
    
    def __init__(self, log_fcn=None):
        self._log_fcn   = log_fcn if log_fcn is not None else self.dummy_log
    #----------------------------------------------------------------------------------------------

    def dummy_log(self, *args): pass
    #----------------------------------------------------------------------------------------------

    def load_incomming(self, patient: str|pathlib.Path) -> tuple[PatitnetInfo, dict[str:str]]:
        ret = (None, None)

        try:
            patient         = pathlib.Path(patient)
            patient_info    = None
            src_docs        = { }

            if not patient.exists():
                self._log_fcn(f"El paciente {patient} no existe en el sistema")
            else:
                id_file = patient / "id.json"

                if not id_file.exists():
                    self._log_fcn(f"El paciente {patient} no tiene fichero de identificación")
                else:
                    with open(id_file, "r", encoding="utf-8") as f:
                        patient_info = PatitnetInfo(**json.loads(f.read()))

                    for file in patient.iterdir():
                        if file.suffix == ".txt":
                            with open(file, "r", encoding="utf-8") as f:
                                src_docs[file.stem] = (f.read())
                    ret = (patient_info, src_docs)
        except Exception as ex:
            self._log_fcn(ex)
        finally:
            return ret
    #----------------------------------------------------------------------------------------------

    def load_consolidated(self, patient: str|pathlib.Path) -> PatientContext:
        ret = None

        try:
            patient         = pathlib.Path(patient)
            patient_info    = None
            ia_docs         = { }
            src_docs        = { }

            if not patient.exists():
                self._log_fcn(f"El paciente {patient} no existe en el sistema")
            else:
                id_file = patient / "id.json"

                if not id_file.exists():
                    self._log_fcn(f"El paciente {patient} no tiene fichero de identificación")
                else:
                    with open(id_file, "r", encoding="utf-8") as f:
                        patient_info = PatitnetInfo(**json.loads(f.read()))

                    for file in patient.iterdir():
                        if file.suffix == ".txt" or file.suffix == ".iadoc":
                            with open(file, "r", encoding="utf-8") as f:
                                if file.suffix == ".txt":
                                    src_docs[file.stem] = f.read()
                                else:
                                    ia_docs[file.stem] = f.read()
                    ret = PatientContext(patient_info, ia_docs, src_docs)
        except Exception as ex:
            self._log_fcn(ex)
        finally:
            return ret
    #----------------------------------------------------------------------------------------------

    def consolidate_context(self, context: PatientContext, location: str|pathlib.Path) -> bool:
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
