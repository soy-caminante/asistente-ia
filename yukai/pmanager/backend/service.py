import  pathlib
import  shutil

from    database.context                    import  ClienteInfo, ExpedienteFileInfo
from    database.database                   import  ClientesDocumentStore
from    database.incomming                  import  IncommingStorage, IncommingFileInfo, IncommingCliente
from    difflib                             import  SequenceMatcher
from    models.models                       import  *
from    ia.client                           import  ModelLoader, SystemPromts
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
    def __init__(self,  db_operator: DBOperator, model: ModelLoader):
        self._db_op                 = db_operator
        self._model                 = model
        self._summary_explanation   = None
        self._summary_question      = None
        self._chat_explanation      = None
    #----------------------------------------------------------------------------------------------

    def load_pretrained(self):
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
        _, binary = self._model.embed_prompt_binary(text)
        return binary
    #----------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------

class BIaDocGenerator:
    def __init__(self, personal_info: ClienteInfo):
        self._personal_info     = personal_info
        self._docs: list[str]   = []
    #----------------------------------------------------------------------------------------------

    def add(self, doc): self._docs.append(doc)
    #----------------------------------------------------------------------------------------------

    def generate(self):
        ret = f"{self._personal_info.edad}**{self._personal_info.sexo}"
        for doc in self._docs:
            if ret != "":
                ret += "**"
            ret += doc
    #----------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------

class BackendService:
    def __init__(self, env: Environment, overlay_ctrl: OverlayCtrlWrapper):
        self._env           = env
        self._model         = ModelLoader(env.model_name)
        self._clientes_db   = ClientesDocumentStore(env.log, env.db_docker_file)
        self._db_operator   = DBOperator(self._clientes_db)
        self._pretrained    = PretrainedManger(self._db_operator, self._model)
        self._incomming_db  = IncommingStorage(env.log, env.db_dir)
        self._overlay_ctrl  = overlay_ctrl
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

    @try_catch(Environment.log_fcn, StatusInfo.error("Error al cargar los contextos preentrenados"))
    def load_pretrained(self) -> StatusInfo[bool]:
        with self._overlay_ctrl.wait("Cargando contextos preentrenados"):
            self._pretrained.load_pretrained()
            return StatusInfo.ok(True)
    #----------------------------------------------------------------------------------------------

    @try_catch(Environment.log_fcn, StatusInfo.error("Error al obtener los pacientes"))
    def load_all_consolidated_clientes(self) -> StatusInfo[list[ClienteInfo]]:
        with self._overlay_ctrl.wait("Cargando pacientes consolidados"):
            return StatusInfo.ok(self._clientes_db.get_all_clientes())
    #----------------------------------------------------------------------------------------------

    @try_catch(Environment.log_fcn, StatusInfo.error("Error al obtener el paciente"))
    def get_consolidated_cliente(self, paciente_id: str) -> StatusInfo[Paciente]:
        with self._overlay_ctrl.wait("Leyendo el paciente"):
            paciente = None
            if paciente is None:
                return StatusInfo.error("Paciente no encontrado")
            else:
                return StatusInfo.ok(paciente)
    #----------------------------------------------------------------------------------------------

    @try_catch(Environment.log_fcn, StatusInfo.error("Error al obtener los pacientes"))
    def load_all_src_clientes(self) -> StatusInfo[list[IncommingCliente]]:
        with self._overlay_ctrl.wait("Cargando nuevos pacientes"):
            return StatusInfo.ok(self._incomming_db.get_all())
    #----------------------------------------------------------------------------------------------

    @try_catch(Environment.log_fcn, StatusInfo.error("Error al preprocesar el paciente"))
    def preprocess_cliente(self, cliente_id: str) -> StatusInfo:
        pass
    #----------------------------------------------------------------------------------------------

    def consolidate_clientes(self, clientes_db_id: list[str]) -> StatusInfo[list[Paciente]]:
        for db_id in clientes_db_id:
            cliente: IncommingCliente   = self._incomming_db.get_cliente_info(db_id)
            biadoc_gen                  = BIaDocGenerator(cliente.personal_info)
            for doc in cliente.docs:
                if doc.is_plain_text: 
                    iadoc = "" # Obtener el iadoc del modelo de ia
                    biadoc_gen.add(doc)

            biadoc = self._pretrained.generate_embeddings(biadoc_gen.generate())
            self._clientes_db.add_cliente()

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


