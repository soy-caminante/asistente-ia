import  queue
import  threading
import  time
import  torch

from    collections                 import  defaultdict, deque
from    concurrent.futures          import  ThreadPoolExecutor
from    fastapi                     import  FastAPI, HTTPException
from    ia.client                   import  ModelLoader
from    logger                      import  Logger
from    pydantic                    import  BaseModel
from    transformers                import  AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
#--------------------------------------------------------------------------------------------------

class EmbeddingRequest(BaseModel):
    request_id:         str
    prompt_embeddings:  list
    max_tokens:         int = 128
    temperature:        float = 0.7
#--------------------------------------------------------------------------------------------------

class IAInferenceServer:
    def __init__(self, model_loader: ModelLoader, log: Logger, max_workers=8, max_requests_per_minute=5):
        self.app                        = FastAPI()
        self.model_loader               = model_loader
        self.request_queue              = queue.Queue()
        self.executor                   = ThreadPoolExecutor(max_workers=max_workers)
        self.user_request_log           = defaultdict(deque)
        self.max_requests_per_minute    = max_requests_per_minute
        self._log                       = log
        self._register_routes()
    #----------------------------------------------------------------------------------------------

    def _register_routes(self):
        @self.app.post("/generate")
        def enqueue_request(req: EmbeddingRequest):
            self._log.info(f"Nueva petición {req.request_id}")

            now             = time.time()
            window_start    = now - 60  # 60 segundos atrás
            request_times   = self.user_request_log[req.request_id]
            while request_times and request_times[0] < window_start:
                request_times.popleft()

            if len(request_times) >= self.max_requests_per_minute:
                result_holder["error"] = "Número máximo de peticiones por minuto excedido"
                
            else:
                request_times.append(now)

                result_holder   = { }
                event           = threading.Event()

                def task():
                    start_time = time.time()
                    try:
                        if self.model_loader:
                            embeds  = torch.tensor(req.prompt_embeddings).unsqueeze(0).to(self.model_loader.model.device)
                            outputs = self.model_loader.model.generate( inputs_embeds   = embeds,
                                                                        max_new_tokens  = req.max_tokens,
                                                                        temperature     = req.temperature,
                                                                        do_sample       = True,
                                                                        use_cache       = True)
                            output_text                 = self.model_loader.tokenizer.decode(outputs[0], skip_special_tokens=True)
                            result_holder["response"]   = output_text
                        else:
                            result_holder["response"] = "Servidor funcinando"
                    except Exception as e:
                        result_holder["error"] = str(e)
                    
                    finally:
                        duration                                     = time.time() - start_time
                        self._log.info(f"Cliente: {req.request_id} | Duración: {duration:.2f}s")
                        event.set()

                self.request_queue.put((task, event))
                self.executor.submit(self._process_queue)
                event.wait()
            return result_holder
    #----------------------------------------------------------------------------------------------

    def _process_queue(self):
        while not self.request_queue.empty():
            task, event = self.request_queue.get()
            try:
                task()
            except Exception as e:
                self._log.exception(e)
    #----------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------

