from    web.backend.service     import  BackendService
from    dataclasses             import  dataclass
#--------------------------------------------------------------------------------------------------

@dataclass
class Environment:
    backend: BackendService   = None
    console                   = False
#--------------------------------------------------------------------------------------------------