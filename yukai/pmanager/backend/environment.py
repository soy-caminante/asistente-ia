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
    db_dir:                     pathlib.Path = None
    db_docker_file:             pathlib.Path = None
    #----------------------------------------------------------------------------------------------

    def __post_init__(self):
        LogFwd.fwd_fcn = self.log.exception
        self.db_dir   = self.runtime / "clients"
        self.db_docker_file = self.runtime / f"docker/docker-compose.yml"
        self.db_dir.mkdir(parents=True, exist_ok=True)
    #----------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------