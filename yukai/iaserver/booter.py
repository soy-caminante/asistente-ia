import  argparse
import  pathlib
import  uvicorn
import  sys

from    ia.client                       import  ModelLoader
from    iaserver.environment            import  Environment
from    iaserver.iaserver               import  IAInferenceServer
from    logger                          import  Logger
from    tools.tools                     import  load_configuration_file
#--------------------------------------------------------------------------------------------------

def load_args() -> Environment:
    parser      = argparse.ArgumentParser(description="YUKAI: Herramienta de gestión de clientes")
    args        = parser.parse_known_args()
    pargs       = vars(args[0])
    runtime     = pathlib.Path(pargs["runtime"])

    env            = load_configuration_file(runtime, Environment)
    runtime        = runtime.parent.parent
    env._runtime   = runtime
    env._log       = Logger().setup("iaserver", runtime / "logs", True)

    (runtime / "logs").mkdir(parents=True, exist_ok=True)

    return env
#--------------------------------------------------------------------------------------------------

class Booter:
    def __init__(self):
        self._env = load_args()
    #----------------------------------------------------------------------------------------------
    
    def run(self):
        
        self._env.log.info("YUKAI: Servidor de inferencia")
        self._env.log.info(sys.argv)

        model_loader        = ModelLoader(self._env.model_name, quantization=self._env.quantization) if self._env.test else None
        inference_server    = IAInferenceServer(model_loader, self._env)
        app                 = inference_server.app
        uvicorn.run(app, host="0.0.0.0", port=self._env.web_port)
    #----------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------