import  pathlib

from    dataclasses             import  dataclass
from    logger                  import  Logger
#--------------------------------------------------------------------------------------------------

@dataclass
class Environment:
    log:            Logger
    clients_dir:    pathlib.Path
#--------------------------------------------------------------------------------------------------