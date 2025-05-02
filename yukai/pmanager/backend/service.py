import  pathlib
import  shutil

from    database.context                    import  ClienteInfo, ExpedienteFileInfo
from    database.database                   import  ClientesDocumentStore
from    database.incomming                  import  IncommingStorage, IncommingFileInfo, IncommingCliente
from    difflib                             import  SequenceMatcher
from    models.models                       import  *
from    ia.client                           import  ModelLoader, SystemPromts, HttpChatClient, OpenAiChatClient
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

class PretrainedManger:
    def __init__(self,  db_operator: DBOperator, model_name: str, gpu_enabled: bool):
        self._db_op                 = db_operator
        self._model                 = ModelLoader(model_name) if gpu_enabled else None
        self._summary_explanation   = None
        self._summary_question      = None
        self._chat_explanation      = None
        self._gpu_enabled           = gpu_enabled
    #----------------------------------------------------------------------------------------------

    def load_pretrained(self):
        if self._gpu_enabled:
            self._summary_explanation = self._db_op.get_summary_explanation()
            self._summary_question    = self._db_op.get_summary_question()
            self._chat_explanation    = self._db_op.get_chat_explanation()

            if not self._summary_explanation:
                self._summary_explanation, binary = self._model.embed_prompt_binary(SystemPromts.SUMMARY_EXPLANATION)
                self._db_op.set_summary_explanation(binary)
            
            if not self._summary_question:
                self._summary_question, binary = self._model.embed_prompt_binary(SystemPromts.SUMMARY_QUESTION)
                self._db_op.set_summary_question(binary)
                
            if not self._chat_explanation:
                self._chat_explanation, binary = self._model.embed_prompt_binary(SystemPromts.CHAT_INFO_EXPLANATION)
                self._db_op.set_chat_explanation(binary)
    #----------------------------------------------------------------------------------------------

    def generate_embeddings(self, text):
        if self._gpu_enabled:
            _, binary = self._model.embed_prompt_binary(text)
            return binary
        return "Hola, mundo".encode("utf-8")
    #----------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------

