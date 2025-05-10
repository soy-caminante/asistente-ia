from    __future__                  import annotations
import  json
import  queue
import  re
import  threading
import  time
import  torch

from    database.database           import  ClientesDocumentStore
from    collections                 import  defaultdict, deque
from    concurrent.futures          import  ThreadPoolExecutor
from    fastapi                     import  FastAPI, HTTPException
from    ia.modelloader              import  ModelLoader
from    ia.iaserver.environment     import  Environment
from    models.iacodec              import  IACodec
from    pydantic                    import  BaseModel
from    typing                      import  List, Union, Literal
from transformers import StoppingCriteria, StoppingCriteriaList


class StopOnStringCriteria(StoppingCriteria):
    def __init__(self, tokenizer, stop_string="<ÑÑÑ>"):
        super().__init__()
        self.tokenizer = tokenizer
        self.stop_string = stop_string
        self.generated_so_far = ""

    def __call__(self, input_ids: torch.LongTensor, scores: torch.FloatTensor, **kwargs) -> bool:
        new_text = self.tokenizer.decode(input_ids[0], skip_special_tokens=True)
        if self.stop_string in new_text:
            return True
        return False
#--------------------------------------------------------------------------------------------------

explanation_str = (
    "Eres un asistente médico que estructura información clínica en las siguientes categorías. "
    "fecha: fecha consignada en el documento. "
    "motivo: motivo de la visita. "
    "síntomas: sintomatología referida por el paciente. "
    "estado físico: estado físico del paciente. "
    "medicación: medicación pautada o referida. "
    "tratamiento: tratamiento recomendado. "
    "recomendaciones: instrucciones dadas al paciente. "
    "ingresos: ingresos hospitalarios. "
    "comentarios: comentarios recogidos en el documento. "
    "diagnósticos: diagnóstico efectuado. "
    "antecedentes familiares: antecedentes familiares. "
    "factores riesgo cardiovascular: factores de riesgo cardiovascular del paciente. "
    "alergias: alergias del paciente. "
    "operaciones: operaciones sufridas por el paciente. "
    "implantes: implantes que tiene el paciente. "
    "otros: cualquier cosa no recogida en los campos anteriores. "
    "keywords: keywords del texto. "
    "tags: tags del texto. "
)

document = (
    "**Consulta 2: Seguimiento a 1 semana**\n\n**INFORME MÉDICO**\n\n"
    "**Paciente:** Luis Ramírez López\n**Fecha de consulta:** 12 de enero de 2024\n"
    "**Motivo de consulta:** Seguimiento tras diagnóstico de cálculos renales.\n\n"
    "### **Evolución:**\nEl paciente refiere disminución del dolor, aunque persisten molestias ocasionales.\n\n"
    "### **Examen Físico:**\n- **Presión arterial:** 138/85 mmHg\n- Dolor leve a la palpación lumbar.\n\n"
    "### **Plan:**\n- Continuar con analgésicos según necesidad.\n- Realizar tomografía abdominal programada.\n\n"
    "**Firma:**\nDr. Mario Sánchez Pérez"
)

question_str = (
    "Retorna la información en un json. "
    "No uses saltos de línea ni formato Markdown. "
    "No incluyas campos que no estén presentes en el documento. "
    "No pongas campos con valor null o similares. "
    "Condensa la información lo máximo posible. "
    "Retorna únicamente el json. Añade al final el marcador <ÑÑÑ>."
)

