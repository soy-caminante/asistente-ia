import  pathlib

from    database.context                    import  PacienteInfo, FileInfo
from    database.database                   import  PacientesDB 
from    difflib                             import  SequenceMatcher
from    models.models                       import  *
from    pmanager.backend.environment        import  Environment
from    tools.tools                         import  StatusInfo, try_catch
from    tools.viewtools                     import  OverlayCtrlWrapper
#--------------------------------------------------------------------------------------------------

class BackendService:
    def __init__(self, env: Environment, overlay_ctrl: OverlayCtrlWrapper):
        self._env           = env
        self._pacientes_db  = PacientesDB(env.clientes_dir)
        self._overlay_ctrl  = overlay_ctrl
    #----------------------------------------------------------------------------------------------

    def check_db(self) -> StatusInfo[bool]: 
        return self._pacientes_db.get_db_status()
    #----------------------------------------------------------------------------------------------

    def log_info(self, info): self._env.log.info(info)
    #----------------------------------------------------------------------------------------------

    def log_error(self, info): self._env.log.error(info)
    #----------------------------------------------------------------------------------------------

    def log_exception(self, ex): self._env.log.exception(ex)
    #----------------------------------------------------------------------------------------------

    @try_catch(Environment.log_fcn, StatusInfo.error("Error al obtener los pacientes"))
    def load_all_consolidated_pacientes(self) -> StatusInfo[list[PacienteShort]]:
        with self._overlay_ctrl.wait("Cargando pacientes consolidados"):
            return StatusInfo.ok(self._pacientes_db.get_all_consolidated_pacientes())
    #----------------------------------------------------------------------------------------------

    @try_catch(Environment.log_fcn, StatusInfo.error("Error al obtener el paciente"))
    def get_consolidated_paciente(self, paciente_id: str) -> StatusInfo[Paciente]:
        with self._overlay_ctrl.wait("Leyendo el paciente"):
            paciente = self._pacientes_db.get_consolidated_paciente(paciente_id)
            if paciente is None:
                return StatusInfo.error("Paciente no encontrado")
            else:
                return StatusInfo.ok(paciente)
    #----------------------------------------------------------------------------------------------

    @try_catch(Environment.log_fcn, StatusInfo.error("Error al obtener los pacientes"))
    def load_all_src_pacientes(self) -> StatusInfo[list[PacienteShort]]:
        with self._overlay_ctrl.wait("Cargando nuevos pacientes"):
            return StatusInfo.ok(self._pacientes_db.get_all_src_pacientes())
    #----------------------------------------------------------------------------------------------

    def consolidate_pacientes(self, pacientes: list[str]) -> StatusInfo[list[Paciente]]:
        pass
    #----------------------------------------------------------------------------------------------

    @try_catch(Environment.log_fcn, StatusInfo.error("Error al preprocesar el paciente"))
    def preprocess_paciente(self, paciente_id: str) -> StatusInfo:
        pass
    #----------------------------------------------------------------------------------------------

    def delete_src_pacientes(self, pacientes: list[str]):
        return self.delete_pacientes(pacientes, self.load_all_src_pacientes)
    #----------------------------------------------------------------------------------------------

    def delete_consolidated_pacientes(self, pacientes: list[str]):
        return self.delete_pacientes(pacientes, self.load_all_consolidated_pacientes)
    #----------------------------------------------------------------------------------------------

    @try_catch(Environment.log_fcn, StatusInfo.error("Error al eliminar el paciente"))
    def delete_pacientes(self, pacientes: list[str], load_fcn: callable):
        with self._overlay_ctrl.wait("Eliminando pacientes"):
            for p in pacientes:
                try:
                    pathlib.Path(p).unlink(missing_ok=True)
                except Exception as ex:
                    self.log_exception(ex)
            return load_fcn()
    #----------------------------------------------------------------------------------------------

    def remove_src_duplicates(self):
        return self.remove_duplicates(self.check_src_duplicates(), self.load_all_src_pacientes)
    #----------------------------------------------------------------------------------------------

    def remove_consolidated_duplicates(self):
        return self.remove_duplicates(self.check_consolidated_duplicates(), self.load_all_consolidated_pacientes)
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

    def check_src_duplicates(self): return self.check_duplicates(self.load_all_src_pacientes())
    #----------------------------------------------------------------------------------------------

    def check_consolidated_duplicates(self): return self.check_duplicates(self.load_all_consolidated_pacientes())
    #----------------------------------------------------------------------------------------------

    @try_catch(Environment.log_fcn, StatusInfo.error("Error al obtener los duplicados del paciente"))
    def check_duplicates(self, status) -> StatusInfo[list[(Paciente, Paciente)]]:
        with self._overlay_ctrl.wait("Buscando duplicados"):
            status = self.load_all_src_pacientes()

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
    def inspect_src_pacientes(self, db_id: str) -> StatusInfo[list[ExpedienteSrc]]:
        paciente:   PacienteInfo
        files:      dict[str:str]
        paciente, files = self._pacientes_db.load_src_expediente(db_id)

        if paciente is not None:
            docs = [ ]
            for _, info in files.items():
                info: FileInfo
                docs.append(DocumentoSrc(info.name,
                                         info.path,
                                         info.mime,
                                         info.size_str))
                
            expediente = ExpedienteSrc( db_id,
                                        paciente.id,
                                        paciente.id_interno,
                                        paciente.nombre,
                                        paciente.apellidos,
                                        paciente.fecha_nacimiento,
                                        paciente.sexo,
                                        docs)
            return StatusInfo.ok(expediente)
        else:
            return StatusInfo.error("Paciente no encontrado")
    #----------------------------------------------------------------------------------------------

    @try_catch(Environment.log_fcn, StatusInfo.error("Error al obtener la información del paciente"))
    def inspect_consolidated_pacientes(self, db_id: str) -> StatusInfo[list[ExpedienteCon]]:
        context = self._pacientes_db.load_consolidated_expediente(db_id)

        if context is not None:
            docs    = [ ]

            for f, info in context.srcdocs.items():
                info: FileInfo
                if f in context.iadocs.keys():
                    tokens = context.iadocs[f].tokens
                else: 
                    tokens = 0
                docs.append(DocumentoCon(   info.name,
                                            info.path,
                                            info.mime,
                                            info.size_str,
                                            tokens))
            
            for f, info in context.iadocs.items():
                info: FileInfo
                if f not in context.srcdocs.keys():
                    docs.append(DocumentoCon(   info.name,
                                                info.path,
                                                info.mime,
                                                info.size_str,
                                                info.tokens))
                
            expediente = ExpedienteCon( db_id,
                                        context.id,
                                        context.id_interno,
                                        context.nombre,
                                        context.apellidos,
                                        context.fecha_nacimiento,
                                        context.sexo,
                                        docs)
            return StatusInfo.ok(expediente)
        else:
            return StatusInfo.error("Paciente no encontrado")
    #----------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------


