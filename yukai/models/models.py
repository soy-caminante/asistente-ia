from    dataclasses             import  dataclass
from    tools.tools             import  get_elapsed_years
from difflib import SequenceMatcher
#--------------------------------------------------------------------------------------------------

@dataclass
class PacienteShort:
    db_id:              str
    dni:                str
    ref_id:             str
    nombre:             str
    apellidos:          str
    fecha_nacimiento:   str
    sexo:               str

    @property
    def edad(self): return get_elapsed_years(self.fecha_nacimiento)
    #----------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------

class Paciente:
    def __init__(self):
        self._db_id             = ""
        self._dni               = ""
        self._ref_id            = ""
        self._nombre            = ""
        self._apellidos         = ""
        self._fecha_nacimiento  = ""
        self._sexo              = ""
        self._medicacion        = [ ]
        self._antecedentes      = [ ]
        self._alergias          = [ ]
        self._factores_riesgo   = [ ]
        self._visitas           = [ ]
        self._ingresos          = [ ]
        self._documentos        = [ ]
    #----------------------------------------------------------------------------------------------

    @property
    def db_id(self): return self._db_id
    #----------------------------------------------------------------------------------------------

    @db_id.setter
    def db_id(self, v): self._db_id = v
    #----------------------------------------------------------------------------------------------

    @property
    def dni(self): return self._dni
    #----------------------------------------------------------------------------------------------

    @dni.setter
    def dni(self, v): self._dni = v
    #----------------------------------------------------------------------------------------------

    @property
    def ref_id(self): return self._ref_id
    #----------------------------------------------------------------------------------------------

    @ref_id.setter
    def ref_id(self, v): self._ref_id = v
    #----------------------------------------------------------------------------------------------

    @property
    def nombre(self): return self._nombre
    #----------------------------------------------------------------------------------------------

    @nombre.setter
    def nombre(self, v): self._nombre = v
    #----------------------------------------------------------------------------------------------

    @property
    def apellidos(self): return self._apellidos
    #----------------------------------------------------------------------------------------------

    @apellidos.setter
    def apellidos(self, v): self._apellidos = v
    #----------------------------------------------------------------------------------------------

    @property
    def fecha_nacimiento(self): return self._fecha_nacimiento
    #----------------------------------------------------------------------------------------------

    @fecha_nacimiento.setter
    def fecha_nacimiento(self, v): self._fecha_nacimiento = v
    #----------------------------------------------------------------------------------------------

    @property
    def edad(self): return get_elapsed_years(self.fecha_nacimiento)
    #----------------------------------------------------------------------------------------------

    @property
    def sexo(self): return self._sexo
    #----------------------------------------------------------------------------------------------

    @sexo.setter
    def sexo(self, v): self._sexo = v
    #----------------------------------------------------------------------------------------------

    @property
    def medicacion(self): return self._medicacion
    #----------------------------------------------------------------------------------------------

    @medicacion.setter
    def medicacion(self, v): self._medicacion = v
    #----------------------------------------------------------------------------------------------

    @property
    def antecedentes(self): return self._antecedentes
    #----------------------------------------------------------------------------------------------

    @antecedentes.setter
    def antecedentes(self, v): self._antecedentes = v
    #----------------------------------------------------------------------------------------------

    @property
    def alergias(self): return self._alergias
    #----------------------------------------------------------------------------------------------

    @alergias.setter
    def alergias(self, v): self._alergias = v
    #----------------------------------------------------------------------------------------------

    @property
    def factores_riesgo(self): return self._factores_riesgo
    #----------------------------------------------------------------------------------------------

    @factores_riesgo.setter
    def factores_riesgo(self, v): self._factores_riesgo = v
    #----------------------------------------------------------------------------------------------

    @property
    def visitas(self): return self._visitas
    #----------------------------------------------------------------------------------------------

    @visitas.setter
    def visitas(self, v): self._visitas = v
    #----------------------------------------------------------------------------------------------

    @property
    def ingresos(self): return self._ingresos
    #----------------------------------------------------------------------------------------------

    @ingresos.setter
    def ingresos(self, v): self._ingresos = v
    #----------------------------------------------------------------------------------------------

    @property
    def documentos(self): return self._documentos
    #----------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------

@dataclass 
class DocumentoSrc:
    nombre          : str
    path            : str
    tipo            : str
    size            : int
#--------------------------------------------------------------------------------------------------

@dataclass
class ExpedienteSrc:
    db_id               : str
    dni                 : str
    ref_id              : str
    nombre              : str
    apellidos           : str
    fecha_nacimiento    : str
    sexo                : str
    documentos          : list[DocumentoSrc]
#--------------------------------------------------------------------------------------------------

@dataclass 
class DocumentoCon:
    nombre          : str
    path            : str
    tipo            : str
    size            : int
    tokens          : int
#--------------------------------------------------------------------------------------------------

@dataclass
class ExpedienteCon:
    db_id               : str
    dni                 : str
    ref_id              : str
    nombre              : str
    apellidos           : str
    fecha_nacimiento    : str
    sexo                : str
    documentos          : list[DocumentoCon]
#--------------------------------------------------------------------------------------------------
