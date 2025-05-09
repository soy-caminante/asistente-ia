from    __future__              import  annotations
import  pathlib

from    dataclasses             import  dataclass
from    logger                  import  Logger
from    pydantic                import  BaseModel, model_validator
from    typing                  import  Callable, ClassVar
#--------------------------------------------------------------------------------------------------

class LogFwd:
    fwd_fcn = None
#--------------------------------------------------------------------------------------------------

def dummy_fcn(*args): 
    LogFwd.fwd_fcn(*args)
#--------------------------------------------------------------------------------------------------

class Environment(BaseModel):
    runtime:                    pathlib.Path
    model_name:                 str
    chat_endpoint:              str
    db_endpoint:                str
    db_name:                    str
    iaserver:                   str
    run_db_on_start:            bool

    _session_id:                str = ""
    _db_dir:                    pathlib.Path = None
    _db_docker_file:            pathlib.Path = None
    _log_fcn:                   ClassVar[Callable[..., None]] = dummy_fcn
    _log:                       Logger = None
    #----------------------------------------------------------------------------------------------

    @property
    def session_id(self): return self._session_id
    #----------------------------------------------------------------------------------------------

    @property
    def log(self):  return self._log
    #----------------------------------------------------------------------------------------------

    @property
    def log_fcn(self):  return self._log_fcn
    #----------------------------------------------------------------------------------------------

    @property
    def db_dir(self):  return self._db_dir
    #----------------------------------------------------------------------------------------------

    @property
    def db_docker_file(self):  return self._db_docker_file
    #----------------------------------------------------------------------------------------------

    def set_session_id(self, id):
        self._session_id = f"cmanager-{id}"
    #----------------------------------------------------------------------------------------------

    def set_log(self, log: Logger):
        (self.runtime / "logs").mkdir(parents=True, exist_ok=True)
        self._log       = log
        LogFwd.fwd_fcn  = self._log.exception
    #----------------------------------------------------------------------------------------------

    class Config:
        extra = "ignore"
    #----------------------------------------------------------------------------------------------

    @model_validator(mode="after")
    def post_init(self) -> Environment:
        self._db_dir         = self.runtime / "clients"
        self._db_docker_file = self.runtime / f"docker/docker-compose.yml"
        self._db_dir.mkdir(parents=True, exist_ok=True)

        if self.iaserver not in [ "openai", "huggingface", "yukai" ]:
            raise Exception(f"Servidor de IA desconocido {self.iaserver}")

        return self
    #----------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------