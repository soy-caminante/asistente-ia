import  json
import  pathlib

from    logger                              import  Logger
from    models.models                       import  IncommingCliente, IncommingFileInfo, ClienteInfo
from    tools.tools                         import  timestamp_str_to_datetime
#--------------------------------------------------------------------------------------------------

class IncommingStorage:
    def __init__(self, log: Logger, path: pathlib.Path):
        self._log               = log
        self._in_path           = path / "incomming"
        self._out_path          = path / "processed"

        self._in_path.mkdir(exist_ok=True, parents=True)
        self._out_path.mkdir(exist_ok=True, parents=True)
    #----------------------------------------------------------------------------------------------

    def get_all(self) -> list[IncommingCliente]:
        ret: list[IncommingCliente] = [ ]

        for iter_0 in self._in_path.iterdir():
            if iter_0.is_dir():
                id_file     = iter_0 / "id.json"
                if not id_file.exists(): continue
                docs: list[IncommingFileInfo] = [ ]
                with open(id_file, "r", encoding="utf-8") as id_f:
                    personal_info    = ClienteInfo(**json.loads(id_f.read()))
                
                for iter_1 in iter_0.iterdir():
                    if not iter_1.is_dir(): continue
                    for iter_2 in iter_1.iterdir():
                        if not iter_2.is_file(): continue
                        creation_time = timestamp_str_to_datetime(iter_1.name)
                        if not creation_time:
                            self._log.multi_warning("Directorio de entrada sin timestamp", iter_2)
                            continue

                        docs.append(IncommingFileInfo.build(iter_2, creation_time))
                ret.append(IncommingCliente(iter_0, personal_info, docs))
        return ret
    #----------------------------------------------------------------------------------------------

    def get_cliente_info(self, db_id: pathlib.Path) -> IncommingCliente:
        ret: IncommingCliente = None

        id_file                         = db_id / "id.json"
        docs: list[IncommingFileInfo]   = [ ]
        if id_file.exists():
            with open(id_file, "r", encoding="utf-8") as id_f:
                personal_info    = ClienteInfo(**json.loads(id_f.read()))

            for iter_0 in db_id.iterdir():
                if not iter_0.is_dir(): continue
                creation_time = timestamp_str_to_datetime(iter_0.name)
                if not creation_time:
                    self._log.multi_warning("Directorio sin timestamp", iter_0)
                    continue
                for iter_1 in iter_0.iterdir():
                    if not iter_1.is_file(): continue
                    docs.append(IncommingFileInfo.build(iter_1, creation_time))
            ret = IncommingCliente(db_id, personal_info, docs)
        return ret
    #----------------------------------------------------------------------------------------------

    def remove(self, db_id: pathlib.Path):
        db_id.unlink(missing_ok=True)
    #----------------------------------------------------------------------------------------------

    def set_as_consolidated(self, db_id: pathlib.Path):
        db_id.replace(self._out_path / db_id.name)
    #----------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------