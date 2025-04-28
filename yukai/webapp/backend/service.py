import  os
import  time

from    database.olddatabase            import  PacientesDB
from    ia.client                       import  InferenceModelClient
from    ia.prompt                       import  DoctorPrompt
from    models.models                   import  *
from    tools.tools                     import  elapsed_time_to_str
from    webapp.backend.environment      import  Environment
#--------------------------------------------------------------------------------------------------

class BackendService:
    service_instance = None
    #----------------------------------------------------------------------------------------------
    
    # Función que devuelve la instancia compartida
    @classmethod
    def get_service_instance(cls, model):
        if cls.service_insatnce is None:
            cls.service_insatnce = cls(model)

        return cls.service_insatnce
    #----------------------------------------------------------------------------------------------

    @staticmethod
    def get_generation_time(ref_ts):
        return elapsed_time_to_str(time.time() - ref_ts)
    #----------------------------------------------------------------------------------------------

    def __init__(self, env: Environment):
        self._env           = env
        self._pacientes_db  = PacientesDB(env.clients_dir)
        self._opena_ai      = InferenceModelClient.openai(os.getenv('oai_api_key'))
        self._huggingface   = InferenceModelClient.huggingface(os.getenv('hf_api_key'))
    #----------------------------------------------------------------------------------------------

    def get_pacientes(self, pattern):
        return   self._pacientes_db.get_matching_pacientes(pattern)
    #----------------------------------------------------------------------------------------------

    def get_paciente_info(self, ref_id):
        return self._pacientes_db.get_consolidated_paciente(ref_id)
    #----------------------------------------------------------------------------------------------

    def chat(self, ref_id, question, model_ref: str):
        start_ts = time.time()
        try:
            self._env.log.info(f"Cosulta sobre el paciente {ref_id}")
            self._env.log.info(question)

            model = None

            if "gpt" in model_ref.lower():
                inference_model = self._opena_ai

                if "o3" in model_ref.lower():
                    model = "o3-mini"
                elif "o4" in model_ref.lower():
                    model = "gpt-4o-mini"
                else:
                    model = "gpt-4o-mini"
            else: 
                inference_model = self._huggingface

                if "llama" in model_ref.lower():
                    if "3b" in model_ref.lower():
                        model = "meta-llama/Llama-3.2-3B-Instruct"
                    elif "8b" in model_ref.lower():
                        model = "meta-llama/Llama-3.1-8B-Instruct"
                elif "phi" in model_ref.lower():
                    if "-2" in model_ref.lower():
                        model = "microsoft/phi-2"
                    elif "-4" in model_ref.lower():
                        model = "microsoft/Phi-4-mini-instruct"
                elif "mistral" in model_ref.lower():
                    model = "mistralai/Mistral-7B-Instruct-v0.3"
                elif "c4ai" in model_ref.lower():
                    model = "CohereLabs/c4ai-command-r7b-12-2024"
            if model_ref is None:
                    model = "meta-llama/Llama-3.2-3B-Instruct"

            self._env.log.info(f"Modelo: {model}")
            
            contexto    = self._pacientes_db.get_contexto_paciente(ref_id)

            if contexto:
                prompt      = DoctorPrompt(contexto, question)
                response    = inference_model.chat(prompt, model)
                gen_time    = self.get_generation_time(start_ts)
                
                self._env.log.info(f"Respuesta obtenida en {gen_time}")

                return response, gen_time
            else:
                self._env.log.error("Paciente no encontrado")
                return "Paciente no encontrado", self.get_generation_time(start_ts)
        except Exception as ex:
            self._env.log.exception(ex)
            return "Error. Modelo no responde", self.get_generation_time(start_ts)
    #----------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------


