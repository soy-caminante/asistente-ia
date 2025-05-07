import  json
import  pathlib
import  re
import  shutil
import  tiktoken

from    database.context                    import  ClienteInfo, ExpedienteFileInfo
from    database.database                   import  ClientesDocumentStore
from    database.incomming                  import  IncommingStorage, IncommingFileInfo, IncommingCliente
from    difflib                             import  SequenceMatcher
from    models.models                       import  *
from    models.iacodec                      import  IACodec
from    ia.client                           import  ModelLoader, SystemPromts, HttpChatClient, OpenAiChatClient, HuggingFaceChatClient
from    pmanager.backend.environment        import  Environment
from    tools.tools                         import  StatusInfo, try_catch
from    tools.viewtools                     import  OverlayCtrlWrapper
#--------------------------------------------------------------------------------------------------

class DBOperator:
    def __init__(self,  db: ClientesDocumentStore):
        self._db    = db
    #----------------------------------------------------------------------------------------------

    def get_summary_explanation(self):
        return self._db.get_pretrained_by_filename("summary-explanation")
    #----------------------------------------------------------------------------------------------

    def get_summary_question(self):
        return self._db.get_pretrained_by_filename("summary-question")
    #----------------------------------------------------------------------------------------------

    def get_chat_explanation(self):
        return self._db.get_pretrained_by_filename("chat-explanation")
    #----------------------------------------------------------------------------------------------

    def set_summary_explanation(self, content: bytes):
        return self._db.add_pretrained("summary-explanation", content)
    #----------------------------------------------------------------------------------------------

    def set_summary_question(self, content: bytes):
        return self._db.add_pretrained("summary-question", content)
    #----------------------------------------------------------------------------------------------

    def set_chat_explanation(self, content: bytes):
        return self._db.add_pretrained("chat-explanation", content)
    #----------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------

class PretrainedManager:
    def __init__(self,  db_operator: DBOperator, model_name: str, gpu_enabled: bool):
        self._db_op                 = db_operator
        self._model                 = ModelLoader(model_name) if gpu_enabled else None
        self._summary_explanation   = None
        self._summary_question      = None
        self._chat_explanation      = None
        self._gpu_enabled           = gpu_enabled
        self._iacodec               = IACodec()
    #----------------------------------------------------------------------------------------------

    def load_pretrained(self):
        if self._gpu_enabled:
            self._summary_explanation = self._db_op.get_summary_explanation()
            self._summary_question    = self._db_op.get_summary_question()
            self._chat_explanation    = self._db_op.get_chat_explanation()

            if not self._summary_explanation:
                self._summary_explanation, binary = self._model.embed_gridfs_prompt(SystemPromts.SUMMARY_EXPLANATION)
                self._db_op.set_summary_explanation(binary)
            
            if not self._summary_question:
                self._summary_question, binary = self._model.embed_gridfs_prompt(SystemPromts.SUMMARY_QUESTION)
                self._db_op.set_summary_question(binary)
                
            if not self._chat_explanation:
                self._chat_explanation, binary = self._model.embed_gridfs_prompt(SystemPromts.CHAT_INFO_EXPLANATION)
                self._db_op.set_chat_explanation(binary)
    #----------------------------------------------------------------------------------------------

    def generate_embeddings_from_iadoc(self, doc_name, iadoc_dict):
        text = self._iacodec.encode(iadoc_dict, doc_name)
        if self._gpu_enabled:
            return self._model.embed_gridfs_prompt(text)
        
        tokenizer   = tiktoken.get_encoding("cl100k_base")
        num_tokens  = len(tokenizer.encode(text))

        return text.encode("utf-8"), num_tokens
    #----------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------

