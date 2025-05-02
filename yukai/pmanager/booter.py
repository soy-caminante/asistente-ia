import  argparse
import  flet                            as ft 
import  pathlib

from    dataclasses                     import  dataclass
from    logger                          import  Logger
from    pmanager.view.app               import  App
from    pmanager.view.environment       import  Environment         as AppEnvironment
from    pmanager.view.snackbar          import  set_snackbar_mngr
from    tools.factories                 import  *
from    tools.tools                     import  get_assets_dir_path
from    tools.viewtools                 import  Factories, ColorPalette
#--------------------------------------------------------------------------------------------------

@dataclass
class Args:
    mode:           str
    runtime:        str
    assets_dir:     str
    log:            Logger
    web_port:       int
    model:          str
    chat_endpoint:  str
    db_endpoint:    str
    gpu:            bool
#--------------------------------------------------------------------------------------------------

def load_args() -> Args:
    parser = argparse.ArgumentParser(description="YUKAI: Herramienta de gestión de clientes")
    parser.add_argument('--system',         help        = 'Sistema',    
                                            required    = True)
    parser.add_argument('--runtime',        help        = 'Directorio de ejecución')
    parser.add_argument('--assets',         help        = 'Directorio de recursos para la web')
    parser.add_argument('--mode',           help        = 'GUI', 
                                            choices     = [ 'web', 'console' ],    
                                            required    = True)
    parser.add_argument('--web-port',       help        = 'Pueto web', 
                                            type        = int,
                                            default     = 8081,
                                            required    = False)
    parser.add_argument('--model',          help        = 'Model de IA', 
                                            type        = str,
                                            required    = True)
    parser.add_argument('--chat-endpoint',  help        = 'Localización del chat', 
                                            type        = str,
                                            default     = "http://localhost:8081",
                                            required    = True)
    parser.add_argument('--db-endpoint',    help        = 'Localización de la base de datos', 
                                            type        = str,
                                            default     = "mongodb://localhost:27017",
                                            required    = False)
    parser.add_argument('--gpu',            help        = 'Modo de desarrollo', 
                                            type        = str,
                                            default     = "on",
                                            choices     = [ "on", "off" ],
                                            required    = False)

    args            = parser.parse_known_args()
    pargs           = vars(args[0])
    mode            = pargs["mode"]
    port            = pargs["web_port"]
    model           = pargs["model"]
    chat_endpoint   = pargs["chat_endpoint"]
    db_endpoint     = pargs["db_endpoint"]
    gpu             = pargs["gpu"]

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

    return Args(mode, 
                runtime, 
                assets, 
                Logger().setup("pmanager", runtime / "logs", True), 
                port,
                model,
                chat_endpoint,
                db_endpoint,
                gpu=="on")
#--------------------------------------------------------------------------------------------------

class Booter:
    def __init__(self):
        self._args = load_args()
    #----------------------------------------------------------------------------------------------
    
    def run(self):
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
        set_snackbar_mngr(page)

        Factories.setup(TextFactory("#54BAAD"), 
                        IconButtonFactory("#54BAAD"),
                        LogoFactory(),
                        ColorPalette("#54BAAD"))

        App(page, AppEnvironment(   self._args.log, 
                                    self._args.runtime, 
                                    self._args.model,
                                    self._args.chat_endpoint,
                                    self._args.db_endpoint,
                                    self._args.gpu))
    #----------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------