class StructureEmbeddings:
    OP_NAME = "structure"
    #----------------------------------------------------------------------------------------------

    def __init__(self, model: ModelLoader):
        self._model                 =   model
        self._explanation_str       =   \
        (
            "Eres un asistente médico que estructura información clínica en las siguientes categorías. "
            "fecha: fecha consignada en el documento. "
            "motivo: motivo de la visita. "
            "síntomas: sintomatología referida por el paciente. "
            "estado físico: estado físico del paciente. "
            "medicación: medicación pautada o referida. "
            "tratamiento: tratamiento recomendado. "
            "recomendaciones: instrucciones dadas al paciente. "
            "ingresos: ingresos hospitalarios. "
            "comentarios: comentarios recogidos en el documento. "
            "diagnósticos: diagnóstico efectuado. "
            "antecedentes familiares: antecedentes familiares. "
            "factores riesgo cardiovascular: factores de riesgo cardiovascular del paciente. "
            "alergias: alergias del paciente. "
            "operaciones: operaciones sufridas por el paciente. "
            "implantes: implantes que tiene el paciente. "
            "otros: cualquier cosa no recogida en los campos anteriores. "
            "keywords: keywords del texto. "
            "tags: tags del texto. "
        )
        
        self._question_str =  \
        (
            "Retorna la información en un json. "
            "No uses saltos de línea ni formato Markdown. "
            "No incluyas campos que no estén presentes en el documento. "
            "No pongas campos con valor null o similares. "
            "Condensa la información lo máximo posible. "
            "Retorna únicamente el json. Añade al final el marcador <ÑÑÑ>."
        )
        
        self._explanation_embd      = None
        self._question_embd         = None
    #----------------------------------------------------------------------------------------------

    def embed(self):
        self._explanation_embd   = self._model.embed_prompt_tensor(self._explanation_str).to(self._model.device)
        self._question_embd      = self._model.embed_prompt_tensor(self._question_str).to(self._model.device)
    #----------------------------------------------------------------------------------------------

    def get_embeddings(self, document: str):
        document_embd    = self._model.embed_prompt_tensor(document).to(self._model.device)
        return torch.cat([ self._explanation_embd, document_embd, self._question_embd], dim=1)
    #----------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------

class SummaryEmbeddings:
    OP_NAME     = "summary"
    
    RIESGO          = "riesgo"
    ANTECEDENTES    = "antecedentes"
    ALERGIAS        = "alergias"
    MEDICACION      = "medicacion"
    VISITAS         = "visitas"
    INGRESOS        = "ingresos"

    QUESTIONS   = [ RIESGO,
                    ANTECEDENTES,
                    ALERGIAS,
                    MEDICACION,
                    VISITAS,
                    INGRESOS ]
    #----------------------------------------------------------------------------------------------

    def __init__(self, model: ModelLoader):
        self._model             = model
        self._riesgo_str        = "user:Dame una lista con los factores de riesgo cardiovascular del paciente. Si no puedes saberlo responde NADA."
        self._antecedentes_str  = "user:Dame una lista con los antecedentes familiares del paciente. Si no puedes saberlo responde NADA."
        self._alergias_str      = "user:Dame una lista con las alergias del paciente. Si no puedes saberlo responde NADA."
        self._medicacion_str    = "user:Dame una lista con medicación pautada al paciente. Ordena la lista de más reciente a más antiguo. Si no puedes saberlo responde NADA."
        self._visitas_str       = "user:Dame una lista de los documentos aportados, indicando su fecha y un resumen muy breve de lo que contiene. Si no puedes saberlo responde NADA."
        self._ingresos_str      = "user:Dame una lista con los ingresos hospitalarios del paciente. Ordena la lista de más reciente a más antiguo. Si no puedes saberlo responde NADA."

        self._explanation_embd: torch.Tensor  = None
        self._riesgo_embd: torch.Tensor       = None
        self._antecedentes_embd: torch.Tensor = None
        self._alergias_embd: torch.Tensor     = None
        self._medicacion_embd: torch.Tensor   = None
        self._visitas_embd: torch.Tensor      = None
        self._ingresos_embd: torch.Tensor     = None
    #----------------------------------------------------------------------------------------------

    def set_explanation_emb(self, embd): self._explanation_embd = embd
    #----------------------------------------------------------------------------------------------

    def embed(self):
        self._riesgo_embd       = self._model.embed_prompt_tensor(self._riesgo_str).to(self._model.device)
        self._antecedentes_embd = self._model.embed_prompt_tensor(self._antecedentes_str).to(self._model.device)
        self._alergias_embd     = self._model.embed_prompt_tensor(self._alergias_str).to(self._model.device)
        self._medicacion_embd   = self._model.embed_prompt_tensor(self._medicacion_str).to(self._model.device)
        self._visitas_embd      = self._model.embed_prompt_tensor(self._visitas_str).to(self._model.device)
        self._ingresos_embd     = self._model.embed_prompt_tensor(self._ingresos_str).to(self._model.device)
    #----------------------------------------------------------------------------------------------

    def get_embeddings(self, documents, question):
        question_embd = None
        if question == "riesgo":
            question_embd = self._riesgo_embd
        elif question == "antecedentes":
            question_embd = self._antecedentes_embd
        elif question == "alergias":
            question_embd = self._alergias_embd
        elif question == "medicacion":
            question_embd = self._medicacion_embd
        elif question == "visitas":
            question_embd = self._visitas_embd
        elif question == "ingresos":
            question_embd = self._ingresos_embd

        embeddings = [self._explanation_embd]

        for i, doc in enumerate(documents, start=1):
            ext_doc  = f"Documento {i}<<<{doc}"
            doc_embd = self._model.embed_prompt_tensor(ext_doc).to(self._model.device)  # shape: [1, Nᵢ, D]
            embeddings.append(doc_embd)
        embeddings.append(question_embd)

        # Concatena por el eje de tokens (dim 1)
        return torch.cat(embeddings, dim=1)  # shape: [1, total_seq_len, D]
    #----------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------

