import  tiktoken
from    huggingface_hub                                         import InferenceClient
from    huggingface_hub.inference._generated.types              import ChatCompletionOutput
from    openai                                                  import OpenAI
from    ia.prompt                                               import IndexerPrompt, DoctorPrompt
from    transformers                                            import  AutoTokenizer

#--------------------------------------------------------------------------------------------------

class InferenceContext:
    @classmethod
    def split_llama_context(cls, api_key, model, src_text: str, n_tokens:int= 120000):
        tokenizer       = AutoTokenizer.from_pretrained(model, token=api_key)
        tokens          = tokenizer.encode(src_text, add_special_tokens=False)
        tokens_chunks   = [ tokens[i:i + n_tokens] for i in range(0, len(tokens), n_tokens) ]
        text_chunks     = [tokenizer.decode(chunk, skip_special_tokens=True) for chunk in tokens_chunks]
    
        return text_chunks, len(tokens)
    #----------------------------------------------------------------------------------------------

    @classmethod
    def split_openai_context(cls, api_key, model, src_text: str, n_tokens:int= 120000):
        tokenizer       = tiktoken.encoding_for_model(model)
        tokens          = tokenizer.encode(src_text)
        tokens_chunks   = [tokens[i:i + n_tokens] for i in range(0, len(tokens), n_tokens)]
        text_chunks     = [tokenizer.decode(chunk) for chunk in tokens_chunks]
        
        return text_chunks, len(tokens)
    #----------------------------------------------------------------------------------------------

    @classmethod
    def huggingface(cls, api_key):
        obj         = InferenceContext(api_key, cls.split_llama_context)
        obj.client  = InferenceModelClient.huggingface(api_key)
        return obj
    #----------------------------------------------------------------------------------------------

    @classmethod
    def openai(cls, api_key):
        obj         = InferenceContext(api_key, cls.split_openai_context)
        obj.client  = InferenceModelClient.openai(api_key)
        return obj
    #----------------------------------------------------------------------------------------------

    def __init__(self, api_key, split_fcn):
        self._model                         = ""
        self._client: InferenceModelClient  = None
        self._chunks                        = [ ]
        self._full_context                  = ""
        self._split_fcn                     = split_fcn
        self._api_key                       = api_key
    #----------------------------------------------------------------------------------------------

    def calc_tokens(self, context):
        _, tokens = self._split_fcn(self._api_key, self.model, context)
        return tokens
    #----------------------------------------------------------------------------------------------

    def get_chunks(self, context):
        chunks, _ = self._split_fcn(self._api_key, self.model, context)
        return chunks
    #----------------------------------------------------------------------------------------------

    @property
    def model(self): return self._model
    #----------------------------------------------------------------------------------------------

    @property
    def client(self): return self._client
    #----------------------------------------------------------------------------------------------

    @property
    def chunks(self): return self._chunks
    #----------------------------------------------------------------------------------------------

    @property
    def full_context(self): return self._full_context
    #----------------------------------------------------------------------------------------------

    @model.setter
    def model(self, value): self._model = value
    #----------------------------------------------------------------------------------------------

    @client.setter
    def client(self, value): self._client = value
    #----------------------------------------------------------------------------------------------

    @chunks.setter
    def chunks(self, value): self._chunks = value
    #----------------------------------------------------------------------------------------------

    @full_context.setter
    def full_context(self, value): self._full_context = value
    #----------------------------------------------------------------------------------------------

    def update_chunks(self):
        self._chunks   = self._split_fcn \
        (
            self._api_key, 
            self._model, 
            self._full_context,     
            120000
        )
    #----------------------------------------------------------------------------------------------

    def chat_doctor(self, promt: DoctorPrompt):
        return self._client.chat_doctor(promt, self._model)
    #----------------------------------------------------------------------------------------------

    def chat_indexer(self, promt: IndexerPrompt):
        return self._client.chat_indexer(promt, self._model)
    #----------------------------------------------------------------------------------------------

    def reset(self):
        self._chunks    = [ ]
        self._model     = ""
    #----------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------

class InferenceModelClient:
    @staticmethod
    def huggingface(api_key: str):
        return InferenceModelClient(InferenceClient(api_key=api_key))
    #----------------------------------------------------------------------------------------------

    @staticmethod
    def openai(api_key: str):
        return InferenceModelClient(OpenAI(api_key=api_key))
    #----------------------------------------------------------------------------------------------

    def __init__(self, client):
        self._client = client
    #----------------------------------------------------------------------------------------------

    def chat_doctor(self, prompt: DoctorPrompt, model):
        messages = \
        [
            {"role": "system", "content":   prompt.get_system_promt()    },
            {"role": "user", "content":     prompt.get_user_prompt()     }
        ]

        completion: ChatCompletionOutput = self._client.chat.completions.create \
        (
            model       = model, 
            messages    = messages, 
            temperature = 0
        )

        return completion.choices[0].message.content
    #----------------------------------------------------------------------------------------------    

    def chat_indexer(self, prompt: IndexerPrompt, model):
        messages = \
        [
            {"role": "system", "content":   prompt.get_system_promt()    },
            {"role": "user", "content":     prompt.get_user_prompt()     }
        ]

        completion: ChatCompletionOutput = self._client.chat.completions.create \
        (
            model       = model, 
            messages    = messages, 
            temperature = 0
        )

        return completion.choices[0].message.content
    #----------------------------------------------------------------------------------------------    
#--------------------------------------------------------------------------------------------------