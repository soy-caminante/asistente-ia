import  os
import  torch

from    enum                                                    import  IntEnum
from    transformers                                            import  AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
#--------------------------------------------------------------------------------------------------


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
        self._device        = torch.device("cuda" if torch.cuda.is_available() else "cpu")
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
            if not torch.cuda.is_available():
                raise EnvironmentError("La cuantización 4bit requiere GPU. Usa FP32 en entorno local sin GPU.")
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
            if not torch.cuda.is_available():
                raise EnvironmentError("La cuantización FP16 requiere GPU. Usa FP32 en entorno local sin GPU.")
            model = AutoModelForCausalLM.from_pretrained(
                self._model_name,
                torch_dtype = torch.float16,
                device_map  = "auto"
            )
        elif self._quantization == Quatization.FP32:
            model = AutoModelForCausalLM.from_pretrained(
                self._model_name,
                torch_dtype = torch.float32,
                device_map  = {"": self._device}
            )
        else:
            raise ValueError("Tipo de cuantización del modelo de IA no soportado")

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
        inputs      = self._tokenizer(text, return_tensors="pt", add_special_tokens=False)
        input_ids   = inputs["input_ids"].to(self._model.device)
        
        with torch.no_grad():
            embeddings = self._model.model.embed_tokens(input_ids)
        return embeddings.unsqueeze(0)  # shape: [1, seq_len, hidden_size]
    #----------------------------------------------------------------------------------------------    
#--------------------------------------------------------------------------------------------------
