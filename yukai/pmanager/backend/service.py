import  pathlib

from    database.database                   import  PacientesDB 
from    difflib                             import  SequenceMatcher
from    models.models                       import  PacienteShort, Paciente
from    pmanager.backend.environment        import  Environment
from    tools.tools                         import  StatusInfo
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

    def __init__(self, env: Environment):
        self._env           = env
        self._pacientes_db  = PacientesDB(env.clientes_dir)
    #----------------------------------------------------------------------------------------------

    def log_info(self, info): self._env.log.info(info)
    #----------------------------------------------------------------------------------------------

    def log_error(self, info): self._env.log.error(info)
    #----------------------------------------------------------------------------------------------

    def log_exception(self, ex): self._env.log.exception(ex)
    #----------------------------------------------------------------------------------------------

    def load_all_consolidated_pacientes(self) -> StatusInfo[list[PacienteShort]]:
        try:
            return StatusInfo.ok(self._pacientes_db.get_all_consolidated_pacientes())
        except Exception as ex:
            self.log_exception(ex)
            return StatusInfo.error("Error al obtener los pacientes")
    #----------------------------------------------------------------------------------------------

    def get_consolidated_paciente(self, paciente_id: str) -> StatusInfo[Paciente]:
        try:
            paciente = self._pacientes_db.get_consolidated_paciente(paciente_id)
            if paciente is None:
                return StatusInfo.error("Paciente no encontrado")
            else:
                return StatusInfo.ok(paciente)
        except Exception as ex:
            self.log_exception(ex)
            return StatusInfo.error("Error al obtener el paciente")
    #----------------------------------------------------------------------------------------------

    def load_all_src_pacientes(self) -> StatusInfo[list[PacienteShort]]:
        try:
            return StatusInfo.ok(self._pacientes_db.get_all_src_pacientes())
        except Exception as ex:
            self.log_exception(ex)
            return StatusInfo.error("Error al obtener los pacientes")
    #----------------------------------------------------------------------------------------------

    def consolidate_pacientes(self, pacientes: list[str]) -> StatusInfo[list[Paciente]]:
        pass
    #----------------------------------------------------------------------------------------------

    def preprocess_paciente(self, paciente_id: str) -> StatusInfo:
        try:
            pass
        except Exception as ex:
            self.log_exception(ex)
            return StatusInfo.error("Error al preprocesar el paciente")
    #----------------------------------------------------------------------------------------------

    def delete_src_pacientes(self, pacientes: list[str]):
        return self.delete_pacientes(pacientes, self.load_all_src_pacientes)
    #----------------------------------------------------------------------------------------------

    def delete_consolidated_pacientes(self, pacientes: list[str]):
        return self.delete_pacientes(pacientes, self.load_all_consolidated_pacientes)
    #----------------------------------------------------------------------------------------------

    def delete_pacientes(self, pacientes: list[str], load_fcn: callable):
        try:
            for p in pacientes:
                try:
                    pathlib.Path(p).unlink(missing_ok=True)
                except Exception as ex:
                    self.log_exception(ex)
            return load_fcn()
        except Exception as ex:
            self.log_exception(ex)
            return StatusInfo.error("Error al preprocesar el paciente")
    #----------------------------------------------------------------------------------------------

    def remove_src_duplicates(self):
        return self.remove_duplicates(self.check_src_duplicates(), self.load_all_src_pacientes)
    #----------------------------------------------------------------------------------------------

    def remove_consolidated_duplicates(self):
        return self.remove_duplicates(self.check_consolidated_duplicates(), self.load_all_consolidated_pacientes)
    #----------------------------------------------------------------------------------------------

    def remove_duplicates(self, status: StatusInfo[list[(Paciente, Paciente)]], load_fcn: callable):
        try:
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
        except Exception as ex:
            self.log_exception(ex)
            return StatusInfo.error("Error al preprocesar el paciente")
    #----------------------------------------------------------------------------------------------

    def check_src_duplicates(self): return self.check_duplicates(self.load_all_src_pacientes())
    #----------------------------------------------------------------------------------------------

    def check_consolidated_duplicates(self): return self.check_duplicates(self.load_all_consolidated_pacientes())
    #----------------------------------------------------------------------------------------------

    def check_duplicates(self, status) -> StatusInfo[list[(Paciente, Paciente)]]:
        try:
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
        except Exception as ex:
            self.log_exception(ex)
            return StatusInfo.error("Error al preprocesar el paciente")
    #----------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------


