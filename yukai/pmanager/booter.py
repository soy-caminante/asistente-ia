import  argparse
import  flet                            as ft 
import  pathlib

from    dataclasses                     import  dataclass
from    logger                          import  Logger
from    pmanager.view.app               import  App
from    pmanager.view.environment       import  Environment         as AppEnvironment
from    pmanager.backend.environment    import  Environment         as BackendEnvironment
from    pmanager.view.filedialog        import  set_filesaver_mngr
from    pmanager.view.snackbar          import  set_snackbar_mngr
from    tools.factories                 import  *
from    tools.tools                     import  load_configuration_file
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
    db_port:        str
    gpu:            bool
#--------------------------------------------------------------------------------------------------

def load_args(target_class) -> AppEnvironment | BackendEnvironment:
    parser = argparse.ArgumentParser(description="YUKAI: Herramienta de gestión de clientes")
    parser.add_argument('--system',         help        = 'Sistema',    
                                            required    = True)
    parser.add_argument('--runtime',        help        = 'Directorio de ejecución',
                                            required    = True)
    parser.add_argument('--assets',         help        = 'Directorio de recursos para la web')
    parser.add_argument('--gui',            help        = 'GUI', 
                                            choices     = [ 'web', 'console' ],    
                                            required    = False)
    parser.add_argument('--web-port',       help        = 'Pueto web', 
                                            type        = int,
                                            required    = False)
    parser.add_argument('--model-name',     help        = 'Model de IA', 
                                            type        = str,
                                            required    = False)
    parser.add_argument('--chat-endpoint',  help        = 'Localización del chat', 
                                            type        = str,
                                            required    = False)
    parser.add_argument('--db-endpoint',    help        = 'Localización de la base de datos', 
                                            type        = str,
                                            required    = False)
    parser.add_argument('--gpu',            help        = 'Modo de desarrollo', 
                                            type        = str,
                                            required    = False)
    parser.add_argument('--db-name',        help        = 'Nombre de la base de datos', 
                                            type        = str,
                                            required    = False)
    parser.add_argument('--ia-server',      help        = 'Servidor de IA', 
                                            type        = str,
                                            choices     = [ "huggingface", "openai", "yukai" ],
                                            required    = False)
    parser.add_argument('--run-db-on-start',default     = True, 
                                            required    = False,
                                            action      = argparse.BooleanOptionalAction)
    
    args            = parser.parse_known_args()
    pargs           = vars(args[0])
    runtime         = pathlib.Path(pargs["runtime"])
    
    extra_args      = { "runtime": runtime.parent.parent }
    for action in parser._actions:
        if not action.required:
            if pargs.get(action.dest, None) is not None:
                extra_args[action.dest] = pargs[action.dest]

    env = load_configuration_file(runtime, target_class, extra_args)
    
    return env
#--------------------------------------------------------------------------------------------------

class Booter:
    def __init__(self):
        self._app_env = load_args(AppEnvironment)
    #----------------------------------------------------------------------------------------------
    
    def run(self):
        self._app_env.log.info("YUKAI pmanager running")
        self._app_env.log.info("assets: ", self._app_env.assets)
        
        if self._app_env.gui == "console":    
            ft.app( target      = self.run_app, 
                    assets_dir  = str(self._app_env.assets))
        else:
            ft.app( target      = self.run_app, 
                    assets_dir  = str(self._app_env.assets), 
                    view        = ft.WEB_BROWSER, 
                    port        = self._app_env.web_port)
    #----------------------------------------------------------------------------------------------

    def run_app(self, page: ft.Page):
        set_snackbar_mngr(page)
        set_filesaver_mngr(page)

        back_env = load_args(BackendEnvironment)
        back_env.set_log(self._app_env.log)
        back_env.set_session_id(page.session_id)

        Factories.setup(TextFactory("#54BAAD"), 
                        IconButtonFactory("#54BAAD"),
                        LogoFactory(),
                        ColorPalette("#54BAAD"))

        App(page, self._app_env, back_env)
    #----------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------