import  pathlib

from    database.context                    import  ClienteInfo, ExpedienteFileInfo
from    database.olddatabase                import  PacientesDB 
from    database.database                   import  PacientesDocumentStore
from    database.incomming                  import  IncommingStorage, IncommingFileInfo, IncommingCliente
from    difflib                             import  SequenceMatcher
from    models.models                       import  *
from    pmanager.backend.environment        import  Environment
from    tools.tools                         import  StatusInfo, try_catch
from    tools.viewtools                     import  OverlayCtrlWrapper
#--------------------------------------------------------------------------------------------------

class BackendService:
    def __init__(self, env: Environment, overlay_ctrl: OverlayCtrlWrapper):
        self._env           = env
        self._clientes_db  = PacientesDocumentStore(env.log, env.db_docker_file, env.db_dir)
        self._incomming_db  = IncommingStorage(env.log, env.db_dir)
        self._overlay_ctrl  = overlay_ctrl
    #----------------------------------------------------------------------------------------------

    def check_db(self) -> StatusInfo[bool]: 
        return self._clientes_db.is_mongo_ready()
    #----------------------------------------------------------------------------------------------

    def log_info(self, info): self._env.log.info(info)
    #----------------------------------------------------------------------------------------------

    def log_error(self, info): self._env.log.error(info)
    #----------------------------------------------------------------------------------------------

    def log_exception(self, ex): self._env.log.exception(ex)
    #----------------------------------------------------------------------------------------------

    @try_catch(Environment.log_fcn, StatusInfo.error("Error al obtener los pacientes"))
    def load_all_consolidated_clientes(self) -> StatusInfo[list[PacienteShort]]:
        with self._overlay_ctrl.wait("Cargando pacientes consolidados"):
            return StatusInfo.ok(self._clientes_db.get_all_clientes())
    #----------------------------------------------------------------------------------------------

    @try_catch(Environment.log_fcn, StatusInfo.error("Error al obtener el paciente"))
    def get_consolidated_paciente(self, paciente_id: str) -> StatusInfo[Paciente]:
        with self._overlay_ctrl.wait("Leyendo el paciente"):
            paciente = None
            if paciente is None:
                return StatusInfo.error("Paciente no encontrado")
            else:
                return StatusInfo.ok(paciente)
    #----------------------------------------------------------------------------------------------

    @try_catch(Environment.log_fcn, StatusInfo.error("Error al obtener los pacientes"))
    def load_all_src_clientes(self) -> StatusInfo[list[PacienteShort]]:
        with self._overlay_ctrl.wait("Cargando nuevos pacientes"):
            return StatusInfo.ok(self._incomming_db.get_all())
    #----------------------------------------------------------------------------------------------

    def consolidate_clientes(self, pacientes: list[str]) -> StatusInfo[list[Paciente]]:
        pass
    #----------------------------------------------------------------------------------------------

    @try_catch(Environment.log_fcn, StatusInfo.error("Error al preprocesar el paciente"))
    def preprocess_cliente(self, paciente_id: str) -> StatusInfo:
        pass
    #----------------------------------------------------------------------------------------------

    def delete_src_clientes(self, pacientes: list[str]):
        return self.delete_clientes(pacientes, self.load_all_src_clientes)
    #----------------------------------------------------------------------------------------------

    def delete_consolidated_clientes(self, pacientes: list[str]):
        return self.delete_clientes(pacientes, self.load_all_consolidated_clientes)
    #----------------------------------------------------------------------------------------------

    @try_catch(Environment.log_fcn, StatusInfo.error("Error al eliminar el paciente"))
    def delete_clientes(self, pacientes: list[str], load_fcn: callable):
        with self._overlay_ctrl.wait("Eliminando pacientes"):
            pass
            return load_fcn()
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
    def inspect_src_clientes(self, db_id: pathlib.Path) -> StatusInfo[ExpedienteSrc]:
        cliente = self._incomming_db.get_cliente_info(db_id)
        if cliente:
            return StatusInfo.ok(cliente)
        else:
            return StatusInfo.error("Paciente no encontrado")
    #----------------------------------------------------------------------------------------------

    @try_catch(Environment.log_fcn, StatusInfo.error("Error al obtener la información del paciente"))
    def inspect_consolidated_clientes(self, owner: str) -> StatusInfo[PacienteMetaInformation]:
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

            return StatusInfo.ok(PacienteMetaInformation(cliente, src_list, ia_list, bia_list))
        else:
            return StatusInfo.error("El cliente no existe")
        
    #----------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------


