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
    model_name:                 str
    chat_endpoint:              str
    db_port:                    str
    gpu:                        bool
    db_dir:                     pathlib.Path = None
    db_docker_file:             pathlib.Path = None
    #----------------------------------------------------------------------------------------------

    def __post_init__(self):
        LogFwd.fwd_fcn = self.log.exception
        self.db_dir   = self.runtime / "clients"
        self.db_docker_file = self.runtime / f"docker/docker-compose.yml"
        self.db_dir.mkdir(parents=True, exist_ok=True)

        if "llama" in self.model_name.lower():
            if "8b" in self.model_name.lower():
                self.model_name ="meta-llama/Llama-3.1-8B-Instruct"
            elif "3b" in self.model_name.lower():
                self.model_name ="meta-llama/Meta-Llama-3.2-3B-Instruct"
        elif "mistral" in self.model_name.lower():
            self.model_name = "mistralai/Mistral-7B-Instruct-v0.3"
        else:
            self.log.error("Modelo de IA desconocido")
            raise Exception("Model de IA desconocido")
    #----------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------