class ChatEmbeddings:
    OP_NAME = "chat"
    #----------------------------------------------------------------------------------------------

    def __init__(self, model: ModelLoader):
        self._model             =   model
        self._explanation_embd  = None        
        self._explanation_str   =   \
        (
            "Eres un asistente médico experto en interpretación de historiales clínicos. Responde a las preguntas sobre este historial. "
            "Responde solo sobre el contenido del expediente. No inventes ni interpoles ni supongas nada. "
            "Siempre que sea posible indica la fecha de la información que suministras. "
            "Formatea la respuesta en markdown. No resumas al final. "
            "El historial está estructurado de la siguiente manera: "
            "edad del paciente**sexo del paciente**documento 1**documento 2**...**documento N. "
            "Formato de cada documento: cada campo se codifica como n.valor. Campos múltiples separados por |. Listas separadas por ;.Delimitadores internos reemplazados por ¬.Fin de documento ||. Mapeo:0:nombre documento,1=fecha documento,2=motivo,3=síntomas,4=estado físico,5=medicación,6=tratamiento,7=recomendaciones,8=ingresos,9=comentarios,19=diagnósticos,11=antecedentes familiares,12=factores riesgo cardiovascular,13=alergias,14=operaciones,15=implantes,16=otros. "
            "Documento:"
        )
    #----------------------------------------------------------------------------------------------

    def embed(self):
        if self._model:
            self._explanation_embd   = self._model.embed_prompt_tensor(self._explanation_str).to(self._model.device)
    #----------------------------------------------------------------------------------------------

    def get_embeddings(self, edad, sexo, documents, question):
        embeddings = [ self._explanation_embd ]
        embeddings.append(self._model.embed_prompt_tensor(f"{edad}**{sexo}").to(self._model.device))
        for doc in documents:
            tag_embd = self._model.embed_prompt_tensor("**").to(self._model.device)  # shape: [1, Nᵢ, D]
            embeddings.append(tag_embd)
            embeddings.append(doc)

        # Concatena por el eje de tokens (dim 1)
        return torch.cat(embeddings, dim=1)  # shape: [1, total_seq_len, D]
    #----------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------

class StructureOp(BaseModel):
    type: Literal["structure"]
    document: str
    document_name: str
#--------------------------------------------------------------------------------------------------

class SummaryOp(BaseModel):
    type: Literal["summary"]
    documents: List[str]
    question: str
#--------------------------------------------------------------------------------------------------

class ChatOp(BaseModel):
    type: Literal["chat"]
    documents: List[str]
    question: str
    edad: int
    sexo: str
#--------------------------------------------------------------------------------------------------

ArgsUnion = Union[StructureOp, SummaryOp, ChatOp]
#--------------------------------------------------------------------------------------------------

class EmbeddingRequest(BaseModel):
    client          : str
    request_id      : str
    op              : Literal["structure", "summary", "chat"]
    args            : ArgsUnion
    max_tokens      : int = 2048
    temperature     : float = 0.3