class BackendService:
    def __init__(self, env: Environment, overlay_ctrl: OverlayCtrlWrapper):
        self._env           = env
        self._clientes_db   = ClientesDocumentStore(env.log, 
                                                    env.db_docker_file,
                                                    env.db_endpoint,
                                                    env.model_name if env.gpu else "no-gpu-db")
        self._db_operator   = DBOperator(self._clientes_db)
        self._pretrained    = PretrainedManger(self._db_operator, env.model_name, env.gpu)
        self._incomming_db  = IncommingStorage(env.log, env.db_dir)
        self._chat          = HttpChatClient(env.chat_endpoint, env.log) if env.gpu else OpenAiChatClient(os.getenv("oai_api_key"), "gpt-4o-mini",env.log)
        self._overlay_ctrl  = overlay_ctrl
        self._req_id        = 0
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

    def log_error(self, info): self._env.log.error(info)
    #----------------------------------------------------------------------------------------------

    def log_exception(self, ex): self._env.log.exception(ex)
    #----------------------------------------------------------------------------------------------

    def log_info_and_return(self, info, ret_obj=True): 
        self._env.log.info(info)
        return StatusInfo.ok(info)
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
        with self._overlay_ctrl.wait("Cargando pacientes consolidados"):
            return StatusInfo.ok(self._clientes_db.get_all_clientes())
    #----------------------------------------------------------------------------------------------

    @try_catch(Environment.log_fcn, StatusInfo.error("Error al obtener el cliente"))
    def get_consolidated_cliente(self, paciente_id: str) -> StatusInfo[Paciente]:
        with self._overlay_ctrl.wait("Leyendo el paciente"):
            paciente = None
            if paciente is None:
                return StatusInfo.error("Paciente no encontrado")
            else:
                return StatusInfo.ok(paciente)
    #----------------------------------------------------------------------------------------------

    @try_catch(Environment.log_fcn, StatusInfo.error("Error al obtener los clientes"))
    def load_all_src_clientes(self) -> StatusInfo[list[IncommingCliente]]:
        with self._overlay_ctrl.wait("Cargando nuevos pacientes"):
            return StatusInfo.ok(self._incomming_db.get_all())
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

                            iadoc   = status.get()
                            biadoc  = self._pretrained.generate_embeddings(iadoc)
                            src_docs.append({   "filename":             doc.name,
                                                "content":              doc.content.encode("utf-8"),
                                                "mime":                 doc.mime })

                            iadocs.append({ "filename":                 doc.name,
                                            "content":                  iadoc.encode("utf-8"),
                                            "source_mime":              doc.mime,
                                            "tokens":                   doc.tokens })

                            biadocs.append({"filename":             doc.name,
                                            "content":              biadoc,
                                            "source_mime":          doc.mime,
                                            "tokens":               doc.tokens})
                        else:
                            return self.log_error_and_return("Error al estructurar el documento")

                for doc in cliente.docs:
                    if not doc.is_plain_text:
                        src_docs.append({   "filename":             doc.name,
                                            "content":              doc.content.encode("utf-8"),
                                            "mime":                 doc.mime })
                
                self._overlay_ctrl.update(f"Cliente: {cliente.personal_info.id_interno}\nGenerando información predefinida")
                status = self._chat.get_predefined_info(self.get_next_req_id(), iadocs)
                
                if status:
                    expediente: ExpedienteBasicInfo = status.get()
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
            self.log_info("Consolidación finalizada")

            return self.load_all_src_clientes()
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
            self._clientes_db.delete_cliente(c)
        return self.load_all_consolidated_clientes() 
    #----------------------------------------------------------------------------------------------

    def remove_src_duplicates(self):
        return self.remove_duplicates(self.check_src_duplicates(), self.load_all_src_clientes)
    #----------------------------------------------------------------------------------------------

    def remove_consolidated_duplicates(self):
        return self.remove_duplicates(self.check_consolidated_duplicates(), self.load_all_consolidated_clientes)
    #----------------------------------------------------------------------------------------------

    @try_catch(Environment.log_fcn, StatusInfo.error("Error al eliminar los duplicados del paciente"))
    def remove_duplicates(self, status: StatusInfo[list[(Paciente, Paciente)]], load_fcn: callable):
        with self._overlay_ctrl.wait("Eliminando duplicados"):
            if status:
                duplicates = status.get()

                for p, _ in duplicates:
                    p: Paciente
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
    def check_duplicates(self, status) -> StatusInfo[list[(Paciente, Paciente)]]:
        with self._overlay_ctrl.wait("Buscando duplicados"):
            status = self.load_all_src_clientes()

            if status:
                pacientes: list[PacienteShort]= status.get()
                
                if len(pacientes) == 0:
                    return StatusInfo.ok([])
                duplicates = []
                
                for i, paciente1 in enumerate(pacientes):
                    paciente1: PacienteShort
                    for j, paciente2 in enumerate(pacientes):
                        paciente2: PacienteShort
                        if i >= j: continue

                        if paciente1.dni == paciente2.dni or paciente1.ref_id == paciente2.ref_id:
                            duplicates.append((paciente1, paciente2))
                        else:
                            full_name_1 = f"{paciente1.nombre} {paciente1.apellidos}"
                            full_name_2 = f"{paciente2.nombre} {paciente2.apellidos}"
                            reversed_name_2 = f"{paciente2.apellidos} {paciente2.nombre}"
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
        cliente = self._incomming_db.get_cliente_info(db_id)
        if cliente:
            return StatusInfo.ok(cliente)
        else:
            return StatusInfo.error("Paciente no encontrado")
    #----------------------------------------------------------------------------------------------

    @try_catch(Environment.log_fcn, StatusInfo.error("Error al obtener la información del paciente"))
    def inspect_consolidated_cliente(self, owner: str) -> StatusInfo[ClienteMetaInformation]:
        cliente = self._clientes_db.get_cliente_by_id_interno(owner)
        if cliente:
            biadocs = self._clientes_db.get_all_biadoc_meta(owner)
            iadocs  = self._clientes_db.get_all_iadoc_meta(owner)
            srcdocs = self._clientes_db.get_all_source_meta(owner)

            src_list:   list[SrcDocInfo]    = [ ]
            ia_list:    list[IaDcoInfo]     = [ ]
            bia_list:   list[BIaDcoInfo]    = [ ]
            for src in srcdocs:
                found = False
                for bia in biadocs:
                    if src.db_id == bia.source_ref:
                        found = True
                        bia_list.append(bia)
                        break
                if not found:
                    for ia in iadocs:
                        if src.db_id == ia.source_ref:
                            found = True
                            ia_list.append(bia)
                            break
                if not found:
                    src_list.append(src)

            return StatusInfo.ok(ClienteMetaInformation(cliente, src_list, ia_list, bia_list))
        else:
            return StatusInfo.error("El cliente no existe")
    #----------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------


