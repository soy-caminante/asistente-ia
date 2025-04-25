import  json
import  pathlib

from    logger                              import  Logger
from    models.models                       import  IncommingCliente, IncommingFileInfo, ClienteInfo
from    tools.tools                         import  StatusInfo, try_catch, void_try_catch
#--------------------------------------------------------------------------------------------------

class LoggerHandler:
    log_fcn = None
    @classmethod
    def log_callback(cls, *args):
        cls.log_fcn(*args)
#--------------------------------------------------------------------------------------------------

class IncommingStorage:
    def __init__(self, log: Logger, path: pathlib.Path):
        self._log               = log
        self._in_path           = path / "incomming"
        self._out_path          = path / "processed"
        LoggerHandler.log_fcn   = log.exception

        self._in_path.mkdir(exist_ok=True, parents=True)
        self._out_path.mkdir(exist_ok=True, parents=True)
    #----------------------------------------------------------------------------------------------

    def get_all(self) -> list[IncommingCliente]:
        ret: list[IncommingCliente] = [ ]

        for iter_d in self._in_path.iterdir():
            if iter_d.is_dir():
                id_file     = iter_d / "id.json"
                if not id_file.exists(): continue
                docs: list[IncommingFileInfo] = [ ]
                with open(id_file, "r", encoding="utf-8") as id_f:
                    personal_info    = ClienteInfo(**json.loads(id_f.read()))
                
                for iter_c in iter_d.iterdir():
                    if iter_c.name == "id.json": continue
                    docs.append(IncommingFileInfo.build(iter_c))
                ret.append(IncommingCliente(iter_d, personal_info, docs))
        return ret
    #----------------------------------------------------------------------------------------------

    def get_cliente_info(self, db_id: pathlib.Path) -> IncommingCliente:
        ret: IncommingCliente = None

        if db_id.exists():
            for iter_d in db_id.iterdir():
                if iter_d.is_dir():
                    id_file     = iter_d / "id.json"
                    if not id_file.exists(): continue
                    docs: list[IncommingFileInfo] = [ ]
                    with open(id_file, "r", encoding="utf-8") as id_f:
                        personal_info    = ClienteInfo(**json.loads(id_f.read()))
                    
                    for iter_c in iter_d.iterdir():
                        if iter_c.name == "id.json": continue
                        docs.append(IncommingFileInfo.build(iter_c))
            ret = IncommingCliente(iter_d, personal_info, docs)
        return ret
    #----------------------------------------------------------------------------------------------

    void_try_catch(LoggerHandler.log_callback)
    def remove(self, db_id: pathlib.Path):
        db_id.unlink(missing_ok=True)
    #----------------------------------------------------------------------------------------------

    void_try_catch(LoggerHandler.log_callback)
    def set_as_consolidated(self, db_id: pathlib.Path):
        db_id.replace(self._out_path / db_id.name)
    #----------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------