import  httpx
import  os
import  tiktoken
import  torch

from    enum                                                    import  IntEnum
from    huggingface_hub                                         import  InferenceClient
from    huggingface_hub.inference._generated.types              import  ChatCompletionOutput
from    ia.prompt                                               import  IndexerPrompt, DoctorPrompt
from    iaserver.iaserver                                       import  SummaryEmbeddings, StructureEmbeddings, ChatEmbeddings
from    models.models                                           import  ExpedienteSummary, StructuredExpediente
from    openai                                                  import  OpenAI
from    transformers                                            import  AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from    tools.tools                                             import  StatusInfo
from    logger                                                  import  Logger
#--------------------------------------------------------------------------------------------------

# hyperstack api-key: 18d10645-1279-4b5d-9df0-78caab8fd1a7
class Quatization(IntEnum):
    B4      = 0
    FP16    = 1
    FP32    = 2
#--------------------------------------------------------------------------------------------------

class ModelLoader:
    def __init__(self, model_name: str, quantization: Quatization = Quatization.B4):
        self._model_name    = model_name
        self._quantization  = quantization
        self._tokenizer     = AutoTokenizer.from_pretrained(model_name, token=os.getenv("hf_api_key"))
        self._model         = self._load_model()
    #----------------------------------------------------------------------------------------------

    @property
    def model(self):
        return self._model
    #----------------------------------------------------------------------------------------------

    @property
    def tokenizer(self):
        return self._tokenizer
    #----------------------------------------------------------------------------------------------
    
    def _load_model(self):
        if self._quantization == Quatization.B4:
            bnb_config = BitsAndBytesConfig(
                load_in_4bit                = True,
                bnb_4bit_compute_dtype      = torch.float16,
                bnb_4bit_use_double_quant   = True
            )
            model = AutoModelForCausalLM.from_pretrained(
                self._model_name,
                quantization_config = bnb_config,
                device_map          = "auto"
            )
        elif self._quantization == Quatization.FP16:
            model = AutoModelForCausalLM.from_pretrained(
                self._model_name,
                torch_dtype = torch.float16,
                device_map  = "auto"
            )
        elif self._quantization == Quatization.FP32:
            model = AutoModelForCausalLM.from_pretrained(
                self._model_name,
                torch_dtype = torch.float32,
                device_map  = "auto"
            )
        else:
            raise ValueError("Unsupported quantization type")
        model.eval()
        return model
    #----------------------------------------------------------------------------------------------
    
    def embed_gridfs_prompt(self, text):
        embedding_tensor    = self.embed_prompt_tensor(text)
        buffer              = torch.io.BytesIO()
        torch.save(embedding_tensor, buffer)
        buffer.seek(0)
        return buffer, embedding_tensor.shape[1]
    #----------------------------------------------------------------------------------------------

    def embed_prompt_tensor(self, text) -> torch.Tensor:
        inputs = self._tokenizer(text, return_tensors="pt", add_special_tokens=False)
        input_ids = inputs["input_ids"].to(self._model.device)
        with torch.no_grad():
            embeddings = self._model.model.embed_tokens(input_ids)
        return embeddings.unsqueeze(0)  # shape: [1, seq_len, hidden_size]
    #----------------------------------------------------------------------------------------------    
#--------------------------------------------------------------------------------------------------