class BackendService:
    @staticmethod
    def extract_dictionary(text):
        """
        Intenta extraer un JSON válido desde una cadena, aunque esté escapada o tenga formato Markdown.
        """
        # 1. Eliminar delimitadores Markdown y etiquetas como ```json
        clean_text = re.sub(r'```(?:json)?', '', text, flags=re.IGNORECASE)
        clean_text = clean_text.strip('` \n')

        # 2. Si parece estar escapado (muchos \\n, \\") lo desescapamos
        if '\\n' in clean_text or '\\"' in clean_text:
            # Reemplazos básicos seguros
            clean_text = clean_text.replace('\\\\', '\\')  # primero dobles backslashes
            clean_text = clean_text.replace('\\n', '\n')
            clean_text = clean_text.replace('\\"', '"')

        clean_text = clean_text.strip()
        # 3. Intentar decodificar como JSON
        try:
            return json.loads(clean_text), clean_text
        except json.JSONDecodeError as e:
            raise ValueError(f"No se pudo interpretar el texto como JSON: {e}")
    #----------------------------------------------------------------------------------------------

    def __init__(self, env: Environment, overlay_ctrl: OverlayCtrlWrapper):
        self._env           = env
        self._clientes_db   = ClientesDocumentStore(env.log, 
                                                    env.db_docker_file,
                                                    env.db_port,
                                                    env.model_name if env.gpu else "no-gpu-db")
        self._db_operator   = DBOperator(self._clientes_db)
        self._pretrained    = PretrainedManager(self._db_operator, env.model_name, env.gpu)
        self._incomming_db  = IncommingStorage(env.log, env.db_dir)
        self._overlay_ctrl  = overlay_ctrl
        self._req_id        = 0

        if env.gpu:
            self._chat = HttpChatClient(env.chat_endpoint, env.log)
        else:
            self._chat = HuggingFaceChatClient(os.getenv("hf_api_key"), "mistralai/Mistral-7B-Instruct-v0.3", env.log)
            #self._chat = OpenAiChatClient(os.getenv("oai_api_key"), "gpt-4o-mini", env.log)

        self._env.log.add_excluded_locations(__file__, None)
    #----------------------------------------------------------------------------------------------

    def get_next_req_id(self):
        self._req_id += 1
        return f"pmanager-{self._req_id}"
    #----------------------------------------------------------------------------------------------

    def check_db(self) -> bool: 
        if self._clientes_db.ensure_mongo_ready():
            self._clientes_db.setup_db()
            return True
        return False
    #----------------------------------------------------------------------------------------------

    def log_info(self, info): self._env.log.info(info)
    #----------------------------------------------------------------------------------------------

    def log_warning(self, info): self._env.log.warning(info)
    #----------------------------------------------------------------------------------------------

    def log_error(self, info): self._env.log.error(info)
    #----------------------------------------------------------------------------------------------

    def log_exception(self, ex): self._env.log.exception(ex)
    #----------------------------------------------------------------------------------------------

    def log_info_and_return(self, info, ret_obj=True): 
        self._env.log.info(info)
        return StatusInfo.ok(ret_obj)
    #----------------------------------------------------------------------------------------------

    def log_error_and_return(self, info): 
        self._env.log.error(info)
        return StatusInfo.error(info)
    #----------------------------------------------------------------------------------------------

    @try_catch(Environment.log_fcn, StatusInfo.error("Error al cargar los contextos preentrenados"))
    def load_pretrained(self) -> StatusInfo[bool]:
        with self._overlay_ctrl.wait("Cargando contextos preentrenados"):
            self._pretrained.load_pretrained()
            return StatusInfo.ok(True)
    #----------------------------------------------------------------------------------------------

    @try_catch(Environment.log_fcn, StatusInfo.error("Error al obtener los clientes"))
    def load_all_consolidated_clientes(self) -> StatusInfo[list[ClienteInfo]]:
        with self._overlay_ctrl.wait("Cargando clientes consolidados"):
            self.log_info("Cargar los clientes consolidados")
            return self.log_info_and_return("Lista de clientes consolidados generad", self._clientes_db.get_all_clientes())
    #----------------------------------------------------------------------------------------------

    @try_catch(Environment.log_fcn, StatusInfo.error("Error al obtener el cliente"))
    def get_consolidated_cliente(self, paciente_id: str) -> StatusInfo[ClienteInfo]:
        with self._overlay_ctrl.wait("Leyendo el cliente"):
            cliente = None
            if cliente is None:
                return StatusInfo.error("Cliente no encontrado")
            else:
                return StatusInfo.ok(cliente)
    #----------------------------------------------------------------------------------------------

    @try_catch(Environment.log_fcn, StatusInfo.error("Error al obtener los clientes"))
    def load_all_src_clientes(self) -> StatusInfo[list[IncommingCliente]]:
        with self._overlay_ctrl.wait("Cargando clientes nuevos"):
            self.log_info("Cargar los nuevos clientes")
            return self.log_info_and_return("Lista de nuevos clientes generada", self._incomming_db.get_all())
    #----------------------------------------------------------------------------------------------

    @try_catch(Environment.log_fcn, StatusInfo.error("Error al preprocesar el cliente"))
    def preprocess_cliente(self, cliente_id: str) -> StatusInfo:
        pass
    #----------------------------------------------------------------------------------------------

    @try_catch(Environment.log_fcn, StatusInfo.error("Error al consolidar el cliente"))
    def consolidate_clientes(self, clientes_db_id: list[str]) -> StatusInfo[bool]:
        with self._overlay_ctrl.wait("Consolidando clientes"):
            for db_id in clientes_db_id:
                self.log_info(f"Consolidando el cliente {db_id}")

                cliente: IncommingCliente   = self._incomming_db.get_cliente_info(db_id)
                src_docs                    = [ ]
                iadocs                      = [ ]
                biadocs                     = [ ]
                for doc in cliente.docs:
                    if doc.is_plain_text:
                        self._overlay_ctrl.update(f"Cliente: {cliente.personal_info.id_interno}\nEstructurando el documento {doc.name}")

                        status = self._chat.get_structured_document(self.get_next_req_id(), doc.content)

                        if status:
                            self._overlay_ctrl.update(f"Cliente: {cliente.personal_info.id_interno}\nObteniendo embeddings de {doc.name}")

                            #iadoc           = '```json\\n{\\n  "fecha": "3 de febrero de 2024",\\n  "motivo": "Revisión del tratamiento y evaluación de síntomas",\\n  "síntomas": "Mejoría en disnea, palpitaciones ocasionales, fatiga leve",\\n  "estado físico": {\\n    "presión arterial": "140/85 mmHg",\\n    "frecuencia cardíaca": "88 lpm",\\n    "peso": "83 kg",\\n    "IMC": "27.7"\\n  },\\n  "medicación": {\\n    "enalapril": "10 mg",\\n    "metoprolol": "50 mg"\\n  },\\n  "tratamiento": "Holter de 24 horas para evaluar palpitaciones",\\n  "recomendaciones": "Reforzar dieta y actividad física",\\n  "diagnósticos": "Mejora parcial en presión arterial y síntomas de disnea"\\n}\\n```'

                            iadoc               = status.get()
                            iadoc_dict, iadoc   = BackendService.extract_dictionary(iadoc)
                            biadoc, btokens     = self._pretrained.generate_embeddings_from_iadoc(doc.name, iadoc_dict)

                            src_docs.append({   "filename":             doc.name,
                                                "content":              doc.content.encode("utf-8"),
                                                "mime":                 doc.mime,
                                                 "ts":                  doc.ts })

                            iadocs.append({ "filename":                 doc.name,
                                            "content":                  iadoc.encode("utf-8"),
                                            "source_mime":              doc.mime,
                                            "ts":                       doc.ts,
                                            "tokens":                   doc.tokens })

                            biadocs.append({"filename":             doc.name,
                                            "content":              biadoc,
                                            "source_mime":          doc.mime,
                                            "ts":                   doc.ts,
                                            "tokens":               btokens})
                        else:
                            return self.log_error_and_return("Error al estructurar el documento")

                for doc in cliente.docs:
                    if not doc.is_plain_text:
                        src_docs.append({   "filename":             doc.name,
                                            "content":              doc.content.encode("utf-8"),
                                            "mime":                 doc.mime,
                                            "ts":                   doc.ts })
                
                cliente_info: ClienteInfo = self._clientes_db.get_cliente_by_id_interno(cliente.personal_info.id_interno)
                
                if cliente_info is None:
                    self._overlay_ctrl.update(f"Cliente: {cliente.personal_info.id_interno}\nGenerando información predefinida")
                    status = self._chat.get_predefined_info(self.get_next_req_id(), iadocs)
                    
                    if status:
                        expediente: ExpedienteSummary = status.get()
                        if self._clientes_db.add_cliente(   cliente.personal_info.nombre,
                                                            cliente.personal_info.apellidos,
                                                            cliente.personal_info.sexo,
                                                            cliente.personal_info.fecha_nacimiento,
                                                            cliente.personal_info.dni,
                                                            cliente.personal_info.id_interno,
                                                            expediente.antecedentes_familiares,        
                                                            expediente.factores_riesgo_cardiovascular,
                                                            expediente.medicacion,                     
                                                            expediente.alergias,                     
                                                            expediente.ingresos,                       
                                                            expediente.ultimas_visitas,
                                                            src_docs,
                                                            iadocs,
                                                            biadocs):
                            self._incomming_db.set_as_consolidated(db_id)
                            self.log_info(f"Cliente {db_id} consolidado")
                        else:
                            return self.log_error_and_return("Error al consolidar el cliente")
                    else:
                        return self.log_error_and_return("Error al resumir el expediente")
                else:
                    existing_iadocs = self._clientes_db.get_all_iadocs(cliente.personal_info.id_interno)
                    aux_iadocs      = iadocs.copy()

                    for doc in existing_iadocs:
                        aux_iadocs.append({ "filename":     doc.name,
                                            "content":      doc.content.decode("utf-8"),
                                            "source_mime":  doc.source_mime,
                                            "ts":           doc.ts,
                                            "tokens":       doc.tokens })
                    self._overlay_ctrl.update(f"Cliente: {cliente.personal_info.id_interno}\nGenerando información predefinida")
                    status = self._chat.get_predefined_info(self.get_next_req_id(), aux_iadocs)

                    if status:
                        expediente: ExpedienteSummary = status.get()
                        if self._clientes_db.update_cliente(db_id                           = cliente_info.db_id,
                                                            antecedentes_familiares         = expediente.antecedentes_familiares,
                                                            factores_riesgo_cardiovascular  = expediente.factores_riesgo_cardiovascular,
                                                            medicacion                      = expediente.medicacion,                     
                                                            alergias                        = expediente.alergias,                     
                                                            ingresos                        = expediente.ingresos,                       
                                                            ultimas_visitas                 = expediente.ultimas_visitas,
                                                            src_docs                        = src_docs,
                                                            iadocs                          = iadocs,
                                                            biadocs                         = biadocs):
                            self._incomming_db.set_as_consolidated(db_id)
                            self.log_info(f"Cliente {db_id} consolidado")
                        else:
                            return self.log_error_and_return("Error al consolidar el cliente")
                        
            self.log_info("Consolidación finalizada")
            return StatusInfo.ok(True)
    #----------------------------------------------------------------------------------------------

    @try_catch(Environment.log_fcn, StatusInfo.error("Error al eliminar el cliente"))
    def delete_src_clientes(self, clientes: list[pathlib.Path]) -> StatusInfo[list[IncommingCliente]]:
        with self._overlay_ctrl.wait("Eliminando clientes"):
            for c in clientes: 
                if c.exists() and c.is_dir():
                    shutil.rmtree(c)
            return self.load_all_src_clientes()
    #----------------------------------------------------------------------------------------------

    def delete_consolidated_clientes(self, clientes: list[str]) -> StatusInfo[list[ClienteInfo]]:
        for c in clientes:
            cliente = self._clientes_db.get_cliente_by_db_id(c)
            if cliente:
                self.log_info(f"Eliminar el cliente {cliente.id_interno}")
                self._clientes_db.delete_cliente(c)
                self.log_info(f"Cliente {cliente.id_interno} eliminado")
            else:
                self.log_warning(f"El cliente con db_id {c} no existe y no se puede eliminar")
        return self.load_all_consolidated_clientes() 
    #----------------------------------------------------------------------------------------------

    def remove_src_duplicates(self):
        return self.remove_duplicates(self.check_src_duplicates(), self.load_all_src_clientes)
    #----------------------------------------------------------------------------------------------

    def remove_consolidated_duplicates(self):
        return self.remove_duplicates(self.check_consolidated_duplicates(), self.load_all_consolidated_clientes)
    #----------------------------------------------------------------------------------------------

    @try_catch(Environment.log_fcn, StatusInfo.error("Error al eliminar los duplicados del paciente"))
    def remove_duplicates(self, status: StatusInfo[list[IncommingCliente | ClienteInfo]], load_fcn: callable):
        with self._overlay_ctrl.wait("Eliminando duplicados"):
            if status:
                duplicates = status.get()

                for p, _ in duplicates:
                    p: IncommingCliente | ClienteInfo
                    try:
                        pathlib.Path(p.db_id).unlink(missing_ok=True)
                    except Exception as ex:
                        self.log_exception(ex)
                return load_fcn()
            else:
                return status
    #----------------------------------------------------------------------------------------------

    def check_src_duplicates(self): return self.check_duplicates(self.load_all_src_clientes())
    #----------------------------------------------------------------------------------------------

    def check_consolidated_duplicates(self): return self.check_duplicates(self.load_all_consolidated_clientes())
    #----------------------------------------------------------------------------------------------

    @try_catch(Environment.log_fcn, StatusInfo.error("Error al obtener los duplicados del paciente"))
    def check_duplicates(self, status) -> StatusInfo[list[(IncommingCliente, IncommingCliente)]]:
        with self._overlay_ctrl.wait("Buscando duplicados"):
            status = self.load_all_src_clientes()

            if status:
                pacientes: list[IncommingCliente]= status.get()
                
                if len(pacientes) == 0:
                    return StatusInfo.ok([])
                duplicates = []
                
                for i, paciente1 in enumerate(pacientes):
                    paciente1: IncommingCliente
                    for j, paciente2 in enumerate(pacientes):
                        paciente2: IncommingCliente
                        if i >= j: continue

                        if paciente1.personal_info.dni == paciente2.personal_info.dni or paciente1.personal_info.id_interno == paciente2.personal_info.id_interno:
                            duplicates.append((paciente1, paciente2))
                        else:
                            full_name_1 = f"{paciente1.personal_info.nombre} {paciente1.personal_info.apellidos}"
                            full_name_2 = f"{paciente2.personal_info.nombre} {paciente2.personal_info.apellidos}"
                            reversed_name_2 = f"{paciente2.personal_info.apellidos} {paciente2.personal_info.nombre}"
                            similarity_1 = SequenceMatcher(None, full_name_1, full_name_2).ratio()
                            similarity_2 = SequenceMatcher(None, full_name_1, reversed_name_2).ratio()
                            if similarity_1 > 0.9 or similarity_2 > 0.9:
                                duplicates.append((paciente1, paciente2))
                return duplicates
            else:
                return StatusInfo.error("Error al buscar pacientes duplicados")
    #----------------------------------------------------------------------------------------------

    @try_catch(Environment.log_fcn, StatusInfo.error("Error al obtener la información del paciente"))
    def inspect_src_cliente(self, db_id: pathlib.Path) -> StatusInfo[ExpedienteSrc]:
        self.log_info(f"Cargar cliente nuevo: {db_id}")
        cliente = self._incomming_db.get_cliente_info(db_id)
        if cliente:
            return self.log_info_and_return("Cliente cargado", cliente)
        else:
            return self.log_error_and_return("Cliente no encontrado")
    #----------------------------------------------------------------------------------------------

    @try_catch(Environment.log_fcn, StatusInfo.error("Error al obtener la información del paciente"))
    def inspect_consolidated_cliente(self, db_id: str) -> StatusInfo[ClienteMetaInformation]:
        self.log_info(f"Cargar cliente consolidado: {db_id}")
        cliente = self._clientes_db.get_cliente_by_db_id(db_id)
        if cliente:
            biadocs     = self._clientes_db.get_all_biadoc_meta(db_id)
            iadocs      = self._clientes_db.get_all_iadoc_meta(db_id)
            srcdocs     = self._clientes_db.get_all_source_meta(db_id)
            summary     = self._clientes_db.get_expediente_by_cliente_db_id(db_id)

            return self.log_info_and_return("Cliente cargado", ClienteMetaInformation(cliente, srcdocs, iadocs, biadocs, summary))
        else:
            return self.log_error_and_return("Cliente no encontrado")
    #----------------------------------------------------------------------------------------------

    @try_catch(Environment.log_fcn, StatusInfo.error("Error al cargar el documento"))
    def load_incomming_document(self, db_id: str) -> StatusInfo[bytes]:
        self.log_info(f"Cargar el documento fuente {db_id}")
        return self.log_info_and_return("Documento cargado", self._incomming_db.get_document(db_id))
    #----------------------------------------------------------------------------------------------

    @try_catch(Environment.log_fcn, StatusInfo.error("Error al cargar el documento"))
    def load_conslidated_src_document(self, db_id: str) -> StatusInfo[bytes]:
        self.log_info(f"Cargar el documento fuente consolidado {db_id}")
        return self.log_info_and_return("Documento cargado", self._clientes_db.get_source_doc_content_by_id(db_id))
    #----------------------------------------------------------------------------------------------

    @try_catch(Environment.log_fcn, StatusInfo.error("Error al cargar el documento"))
    def load_conslidated_iadoc(self, db_id: str) -> StatusInfo[bytes]:
        self.log_info(f"Cargar el documento iadoc consolidado {db_id}")
        return self.log_info_and_return("Documento cargado", self._clientes_db.get_iadoc_content_by_id(db_id))
    #----------------------------------------------------------------------------------------------

    @try_catch(Environment.log_fcn, StatusInfo.error("Error al cargar el documento"))
    def load_conslidated_biadoc(self, db_id: str) -> StatusInfo[bytes]:
        self.log_info(f"Cargar el documento biadoc consolidado {db_id}")
        return self.log_info_and_return("Documento cargado", self._clientes_db.get_biadoc_content_by_id(db_id))
    #----------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------


