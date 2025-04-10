import  argparse
import  pathlib
import  sys

from    dataclasses                     import  dataclass
from    indexer.environment             import  Environment
from    indexer.app                     import  CtrlConsole
from    logger                          import  Logger
#--------------------------------------------------------------------------------------------------

@dataclass
class Args:
    runtime: str
#--------------------------------------------------------------------------------------------------

def load_args() -> Args:
    parser = argparse.ArgumentParser(description="YUKAI: Herramienta de indexación de historiales clínicos")
    parser.add_argument('--system', help    = 'Sistema',    
                                    required= True)
    parser.add_argument('--runtime',    help        = 'Directorio de ejecución',                
                                        required    = True)
    args        = parser.parse_known_args()
    pargs       = vars(args[0])
    cfg_file    = pathlib.Path(pargs["runtime"])

    if not cfg_file.exists():
        print("El fichero de configuración no existe")
        sys.exit(-1)

    (cfg_file / "inbox").mkdir(parents=True, exist_ok=True)
    (cfg_file / "consolidated").mkdir(parents=True, exist_ok=True)
    (cfg_file / "indexes").mkdir(parents=True, exist_ok=True)
    (cfg_file / "logs").mkdir(parents=True, exist_ok=True)

    return Args(cfg_file)
#--------------------------------------------------------------------------------------------------

class Booter:
    def __init__(self):
        self._args  = load_args()
    #----------------------------------------------------------------------------------------------
    
    def run(self):
        logger  = Logger().setup("indexer", self._args.runtime / "logs", True)
        env     = Environment(  logger,
                                self._args.runtime / "income",
                                self._args.runtime / "consolidated",
                                self._args.runtime / "indexes")
        sys.argv    = [sys.argv[0]]
        cmd         = CtrlConsole(env)
        cmd.cmdloop()
    #----------------------------------------------------------------------------------------------
#------------------------------------------lis--------------------------------------------------------