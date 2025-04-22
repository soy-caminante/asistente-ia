import  pathlib

from    dataclasses             import  dataclass
from    logger                  import  Logger
from    typing                  import  Callable, ClassVar
#--------------------------------------------------------------------------------------------------

def dummy_fcn(*args): pass
#--------------------------------------------------------------------------------------------------

@dataclass
class Environment:
    log_fcn:                    ClassVar[Callable[..., None]] = dummy_fcn
    log:                        Logger
    #----------------------------------------------------------------------------------------------

    def __post_init__(self):
        Environment.log_fcn = self.log.exception
    #----------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------