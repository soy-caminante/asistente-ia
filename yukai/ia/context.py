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
#--------------------------------------------------------------------------------------------------

class CompactEncoder:
    # Mapeo de campos con sus índices
    FIELD_MAP = \
    {
        "documento": 0,
        "edad": 1,
        "sexo": 2,
        "fecha": 3,
        "motivo": 4,
        "síntomas": 5,
        "estado físico": 6,
        "medicación": 7,
        "tratamiento": 8,
        "recomendaciones": 9,
        "ingresos": 10,
        "comentarios": 11,
        "diagnósticos": 12,
        "antecedentes familiares": 13,
        "factores riesgo cardivascular": 14,
        "alergias": 15,
        "operaciones": 16,
        "implantes": 17,
        "otros": 18,
        "keywords": 19,
        "tags": 20
    }
    #----------------------------------------------------------------------------------------------

    # Delimitadores
    FIELD_DELIM = "|"
    LIST_DELIM = ";"
    ESCAPE_CHAR = "¬"
    #----------------------------------------------------------------------------------------------

    def __init__(self):
        pass
    #----------------------------------------------------------------------------------------------

    def _sanitize(self, text):
        if not isinstance(text, str):
            text = str(text)
        return text.replace(self.FIELD_DELIM, self.ESCAPE_CHAR).replace(self.LIST_DELIM, self.ESCAPE_CHAR)
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
                parts.append(f"{index}.{encoded}")
        return self.FIELD_DELIM.join(parts)
    #----------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------

class PatientContext:
    NAME        = "nombre"
    APELLIDOS   = "apellidos"
    ID          = "id"
    BDATE       = "fecha-nacimiento"
    SEX         = "sexo"
    IADOCS      = "documentos-ia"
    SRCDOCS     = "documentos"
    #----------------------------------------------------------------------------------------------

    def __init__(self, info: PatitnetInfo=None, iadocs: dict[str:str]={}, srcdocs: dict[str:str]={}):
        self._json_obj  = { }

        if info:
            self.name       = info.nombre
            self.apellidos  = info.apellidos
            self.id         = info.id
            self.sex        = info.sexo
            self.birth_date = info.fecha_nacimiento
            self.iadocs     = iadocs
            self.srcdocs    = srcdocs
    #----------------------------------------------------------------------------------------------

    def get_id_json(self):
        return asdict(PatitnetInfo(self.name, self.apellidos, self.birth_date, self.sex, self.id))
    #----------------------------------------------------------------------------------------------

    @property
    def name(self) -> str: return self._json_obj[self.NAME]
    #----------------------------------------------------------------------------------------------

    @property
    def apellidos(self) -> str: return self._json_obj[self.APELLIDOS]
    #----------------------------------------------------------------------------------------------

    @property
    def id(self) -> str: return self._json_obj[self.ID]
    #----------------------------------------------------------------------------------------------

    @property
    def birth_date(self) -> str: return self._json_obj[self.BDATE]
    #----------------------------------------------------------------------------------------------

    @property
    def sex(self) -> str: return self._json_obj[self.SEX]
    #----------------------------------------------------------------------------------------------

    @property
    def iadocs(self) -> dict[str:str]: return self._json_obj[self.IADOCS]
    #----------------------------------------------------------------------------------------------

    @property
    def srcdocs(self) -> dict[str:str]: return self._json_obj[self.SRCDOCS]
    #----------------------------------------------------------------------------------------------

    @name.setter
    def name(self, v): self._json_obj[self.NAME] = v
    #----------------------------------------------------------------------------------------------

    @apellidos.setter
    def apellidos(self, v): self._json_obj[self.APELLIDOS] = v
    #----------------------------------------------------------------------------------------------

    @id.setter
    def id(self, v): self._json_obj[self.ID] = v
    #----------------------------------------------------------------------------------------------

    @birth_date.setter
    def birth_date(self, v): self._json_obj[self.BDATE] = v
    #----------------------------------------------------------------------------------------------

    @sex.setter
    def sex(self, v): self._json_obj[self.SEX] = v
    #----------------------------------------------------------------------------------------------

    @iadocs.setter
    def iadocs(self, v): self._json_obj[self.IADOCS] = v
    #----------------------------------------------------------------------------------------------

    def add_ia_doc(self, k, v): self._json_obj[self.IADOCS][k] = v
    #----------------------------------------------------------------------------------------------

    @srcdocs.setter
    def srcdocs(self, v): self._json_obj[self.SRCDOCS] = v
    #----------------------------------------------------------------------------------------------

    def add_src_doc(self, k, v): self._json_obj[self.SRCDOCS][k] = v
    #----------------------------------------------------------------------------------------------

    def get_context(self):
        context = ""
        for _, c in self.iadocs.items():
            context += c
        return context
    #----------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------

class PatientContextFactory:
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
