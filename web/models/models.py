from persistent import Persistent
#--------------------------------------------------------------------------------------------------

class Paciente(Persistent):
    def __init__(self):
        self._ref_id            = ""
        self._nombre            = ""
        self._apellidos         = ""
        self._fecha_nacimiento  = ""
        self._sexo              = ""
        self._medicacion        = ""
        self._antecedentes      = ""
        self._alergias          = ""
        self._factores_riesgo   = ""
        self._visitas           = ""
        self._ingresos          = ""
        self._documentos        = [ ]
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

