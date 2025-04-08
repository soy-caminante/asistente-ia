import  pathlib

from    dataclasses import  dataclass
from    logger      import  Logger
#--------------------------------------------------------------------------------------------------

@dataclass
class Environment:
    logger: Logger
    income_dir: pathlib.Path
    consolidated_dir: pathlib.Path
    indexes_dir: pathlib.Path
#--------------------------------------------------------------------------------------------------
