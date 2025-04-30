import  pathlib

from    dataclasses             import  dataclass
from    logger                  import  Logger
from    typing                  import  Callable, ClassVar
#--------------------------------------------------------------------------------------------------

class LogFwd:
    fwd_fcn = None
#--------------------------------------------------------------------------------------------------

def dummy_fcn(*args): 
    LogFwd.fwd_fcn(*args)
#--------------------------------------------------------------------------------------------------

@dataclass
class Environment:
    log_fcn:                    ClassVar[Callable[..., None]] = dummy_fcn
    log:                        Logger
    runtime:                    pathlib.Path
    model:                      str
    #----------------------------------------------------------------------------------------------

    def __post_init__(self):
        LogFwd.fwd_fcn = self.log.exception
    #----------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------