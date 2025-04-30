import  argparse
import  pathlib
import  uvicorn
import  sys

from    dataclasses                     import  dataclass
from    ia.client                       import  ModelLoader
from    iaserver.iaserver               import  IAInferenceServer
from    logger                          import  Logger
#--------------------------------------------------------------------------------------------------

@dataclass
class Args:
    runtime:        str
    log:            Logger
    web_port:       int
    max_requests:   int
    workers_num:    int
    model_name:     str
    quantization:   str
    test:           bool

    def __post_init__(self):

        if "llama" in self.model_name.lower():
            if "8B" in self.model_name.lower():
                self.model_name ="meta-llama/Meta-Llama-3.1-8B-Instruct"
            elif "3B" in self.model_name.lower():
                self.model_name ="meta-llama/Meta-Llama-3.2-3B-Instruct"
        elif "mistral" in self.model_name.lower():
            self.model_name = "mistralai/Mistral-7B-Instruct-v0.3"
        else:
            self.log.error("Modelo de IA desconocido")
            raise Exception("Model de IA desconocido")
#--------------------------------------------------------------------------------------------------

def load_args() -> Args:
    parser = argparse.ArgumentParser(description="YUKAI: Herramienta de gestión de clientes")
    parser.add_argument('--runtime',        help        = 'Directorio de ejecución')
    parser.add_argument('--log',            action      = 'store_false', 
                                            help        = 'Activa el log')
    parser.add_argument('--test',           action      = 'store_true', 
                                            help        = 'Pruebas locales')
    parser.add_argument('--web-port',       help        = 'Pueto web', 
                                            type        = int,
                                            default     = 8081,
                                            required    = False)
    parser.add_argument('--workers-num',    help        = 'Número de clientes concurrentes', 
                                            type        = int,
                                            default     = 6,
                                            required    = False)
    parser.add_argument('--max-requests',   help        = '', 
                                            type        = int,
                                            default     = 3,
                                            required    = False)
    parser.add_argument('--model',          help        = 'Modelo de IA', 
                                            type        = str,
                                            required    = True)
    parser.add_argument('--quantization',    help        = 'Cuantización', 
                                            type        = str,
                                            default     = "4bit",
                                            required    = False)

    args            = parser.parse_known_args()
    pargs           = vars(args[0])
    log             = pargs["log"]
    port            = pargs["web_port"]
    max_requests    = pargs["max_requests"]
    workers_num     = pargs["workers_num"]
    model           = pargs["model"]
    runtime         = pathlib.Path(pargs["runtime"])
    quantization    = pargs["quantization"]
    test            = pargs["test"]

    print(pargs["test"])
    (runtime / "logs").mkdir(parents=True, exist_ok=True)

    return Args(runtime, 
                Logger(log).setup("iaserver", runtime / "logs", True), 
                port,
                max_requests,
                workers_num,
                model,
                quantization,
                test)
#--------------------------------------------------------------------------------------------------

class Booter:
    def __init__(self):
        self._args = load_args()
    #----------------------------------------------------------------------------------------------
    
    def run(self):
        
        self._args.log.info("YUKAI: Servidor de inferencia")
        self._args.log.info(sys.argv)

        model_loader        = ModelLoader(self._args.model_name, quantization=self._args.quantization) if self._args.test else None
        inference_server    = IAInferenceServer(model_loader, 
                                                self._args.log,
                                                self._args.workers_num,
                                                self._args.max_requests)
        app                 = inference_server.app
        uvicorn.run(app, host="0.0.0.0", port=self._args.web_port)
    #----------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------