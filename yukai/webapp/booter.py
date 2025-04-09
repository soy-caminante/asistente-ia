import  flet                            as ft 
import  pathlib
import  sys

from    web.environment                 import  Environment

from    logger                          import  Logger
#--------------------------------------------------------------------------------------------------

class Booter:
    def __init__(self):
        pass
    #----------------------------------------------------------------------------------------------
    
    def run(self, cfg_dir: pathlib.Path):
        logger  = Logger().setup("web", cfg_dir / "logs", True)
        env     = Environment(  logger,
                                cfg_dir / "income",
                                cfg_dir / "consolidated",
                                cfg_dir / "indexes")
        sys.argv    = [sys.argv[0]]
        cmd         = CtrlConsole(env)
        cmd.cmdloop()
    #----------------------------------------------------------------------------------------------
#------------------------------------------lis--------------------------------------------------------