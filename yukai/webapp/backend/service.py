import  os
import  pathlib
import  unicodedata
import  time

from    dataclasses                     import  dataclass
from    ia.client                       import  InferenceModelClient
from    ia.context                      import  PatientContextFactory, CompactEncoder, PatientContext
from    ia.prompt                       import  DoctorPrompt
from    webapp.backend.environment      import  Environment
from    webapp.backend.tools            import  *
from    webapp.models.models            import  *
#--------------------------------------------------------------------------------------------------

class PacientesDB:
    @dataclass
    class DbIndex:
        id:         str
        direct:     str
        reverse:    str
        paciente:   Paciente
    #-----------------------------------------------------------------------------------------------

    def __init__(self, base: pathlib.Path):
        self._base          = base
        self._files_factory = PatientContextFactory()
        self._file_decoder  = CompactEncoder()
    #----------------------------------------------------------------------------------------------

    def check_paciente(self, ref_id:str): return ref_id in self._db.root
    #----------------------------------------------------------------------------------------------

    def get_paciente(self, ref_id:str) -> Paciente:
        target_dir  = self._base / ref_id
        ret         = None

        if target_dir.exists():
            context = self._files_factory.load_consolidated(target_dir)
            if context:
                ret = Paciente()
                ret.nombre              = context.name
                ret.apellidos           = context.apellidos
                ret.fecha_nacimiento    = context.fecha_nacimiento
                ret.sexo                = context.sexo
                ret.ref_id              = context.id

                for _, file in context.iadocs.items():
                    file_dict = self._file_decoder.decode(file)
                    for a in self._file_decoder.get_alergias(file_dict):
                        ret.alergias.append(a)
                    for a in self._file_decoder.get_riesgo_cardio(file_dict):
                        ret.factores_riesgo.append(a)
                    for a in self._file_decoder.get_antecedentes(file_dict):
                        ret.antecedentes.append(a)
                    for a in self._file_decoder.get_ingresos(file_dict):
                        ret.ingresos.append(a)
                    for a in self._file_decoder.get_visitas(file_dict):
                        ret.visitas.append(a)
                    for a in self._file_decoder.get_medicacion(file_dict):
                        ret.medicacion.append(a)
        return ret
    #----------------------------------------------------------------------------------------------

    def get_contexto_paciente(self, ref_id: str) -> PatientContext:
        return self._files_factory.load_consolidated(self._base / ref_id)
    #----------------------------------------------------------------------------------------------

    def get_pacientes(self, pattern) -> list[Paciente]:
        def normalize(text):
            return unicodedata.normalize("NFKD", text).encode("ASCII", "ignore").decode("utf-8")

        ret                                     = [ ]
        refs_list: list[PacientesDB.DbIndex]    = [ ]

        if pattern == "": return ret
        
        for obj in self._base.iterdir():
            if not obj.is_dir(): continue

            paciente_info = PatientContextFactory.get_patient_id(obj)
            if paciente_info:
                paciente            = Paciente()
                paciente.nombre     = paciente_info.nombre
                paciente.apellidos  = paciente_info.apellidos
                paciente.ref_id     = paciente_info.id

                refs_list.append(PacientesDB.DbIndex(   obj.stem, 
                                                        normalize(f"{paciente_info.apellidos} {paciente_info.nombre}").lower(),
                                                        normalize(f"{paciente_info.apellidos} {paciente_info.nombre}").lower(),
                                                        paciente))

        normalized_pattern  = normalize(pattern).lower()
        for ref in refs_list:
            if pattern == ref.id: 
                ret = [ ref.paciente ]
                break
            else:
                if ref.direct.startswith(normalized_pattern):
                    ret.append(ref.paciente)
        return ret
    #----------------------------------------------------------------------------------------------
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
        return   self._pacientes_db.get_pacientes(pattern)
    #----------------------------------------------------------------------------------------------

    def get_paciente_info(self, ref_id):
        return self._pacientes_db.get_paciente(ref_id)
    #----------------------------------------------------------------------------------------------

    def chat(self, ref_id, question, model: str):
        start_ts = time.time()
        try:
            self._env.log.info(f"Cosulta sobre el paciente {ref_id}")
            self._env.log.info(question)

            if "gpt" in model.lower():
                inference_model = self._opena_ai

                if "o3" in model.lower():
                    model = "o3-mini"
                elif "o4" in model.lower():
                    model = "gpt-4o-mini"
                else:
                    model = "gpt-4o-mini"
            else: 
                inference_model = self._huggingface

                if "3b" in model.lower():
                    model = "meta-llama/Llama-3.2-3B-Instruct"
                elif "8b" in model.lower():
                    model = "meta-llama/Llama-3.1-8B-Instruct"
                else:
                    model = "meta-llama/Llama-3.2-3B-Instruct"
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


