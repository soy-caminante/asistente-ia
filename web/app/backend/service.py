import  os
import  pathlib
import  time

from    app.backend.db                  import *
from    app.backend.ia.inferenceclient  import *
from    app.backend.ia.prompt           import *
from    app.backend.tools               import *
#--------------------------------------------------------------------------------------------------

STORAGE_PATH = (pathlib.Path(__file__).parent / "../../data").resolve()
#--------------------------------------------------------------------------------------------------

class BackendService:
    def __init__(self, storage_path=STORAGE_PATH):
        self._docs_path         = storage_path / "src-docs"
        self._oai_context       = InferenceContext.openai(os.getenv('oai_api_key'))
        self._oai_context.model = "gpt-4o-mini"
        self._db                = NoSQLDB(storage_path / "dbs/documents.fs", self.log_callback)
        self._pacientes_db      = DbPacienteMngr(self._db)
    #----------------------------------------------------------------------------------------------

    def log_callback(self, info):
        if isinstance(info, Exception): 
            print(info)
        else:
            print(info)
    #----------------------------------------------------------------------------------------------

    def get_pacientes(self, pattern):
        return   self._pacientes_db.get_pacientes(pattern)
    #----------------------------------------------------------------------------------------------

    def get_paciente_info(self, ref_id):
        paciente = self._pacientes_db.get_paciente(ref_id)
        
        if paciente is None: return None

        return paciente
    #----------------------------------------------------------------------------------------------

    def chat(self, ref_id, question):
        paciente = self._pacientes_db.get_paciente(ref_id)
        
        if paciente is None: return None

        self._oai_context.full_context = ""

        for doc in paciente.documentos:
            if self._oai_context.full_context != "": 
                self._oai_context.full_context += "\n"
            self._oai_context.full_context += doc["contenido"]

        self._oai_context.update_chunks()

        if len(self._oai_context.chunks) == 0:
            return "No hay información para responder a la pregunta"

        prompts  = [ ]

        for chunk in self._oai_context.chunks:
            prompts.append(Prompt(chunk, question))

        current_ts  = time.time()
        response    = self._oai_context.chat(prompts)
        gen_time    = elapsed_time_to_str(time.time() - current_ts)
        
        return f"Tiempo de generación: {gen_time}\n{response}"
    #----------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------

# Crear una instancia singleton
service_insatnce = BackendService()
#--------------------------------------------------------------------------------------------------

# Función que devuelve la instancia compartida
def get_service_instance():
    return service_insatnce
#--------------------------------------------------------------------------------------------------

