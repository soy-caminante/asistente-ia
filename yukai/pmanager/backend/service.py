import  json
import  pathlib
import  re
import  shutil

from    database.context                    import  ClienteInfo
from    database.database                   import  ClientesDocumentStore
from    database.incomming                  import  IncommingStorage, IncommingCliente
from    difflib                             import  SequenceMatcher
from    models.models                       import  *
from    ia.iaclient.client                  import  HttpChatClient, HuggingFaceChatClient, OpenAiChatClient, HttpStructuredDocument
from    pmanager.backend.environment        import  Environment
from    tools.tools                         import  StatusInfo, try_catch, void_try_catch
from    tools.viewtools                     import  OverlayCtrlWrapper
#--------------------------------------------------------------------------------------------------

class BackendService:
    def __init__(self, env: Environment, overlay_ctrl: OverlayCtrlWrapper):
        self._env           = env
        self._clientes_db   = ClientesDocumentStore(env.log, 
                                                    env.db_docker_file if env.run_db_on_start else None,
                                                    env.db_port,
                                                    env.db_host,
                                                    env.db_user,
                                                    env.db_password,
                                                    env.db_name)
        self._incomming_db  = IncommingStorage(env.log, env.db_dir)
        self._overlay_ctrl  = overlay_ctrl
        self._req_id        = 0
        self._client_id     = "pmanager"

        if env.iaserver == "openai":
            self._chat = OpenAiChatClient(os.getenv("oai_api_key"), "gpt-4o-mini", 
                                          env.model_name,
                                          env.log)
        elif env.iaserver == "huggingface":
            self._chat = HuggingFaceChatClient(os.getenv("hf_api_key"), 
                                               env.model_name, 
                                               env.log)
        else:
            self._chat = HttpChatClient(env.chat_endpoint, env.log)
            
        self._env.log.add_excluded_locations(__file__, None)
    #----------------------------------------------------------------------------------------------

    def get_next_req_id(self):
        self._req_id += 1
        return f"pmanager-{self._req_id}"
    #----------------------------------------------------------------------------------------------

    @try_catch(Environment.log_fcn, StatusInfo.error("Base de datos no disponible"))
    def check_db(self) -> StatusInfo[bool]: 
        if self._clientes_db.is_mongo_ready():
            self._clientes_db.setup_db()
            return StatusInfo.ok()
        return StatusInfo.error("Base de datos no disponible")
        
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

    @try_catch(Environment.log_fcn, StatusInfo.error())
    def check_ia_server(self) -> StatusInfo[list[ClienteInfo]]:
        #return StatusInfo.ok()
        return self._chat.ping()
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

                        status = self._chat.get_structured_document(self._client_id, self.get_next_req_id(), doc.content, doc.name)

                        if status:
                            response: HttpStructuredDocument    = status.get()
                            iadoc                               = response.iadoc
                            biadoc                              = response.biadoc
                            btokens                             = response.tokens

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
                            return self.log_error_and_return(f"Error al estructurar el documento: {status}")

                for doc in cliente.docs:
                    if not doc.is_plain_text:
                        src_docs.append({   "filename":             doc.name,
                                            "content":              doc.content.encode("utf-8"),
                                            "mime":                 doc.mime,
                                            "ts":                   doc.ts })
                
                cliente_info: ClienteInfo = self._clientes_db.get_cliente_by_id_interno(cliente.personal_info.id_interno)
                
                if cliente_info is None:
                    self._overlay_ctrl.update(f"Cliente: {cliente.personal_info.id_interno}\nGenerando información predefinida")
                    status = self._chat.get_summary(self._client_id, self.get_next_req_id(), iadocs)
                    
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
                    status = self._chat.get_summary(self._client_id, self.get_next_req_id(), aux_iadocs)

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
        return self.log_info_and_return("Documento cargado", self._clientes_db.get_biadoc_content_by_db_id(db_id))
    #----------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------


