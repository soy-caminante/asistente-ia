import  argparse
import  flet                            as ft 
import  pathlib

from    dataclasses                     import  dataclass
from    logger                          import  Logger
from    pmanager.backend.environment    import  Environment
from    pmanager.backend.service        import  BackendService
from    pmanager.view.app               import  App
from    tools.tools                     import  get_assets_dir_path
#--------------------------------------------------------------------------------------------------

@dataclass
class Args:
    mode:           str
    runtime:        str
    assets_dir:     str
    log:            Logger
    web_port:       int
#--------------------------------------------------------------------------------------------------

def load_args() -> Args:
    parser = argparse.ArgumentParser(description="YUKAI: Herramienta de gestión de clientes")
    parser.add_argument('--system',     help        = 'Sistema',    
                                        required    = True)
    parser.add_argument('--runtime',    help        = 'Directorio de ejecución')
    parser.add_argument('--assets',     help        = 'Directorio de recursos para la web')
    parser.add_argument('--log',        action      = 'store_true', 
                                        help        = 'Activa el log')
    parser.add_argument('--mode',       help        = 'GUI', 
                                        choices     = [ 'web', 'console' ],    
                                        required    = True)
    parser.add_argument('--web-port',   help        = 'Pueto web', 
                                        type        = int,
                                        default     = 8081,
                                        required    = False)

    args    = parser.parse_known_args()
    pargs   = vars(args[0])
    mode    = pargs["mode"]
    log     = pargs["log"]
    port    = pargs["web_port"]

    if "assets" in pargs.keys() and "runtime" in pargs.keys():
        runtime = pathlib.Path(pargs["runtime"])
        assets  = pargs["assets"]

        if not assets:
            target_path = (pathlib.Path(__file__).parent / "../webapp/static").resolve()
            cwd         = pathlib.Path.cwd()

            if target_path.is_relative_to(cwd):
                assets = str(target_path.relative_to(cwd))
            elif cwd.is_relative_to(target_path):
                assets = str(cwd.relative_to(target_path))
            assets = get_assets_dir_path(assets, True)
    elif "assets" in pargs.keys():
        assets  = pargs["assets"]
        runtime = (pathlib.Path(__file__).parent / "../runtime").resolve()
    elif "runtime" in pargs.keys():
        runtime     = pathlib.Path(pargs["runtime"])
        target_path = (pathlib.Path(__file__).parent / "../webapp/static").resolve()
        cwd         = pathlib.Path.cwd()

        if target_path.is_relative_to(cwd):
            assets = str(target_path.relative_to(cwd))
        elif cwd.is_relative_to(target_path):
            assets = str(cwd.relative_to(target_path))
        else:
            assets = None
        assets = get_assets_dir_path(assets, True)
    else:
        runtime = (pathlib.Path(__file__).parent / "../runtime").resolve()
        assets  = str(pargs["assets"] / "assets")

    (runtime / "logs").mkdir(parents=True, exist_ok=True)

    return Args(mode, runtime, assets, Logger(log).setup("pmanager", runtime / "logs", True), port)
#--------------------------------------------------------------------------------------------------


class Booter:
    def __init__(self):
        self._args                      = load_args()
    #----------------------------------------------------------------------------------------------
    
    def run(self):
        self._backend = BackendService(Environment(self._args.log,
                                                   self._args.runtime))

        self._args.log.info("YUKAI pmanager running")
        self._args.log.info("assets: ", self._args.assets_dir)

        if self._args.mode == "console":    
            ft.app( target      = self.run_app, 
                    assets_dir  = self._args.assets_dir)
        else:
            ft.app( target      = self.run_app, 
                    assets_dir  = str(self._args.assets_dir), 
                    view        = ft.WEB_BROWSER, 
                    port        = self._args.web_port)
    #----------------------------------------------------------------------------------------------

    def run_app(self, page: ft.Page):
        App( page,
                WebEnvironment(self._backend._env.log, self._backend))
    #----------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------