class InferenceChatClient:
    SUMMARY_EXPLANATION     =   "Eres un asistente médico que estructura información clínica en las siguientes categorías, " \
                                "fecha: fecha consignada en el documento." \
                                "motivo: motivo de la visista." \
                                "síntomas: sintomatología referida por el paciente." + \
                                "esatdo físico: estado físico del paciente." + \
                                "medicación: medicación pautada o referida." + \
                                "tratamiento: tratamiento recomendado." + \
                                "recomendaciones: instrucciones dadas al paciente." + \
                                "ingresos: ingresos hospitalarios." + \
                                "comentarios: comentatios recogidos en el documento."  + \
                                "diagnósticos: diagnóstico efectuado." + \
                                "antecedentes familiares: antecedentes familiares." + \
                                "factores riesgo cardivascular: factores de riesgo cardiovascular del paciente." + \
                                "alergias: alergias del paciente." + \
                                "operaciones: operaciones sufridas por el paciente." + \
                                "implantes: implantes que tiene el paciente." + \
                                "otros: cualquier cosa no recogida en los campos anteriores." + \
                                "keywords: keywords del texto." + \
                                "tags: tags del texto."
    
    SUMMARY_QUESTION        =   "Retorna la información en un json." \
                                "si algún campo no está presente en el documento no lo incluyas en el json." + \
                                "condensa la información lo más posible. se sucinto y conciso." + \
                                "si alguna información no aparece o no se menciona, ni incluyas el campo ni lo indiques." + \
                                "retorna únicamente el json"
            
    CHAT_EXPLANATION        =   "Eres un asistente médico experto en interpretación de historiales clínicos. Responde a las preguntas sobre este historial." \
                                "Responde solo sobre el contenido del expediente. No inventes ni interpoles ni supongas nada."  \
                                "Siempre que sea posible indica la fecha de la información que suministras." \
                                "Formatea la respuesta en markdown. No resumas al final." \
                                "El historial está estructurado de la siguiente manera:" \
                                "edad del paciente**sexo del paciente**documento 1**documento 2**...**documento N" \
                                "Formato de cada documento: cada campo se codifica como n.valor. Campos múltiples separados por |. Listas separadas por ;.Delimitadores internos reemplazados por ¬.Fin de documento ||. Mapeo:0:nombre documento,1=fecha documento,2=motivo,3=síntomas,4=estado físico,5=medicación,6=tratamiento,7=recomendaciones,8=ingresos,9=comentarios,19=diagnósticos,11=antecedentes familiares,12=factores riesgo cardiovascular,13=alergias,14=operaciones,15=implantes,16=otros."
    #----------------------------------------------------------------------------------------------

    def __init__(self,  client: OpenAI | InferenceClient,
                        model_name: str,
                        log:        Logger):
        self._client        = client
        self._model_name    = model_name
        self._log           = log
    #----------------------------------------------------------------------------------------------

    def get_structured_document(self, request_id:str, document: str) -> StatusInfo[str]:
        messages     = \
        [
            {"role": "system", "content": f"{self.SUMMARY_EXPLANATION}: {document}"},
            {"role": "user", "content": self.SUMMARY_QUESTION}
        ]

        try:
            completion: ChatCompletionOutput = self._client.chat.completions.create \
            (
                model       = self._model_name, 
                messages    = messages, 
                temperature = 0
            )
            return StatusInfo.ok(completion.choices[0].message.content)
        except Exception as ex:
            self._log.exception(ex)
            return StatusInfo.error("Error al estructurar el expediente")
    #----------------------------------------------------------------------------------------------

    def get_predefined_info(self, request_id:str, documents: list[str]) -> StatusInfo[ExpedienteSummary]:
        riesgo          = [ None ]
        antecedentes    = [ None ]
        medicacion      = [ None ]
        visitas         = [ None ]
        ingresos        = [ None ]
        alergias        = [ None ]
        queries = \
        [ 
            (   "Dame una lista con los factores de riesgo cardiovascular del paciente. Si no puedes saberlo responde NADA.",
                riesgo),
            (   "Dame una lista con los antecedentes familiares del paciente. Si no puedes saberlo responde NADA.",
                antecedentes),
            (   "Dame una lista con las alergias del paciente. Si no puedes saberlo responde NADA.",
                alergias),
            (   "Dame una lista con medicación pautada al paciente. Ordena la lista de más reciente a más antiguo. Si no puedes saberlo responde NADA.",
                medicacion),
            (   "Dame una lista de los documentos aportados, indicando su fecha y un resumen muy breve de lo que contiene. Si no puedes saberlo responde NADA.",
                visitas),
            (   "Dame una lista con los ingresos hospitalarios del paciente. Ordena la lista de más reciente a más antiguo. Si no puedes saberlo responde NADA.",
                ingresos)
        ]
        
        expediente = ""
        for index, doc in enumerate(documents):
            expediente += f"documento {index}>>>{doc}<<<"

        for query, info in queries:
            question    = query
            messages    = \
            [
                {"role": "system", "content": f"{self.CHAT_EXPLANATION}: {expediente}"},
                {"role": "user", "content": question}
            ]

            try:
                completion: ChatCompletionOutput = self._client.chat.completions.create \
                (
                    model       = self._model_name, 
                    messages    = messages, 
                    temperature = 0
                )

                if completion.choices[0].message.content.lower() != "nada":
                    info[0] = completion.choices[0].message.content                        

            except Exception as ex:
                self._log.exception(ex)
                return StatusInfo.error("Error al analizar el expediente")
            
        return StatusInfo.ok(ExpedienteSummary(antecedentes[0],
                                                 riesgo[0],
                                                 medicacion[0],
                                                 alergias[0],
                                                 ingresos[0],
                                                 visitas[0]))
    #----------------------------------------------------------------------------------------------

    def chat(self, request_id: int, documents:list[str], question: str):
        payload = \
        {
            "request_id":   request_id,
            "op":           "predefined",
            "documents":    documents,   
            "question":     question
        }

        try:
            response = self._client.post(self._end_point, headers={"Content-Type": "application/json"}, json=payload, timeout=300)
            
            if response.status_code == 200:
                data = response.json()
                if "response" in data:
                    return StatusInfo.ok(data["response"])
                return StatusInfo.error(data.get("error", "Respuesta sin contenido"))
            return StatusInfo.error(f"Error HTTP {response.status_code}")
        except Exception as ex:
            self._log.exception(ex)
            return StatusInfo.error("Error al generar desde embeddings")
    #----------------------------------------------------------------------------------------------

    def generate_from_embeddings(self, request_id: str, embeddings: list, max_tokens=128, temperature=0.7) -> StatusInfo[str]:
        return StatusInfo.error("No disponible en este modelo")
    #----------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------

