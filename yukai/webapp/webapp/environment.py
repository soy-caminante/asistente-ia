from    webapp.backend.service  import  BackendService
from    dataclasses             import  dataclass
from    logger                  import  Logger
#--------------------------------------------------------------------------------------------------

@dataclass
class Environment:
    log:        Logger
    backend:    BackendService
#--------------------------------------------------------------------------------------------------