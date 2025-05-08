import  argparse
import  pathlib
import  uvicorn
import  sys

from    ia.modelloader                  import  ModelLoader
from    ia.iaserver.environment            import  Environment
from    ia.iaserver.iaserver               import  IAInferenceServer
from    logger                          import  Logger
from    tools.tools                     import  load_configuration_file
#--------------------------------------------------------------------------------------------------

def load_args() -> Environment:
    parser = argparse.ArgumentParser(description="YUKAI: Servidor de IA")
    parser.add_argument('--system',         help        = 'Sistema',    
                                            required    = True)
    parser.add_argument('--runtime',        help        = 'Directorio de ejecución',
                                            required    = True)
    parser.add_argument('--test',           help        = 'Modo de prueba',
                                            type        = bool,
                                            required    = False)
    parser.add_argument('--workers-num',    help        = 'Número de peticiones concurrentes',
                                            type        = int,
                                            required    = False)
    parser.add_argument('--web-port',       help        = 'Puerto del servidor web',
                                            type        = int,
                                            required    = False)
    parser.add_argument('--model-name',     help        = 'Modelo de IA',
                                            type        = str,
                                            required    = False)
    parser.add_argument('--max-requests',   help        = 'Número máximo de peticiones por minuto para un usuario',
                                            type        = int,
                                            required    = False)
    parser.add_argument('--db-port',        help        = 'Puerto de conexión a la base de datos',
                                            type        = int,
                                            required    = False)
    parser.add_argument('--quantization',   help        = 'Cuantización del modelo de IA',
                                            type        = str,
                                            choices     = [ "b4", "fp16", "fp32" ],
                                            required    = False)
    parser.add_argument('--db-name',        help        = 'Nombre de la base de datos', 
                                            type        = str,
                                            required    = False)

    args            = parser.parse_known_args()
    pargs           = vars(args[0])
    runtime         = pathlib.Path(pargs["runtime"])

    extra_args      = { "runtime": runtime.parent.parent }
    for action in parser._actions:
        if not action.required:
            if pargs.get(action.dest, None) is not None:
                extra_args[action.dest] = pargs[action.dest]

    return load_configuration_file(runtime, Environment, extra_args)
#--------------------------------------------------------------------------------------------------

class Booter:
    def __init__(self):
        self._env = load_args()
    #----------------------------------------------------------------------------------------------
    
    def run(self):
        
        self._env.log.info("YUKAI: Servidor de inferencia")
        self._env.log.info(sys.argv)
        try:
            model_loader        = ModelLoader(self._env.model_name, 
                                              self._env.quantization, 
                                              self._env.ia_cache_dir,
                                              self._env.low_cpu_mem_usage)
            inference_server    = IAInferenceServer(model_loader, self._env)
            app                 = inference_server.app
            uvicorn.run(app, host="0.0.0.0", port=self._env.web_port)
        except Exception as ex:
            self._env.log.exception(ex)
    #----------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------