#--------------------------------------------------------------------------------------------------

class IAInferenceServer:
    @staticmethod
    def extract_dictionary(text):
        """
        Intenta extraer un JSON válido desde una cadena, aunque esté escapada o tenga formato Markdown.
        """
        # 1. Eliminar delimitadores Markdown y etiquetas como ```json
        clean_text = re.sub(r'```(?:json)?', '', text, flags=re.IGNORECASE)
        clean_text = clean_text.strip('` \n')

        # 2. Si parece estar escapado (muchos \\n, \\") lo desescapamos
        if '\\n' in clean_text or '\\"' in clean_text:
            # Reemplazos básicos seguros
            clean_text = clean_text.replace('\\\\', '\\')  # primero dobles backslashes
            clean_text = clean_text.replace('\\n', '\n')
            clean_text = clean_text.replace('\\"', '"')

        clean_text = clean_text.strip()
        # 3. Intentar decodificar como JSON
        try:
            return json.loads(clean_text), clean_text
        except json.JSONDecodeError as e:
            raise ValueError(f"No se pudo interpretar el texto como JSON: {e}")
    #----------------------------------------------------------------------------------------------

    def __init__(self, model_loader: ModelLoader, env: Environment):
        env.log.add_excluded_locations(__file__, None)

        env.log.info(f"Servidor de inferencia. Base de datos: {env.db_docker_file}")
        env.log.info(f"Lanzar base de datos de manera automática: {env.run_db_on_start}")
        
        self._env                       = env
        self.app                        = FastAPI()
        self.model_loader               = model_loader
        self.request_queue              = queue.Queue()
        self.executor                   = ThreadPoolExecutor(max_workers=env.workers_num)
        self.user_request_log           = defaultdict(deque)
        self.max_requests_per_minute    = env.max_requests
        self._summary_embeddings        = SummaryEmbeddings(model_loader)
        self._stucture_embeddings       = StructureEmbeddings(model_loader)
        self._chat_embeddings           = ChatEmbeddings(model_loader)
        self._embeddings_ready          = self.generate_embeddings()
        self.iacodec                    = IACodec()
        self._clientes_db               = ClientesDocumentStore(env.log, 
                                                                env.db_docker_file if env.run_db_on_start else None,
                                                                env.db_port,
                                                                env.db_host,
                                                                env.db_user,
                                                                env.db_password,
                                                                env.db_name)
        
        if self.model_loader.tokenizer.pad_token_id is None:
            self.model_loader.tokenizer.pad_token = self.model_loader.tokenizer.eos_token

        self._input_ids = torch.full((1, 1), self.model_loader.tokenizer.pad_token_id).to(self.model_loader.device)

        self._register_routes()
    #----------------------------------------------------------------------------------------------

    def log_info(self, *info):
        self._env.log.info(info)
    #----------------------------------------------------------------------------------------------

    def log_warning(self, *info):
        self._env.log.warning(info)
    #----------------------------------------------------------------------------------------------

    def log_error(self, *info):
        self._env.log.error(info)
    #----------------------------------------------------------------------------------------------

    def log_exception(self, ex):
        self._env.log.exception(ex)
    #----------------------------------------------------------------------------------------------

    def log_client_info(self, client, *info):
        self._env.log.info(f"Cliente {client}:", info)
    #----------------------------------------------------------------------------------------------

    def log_client_warning(self, client, *info):
        self._env.log.warning(f"Cliente {client}:", info)
    #----------------------------------------------------------------------------------------------

    def log_client_error(self, client, *info):
        self._env.log.error(f"Cliente {client}:", info)
    #----------------------------------------------------------------------------------------------

    def log_client_exception(self, client, ex):
        self._env.log.error(f"Cliente {client}: excepción")
        self._env.log.exception(ex)
    #----------------------------------------------------------------------------------------------

    def log_holder_error(self, client, holder, info):
        holder["error"] = info
        self._env.log.error(f"Cliente {client}: {info}")
    #----------------------------------------------------------------------------------------------

    def log_holder_exception(self, client, holder, ex):
        holder["error"] = str(ex)
        self._env.log.error(f"Cliente {client}: excepción")
        self._env.log.exception(ex)
    #----------------------------------------------------------------------------------------------

    def log_holder_response(self, client, holder, info):
        holder["response"] = info
        self._env.log.info(f"Cliente {client}: {info}")
    #----------------------------------------------------------------------------------------------

    def generate_embeddings(self):
        try:
            self._summary_embeddings.embed()
            self._stucture_embeddings.embed()
            self._chat_embeddings.embed()
            self._summary_embeddings.set_explanation_emb(self._chat_embeddings._explanation_embd)
            return True
        except Exception as ex:
            self.log_exception(ex)
            return False
    #----------------------------------------------------------------------------------------------

    def _check_embeddings(self, req: EmbeddingRequest):
        if not self._embeddings_ready or not self.model_loader:
            self.log_client_error(req.client, "El servidor no está correctamente configurado")
            raise HTTPException(status_code=429, detail=f"El servidor no está correctamente configurado")
    #----------------------------------------------------------------------------------------------

    def _check_overload(self, req: EmbeddingRequest):
        now             = time.time()
        window_start    = now - 60  # 60 segundos atrás
        request_times   = self.user_request_log[req.request_id]

        while request_times and request_times[0] < window_start:
            request_times.popleft()

        request_times.append(now)

        if len(request_times) >= self.max_requests_per_minute:
            self.log_client_error(req.client, "Número máximo de peticiones por minuto excedido")
            raise HTTPException(status_code=429, detail=f"Número máximo de peticiones por minuto excedido")
    #----------------------------------------------------------------------------------------------
    
    def _check_db(self):
        if not self._clientes_db.is_mongo_ready():
            raise HTTPException(status_code=429, detail=f"Servidor de base de datos no disponible")
    #----------------------------------------------------------------------------------------------
    
    def run_integrity_checks(self, req):
        self._check_embeddings(req)
        self._check_overload(req)
        self._check_db()
    #----------------------------------------------------------------------------------------------

    def _register_routes(self):
        @self.app.post("/generate")
        def enqueue_request(req: EmbeddingRequest):
            self.log_info(f"Nueva petición {req.client}:{req.request_id}")
            result_holder   = { }

            self.run_integrity_checks(req)
                 
            event = threading.Event()

            def task_1():
                start_time = time.time()

                # 1. Preparar embeddings
                explanation_embd = self.model_loader.embed_prompt_tensor(explanation_str).to(self.model_loader.device)
                document_embd    = self.model_loader.embed_prompt_tensor(document).to(self.model_loader.device)
                question_embd    = self.model_loader.embed_prompt_tensor(question_str).to(self.model_loader.device)

                # 2. Concatenar los embeddings [1, tokens, dim]
                embedding_concat = torch.cat([explanation_embd, document_embd, question_embd], dim=1)

                # 3. Fijar pad_token_id si no lo está
                if self.model_loader.tokenizer.pad_token_id is None:
                    self.model_loader.tokenizer.pad_token = self.model_loader.tokenizer.eos_token

                # 4. Crear input_ids y attention_mask dummy
                # Generación con embeddings necesita input_ids y atención explícita por bug en algunos modelos
                input_ids = torch.full((1, 1), self.model_loader.tokenizer.pad_token_id).to(self.model_loader.device)
                attention_mask = torch.ones(embedding_concat.shape[:-1], dtype=torch.long).to(self.model_loader.device)

                # 5. Generar con parada en (END)
                outputs = self.model_loader.model.generate(
                    inputs_embeds      = embedding_concat,
                    attention_mask     = attention_mask,
                    input_ids          = input_ids,
                    max_new_tokens     = 1024,
                    temperature        = 0.3,
                    do_sample          = True,
                    use_cache          = True,
                    stopping_criteria = StoppingCriteriaList([
        StopOnStringCriteria(self.model_loader.tokenizer, stop_string="<ÑÑÑ>")
    ])
                )

                # 6. Cortar en el marcador explícito
                response = self.model_loader.tokenizer.decode(outputs[0], skip_special_tokens=True).split("(END)")[0].strip()

                # 7. Log
                duration = time.time() - start_time
                self.log_info(f"Respuesta: {duration:.2f}s")
                self.log_info(response)
                raise HTTPException(status_code=402, detail=f"Servidor en pruebas")

            def task():
                def generate(embeddings):
                    # Generación con embeddings necesita input_ids y atención explícita por bug en algunos modelos
                    attention_mask = torch.ones(embeddings.shape[:-1], dtype=torch.long).to(self.model_loader.device)

                    outputs = self.model_loader.model.generate\
                    (
                        inputs_embeds      = embeddings,
                        attention_mask     = attention_mask,
                        input_ids          = self._input_ids,
                        max_new_tokens     = 1024,
                        temperature        = 0.3,
                        do_sample          = True,
                        use_cache          = True,
                        stopping_criteria = StoppingCriteriaList \
                                            ([
                                                StopOnStringCriteria(self.model_loader.tokenizer, stop_string="<ÑÑÑ>")
                                            ])
                    )

                    
                    return self.model_loader.tokenizer.decode(outputs[0], skip_special_tokens=True).split("(END)")[0].strip()

                start_time = time.time()

                try:
                    if req.op == StructureEmbeddings.OP_NAME:
                        st_args: StructureOp = req.args
                        
                        self.log_info(f"Estructurando el documento {st_args.document_name}")

                        embeddings  = self._stucture_embeddings.get_embeddings(question_str)#st_args.document)
                        iadoc       = generate(embeddings)

                        duration = time.time() - start_time
                        self.log_info(f"Respuesta: {duration:.2f}s")

                        self.log_info(f"IADOC disponible {iadoc}")
                        raise HTTPException(status_code=402, detail=f"Servidor en pruebas")
                        # iadoc_dict, iadoc       = IAInferenceServer.extract_dictionary(iadoc)
                        # text                    = self.iacodec.encode(iadoc_dict, st_args.document_name)
                        
                        # self.log_info(f"Calculando el biadoc...")

                        # biadoc, btokens         = self.model_loader.embed_gridfs_prompt(text)

                        # self.log_info(f"...biadoc generado")

                        # result_holder["iadoc"]  = iadoc
                        # result_holder["tokens"] = btokens

                        # self.log_info(f"Guardando el biadoc")

                        # result_holder["biadoc"] = self._clientes_db.add_tmp_biadoc(st_args.document_name, biadoc)

                        # self.log_client_info(req.client, "Generación de BIADOC finalizada")
                        
                    elif req.op == SummaryEmbeddings.OP_NAME:
                        sm_args: SummaryOp  = req.args
                        embeddings          = self._summary_embeddings.get_embeddings(sm_args.documents, sm_args.question)
                        self.log_holder_response(req.client, result_holder, generate(embeddings))
                    else:
                        ch_args: ChatOp = req.args
                        biadocs         = [ ]

                        for doc in ch_args.documents:
                            biadoc = self._clientes_db.get_biadoc_content_by_db_id(doc)
                            if biadoc is not None:
                                tensor = torch.load(biadoc).to(self.model_loader.device)
                                biadoc.append(tensor)

                        embeddings = self._chat_embeddings.get_embeddings(biadocs, ch_args.question)
                        self.log_holder_response(req.client, result_holder, generate(embeddings))

                except Exception as e:
                    self.log_holder_exception(req.client, result_holder, e)
                
                finally:
                    duration = time.time() - start_time
                    self.log_info(f"Cliente: {req.client}:{req.request_id} | Duración: {duration:.2f}s")
                    event.set()

            self.request_queue.put((task, event))
            self.executor.submit(self._process_queue)
            event.wait()
            return result_holder
        #------------------------------------------------------------------------------------------

        @self.app.get("/ping")
        def ping():
            return {"status": "ok"}        
        #------------------------------------------------------------------------------------------
    #----------------------------------------------------------------------------------------------

    def _process_queue(self):
        while not self.request_queue.empty():
            task, event = self.request_queue.get()
            try:
                task()
            except Exception as e:
                self._env.log.exception(e)
    #----------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------

