import  pathlib
import  unicodedata

from    dataclasses                     import  dataclass
from    database.context                import  PacienteContextFactory, CompactEncoder, PacienteContext, ClienteInfo, ExpedienteFileInfo
from    models.models                   import  *
from    tools.tools                     import  StatusInfo
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
        self._consolidated_dir  = base / "consolidated"
        self._src_dir           = base / "income"
        self._files_factory     = PacienteContextFactory()
        self._file_decoder      = CompactEncoder()
    #----------------------------------------------------------------------------------------------

    def get_db_status(self) -> StatusInfo[bool]:
        if not self._consolidated_dir.exists() and not self._src_dir.exists():
            return StatusInfo.error("No existen los directorios de pacientes")
        elif not self._consolidated_dir.exists():
            return StatusInfo.error("No existe el directorio de pacientes consolidados")
        elif not self._src_dir.exists():
            return StatusInfo.error("No existe el directorio de pacientes nuevos")
        return StatusInfo.ok(True)
    #----------------------------------------------------------------------------------------------

    def get_src_file_path(self, paciente:str, id: str): return self._src_dir / f"{paciente}/{id}.txt"
    #----------------------------------------------------------------------------------------------

    def get_consolidated_file_path(self, paciente:str, id: str): return self._consolidated_dir / f"{paciente}/{id}"
    #----------------------------------------------------------------------------------------------

    def check_consolidated_paciente(self, ref_id:str): return ref_id in self._db.root
    #----------------------------------------------------------------------------------------------

    def get_consolidated_paciente(self, ref_id:str) -> Paciente:
        target_dir  = self._consolidated_dir / ref_id
        ret         = None

        if target_dir.exists():
            context = self._files_factory.load_consolidated_paciente(target_dir)
            if context:
                ret                     = Paciente()
                ret.db_id               = str(target_dir)
                ret.nombre              = context.nombre
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

    def get_contexto_paciente(self, ref_id: str) -> PacienteContext:
        return self._files_factory.load_consolidated_paciente(self._consolidated_dir / ref_id)
    #----------------------------------------------------------------------------------------------

    def get_matching_pacientes(self, pattern) -> list[Paciente]:
        def normalize(text):
            return unicodedata.normalize("NFKD", text).encode("ASCII", "ignore").decode("utf-8")

        ret                                     = [ ]
        refs_list: list[PacientesDB.DbIndex]    = [ ]

        if pattern == "": return ret
        
        for obj in self._consolidated_dir.iterdir():
            if not obj.is_dir(): continue

            paciente_info = PacienteContextFactory.get_patient_id(obj)
            if paciente_info:
                paciente            = Paciente()
                paciente.db_id      = str(obj)
                paciente.nombre     = paciente_info.nombre
                paciente.apellidos  = paciente_info.apellidos
                paciente.dni        = paciente_info.dni
                paciente.ref_id     = paciente_info.id_interno

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

    def get_all_consolidated_pacientes(self) -> list[PacienteShort]:
        ret: list[PacienteShort] = [ ]
        
        for obj in self._consolidated_dir.iterdir():
            if not obj.is_dir(): continue

            paciente_info = PacienteContextFactory.get_patient_id(obj)
            if paciente_info:
                paciente = PacienteShort \
                (
                    str(obj),
                    paciente_info.dni,
                    paciente_info.id_interno,
                    paciente_info.nombre,
                    paciente_info.apellidos,
                    paciente_info.fecha_nacimiento,
                    paciente_info.sexo
                )
                ret.append(paciente)
        return ret
    #----------------------------------------------------------------------------------------------

    def get_all_src_pacientes(self) -> list[PacienteShort]:
        ret: list[PacienteShort] = [ ]
        
        for obj in self._src_dir.iterdir():
            if not obj.is_dir(): continue

            paciente_info = PacienteContextFactory.get_patient_id(obj)
            if paciente_info:
                paciente = PacienteShort \
                (
                    str(obj),
                    paciente_info.dni,
                    paciente_info.id_interno,
                    paciente_info.nombre,
                    paciente_info.apellidos,
                    paciente_info.fecha_nacimiento,
                    paciente_info.sexo
                )
                ret.append(paciente)
        return ret
    #----------------------------------------------------------------------------------------------

    def load_src_expediente(self, db_id: str) -> tuple[ClienteInfo, dict[str:ExpedienteFileInfo]]:
        return self._files_factory.load_src_paciente(db_id)
    #----------------------------------------------------------------------------------------------

    def load_consolidated_expediente(self, db_id: str) -> PacienteContext:
        return self._files_factory.load_consolidated_paciente(db_id)
    #----------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------
