from    __future__              import  annotations
import  pathlib

from    logger                  import  Logger
from    pydantic                import  BaseModel, model_validator
from    typing                  import  Callable, ClassVar, Optional
#--------------------------------------------------------------------------------------------------

class LogFwd:
    fwd_fcn = None
#--------------------------------------------------------------------------------------------------

def dummy_fcn(*args): 
    LogFwd.fwd_fcn(*args)
#--------------------------------------------------------------------------------------------------

class Environment(BaseModel):
    runtime:                pathlib.Path
    assets:                 Optional[pathlib.Path|str] = None
    web_port:               int
    gui:                    str
    
    _log_fcn:               ClassVar[Callable[..., None]] = dummy_fcn
    _log:                   Logger
    #----------------------------------------------------------------------------------------------

    @property
    def log(self):  return self._log
    #----------------------------------------------------------------------------------------------

    @property
    def log_fcn(self): return self._log_fcn
    #----------------------------------------------------------------------------------------------

    class Config:
        extra = "ignore"
    #----------------------------------------------------------------------------------------------

    @model_validator(mode="after")
    def post_init(self) -> Environment:
        (self.runtime / "logs").mkdir(parents=True, exist_ok=True)
        self._log       = Logger().setup("pmanager", self.runtime / "logs", True)
        LogFwd.fwd_fcn  = self._log.exception
        
        if self.assets is None:
            self.assets = self.runtime / "assets/static"
        else:
            self.assets = pathlib.Path(self.assets)
            if not self.assets.is_absolute():
                self.assets = self.runtime / self.assets
        return self
    #----------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------