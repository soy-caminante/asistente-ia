import  pathlib

from    logger                          import  Logger
from    pydantic                        import  BaseModel, PrivateAttr
#--------------------------------------------------------------------------------------------------

class Environment(BaseModel):
    test                : str
    web_port            : int
    workers_num         : int
    max_requests        : int
    model_name          : str
    quantization        : str
    db_port             : int
    db_docker           : str
    _log                : Logger = PrivateAttr(default=None)
    _runtime            : pathlib.Path = PrivateAttr(default=None)
    #----------------------------------------------------------------------------------------------
    
    @property
    def log(self): return self._log
    #----------------------------------------------------------------------------------------------

    @property
    def runtime(self): return self._runtime
    #----------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------