from    huggingface_hub                                         import InferenceClient
from    huggingface_hub.inference._generated.types              import ChatCompletionOutput
from    openai                                                  import OpenAI
from    .prompt                                                 import Prompt
#--------------------------------------------------------------------------------------------------

class InferenceContext:
    @staticmethod
    def huggingface(api_key):
        obj         = InferenceContext(api_key, Prompt.split_llama_context)
        obj.client  = InferenceModelClient.huggingface(api_key)
        return obj
    #----------------------------------------------------------------------------------------------

    @staticmethod
    def openai(api_key):
        obj         = InferenceContext(api_key, Prompt.split_openai_context)
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

    def chat_doctor(self, promt: Prompt):
        return self._client.chat_doctor(promt, self._model)
    #----------------------------------------------------------------------------------------------

    def chat_indexer(self, promt: Prompt):
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

    def chat_doctor(self, prompt: Prompt, model):
        messages = \
        [
            {"role": "system", "content":   prompt.get_doctor_system_promt()    },
            {"role": "user", "content":     prompt.get_doctor_user_prompt()     }
        ]

        completion: ChatCompletionOutput = self._client.chat.completions.create \
        (
            model       = model, 
            messages    = messages, 
            temperature = 0
        )

        return completion.choices[0].message.content
    #----------------------------------------------------------------------------------------------    

    def chat_indexer(self, prompt: Prompt, model):
        messages = \
        [
            {"role": "system", "content":   prompt.get_indexer_system_promt()    },
            {"role": "user", "content":     prompt.get_indexer_user_prompt()     }
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