class OpenAiChatClient(InferenceChatClient):
    def __init__(self, api_key, model_name, log):
        super().__init__(OpenAI(api_key=api_key), model_name, log)
    #----------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------

class HuggingFaceChatClient(InferenceChatClient):
    def __init__(self, api_key, model_name, log):
        super().__init__(InferenceClient(api_key=api_key), model_name, log)
    #----------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------

class HttpChatClient:
    def __init__(self, end_point: str, log: Logger):
        self._end_point = f"{end_point}/generate"
        self._client    = httpx.Client()
        self._log       = log
    #----------------------------------------------------------------------------------------------

    def get_structured_document(self, client: str, request_id:str, document: str):
        payload = \
        {
            "client":       client,
            "request_id":   request_id,
            "op":           StructureEmbeddings.OP_NAME,
            "documents":    [ document ],
            "question":     None
        }

        try:
            response = self._client.post(self._end_point, headers={"Content-Type": "application/json"}, json=payload, timeout=300)
            
            if response.status_code == 200:
                data = response.json()
                if "response" in data:
                    return StatusInfo.ok(data["response"])
                return StatusInfo.error(data.get("error", "Respuesta sin contenido"))
            return StatusInfo.error(f"Error HTTP {response.status_code}")
        except Exception as ex:
            self._log.exception(ex)
            return StatusInfo.error("Error al generar desde embeddings")
    #----------------------------------------------------------------------------------------------

    def get_predefined_info(self, client: str, request_id:str, documents: list[list]) -> StatusInfo[ExpedienteSummary]:
        payload = \
        {
            "client":       client,
            "request_id":   request_id,
            "op":           SummaryEmbeddings.OP_NAME,
            "documents":    documents,
            "question":     None   
        }

        try:
            map_info = { }
            
            for question in SummaryEmbeddings.QUESTIONS:
                payload["question"] = question
                response = self._client.post(self._end_point, headers={"Content-Type": "application/json"}, json=payload, timeout=300)
                
                if response.status_code == 200:
                    data = response.json()
                    if "response" in data:
                        map_info[question] = data["response"]
                    return StatusInfo.error(data.get("error", "Respuesta sin contenido"))
                return StatusInfo.error(f"Error HTTP {response.status_code}")
            return StatusInfo.ok(ExpedienteSummary( map_info[SummaryEmbeddings.ANTECEDENTES],
                                                    map_info[SummaryEmbeddings.RIESGO],
                                                    map_info[SummaryEmbeddings.MEDICACION],
                                                    map_info[SummaryEmbeddings.ALERGIAS],
                                                    map_info[SummaryEmbeddings.INGRESOS],
                                                    map_info[SummaryEmbeddings.VISITAS]))            
        except Exception as ex:
            self._log.exception(ex)
            return StatusInfo.error("Error al generar desde embeddings")
    #----------------------------------------------------------------------------------------------

    def chat(self, client: str, request_id: int, documents:list[list], question: str):
        payload = \
        {
            "client":       client,
            "request_id":   request_id,
            "op":           ChatEmbeddings.OP_NAME,
            "question":     question,
            "documents":    documents,
        }

        try:
            response = self._client.post(self._end_point, headers={"Content-Type": "application/json"}, json=payload, timeout=300)
            
            if response.status_code == 200:
                data = response.json()
                if "response" in data:
                    return StatusInfo.ok(data["response"])
                return StatusInfo.error(data.get("error", "Respuesta sin contenido"))
            return StatusInfo.error(f"Error HTTP {response.status_code}")
        except Exception as ex:
            self._log.exception(ex)
            return StatusInfo.error("Error al generar desde embeddings")
    #----------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------
