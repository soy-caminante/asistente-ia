import  tiktoken
from    transformers import AutoTokenizer

class Prompt:
    @classmethod
    def split_llama_context(cls, api_key, model, src_text: str, n_tokens: 120000):
        tokenizer       = AutoTokenizer.from_pretrained(model, token=api_key)
        tokens          = tokenizer.encode(src_text, add_special_tokens=False)
        tokens_chunks   = [ tokens[i:i + n_tokens] for i in range(0, len(tokens), n_tokens) ]
        text_chunks     = [tokenizer.decode(chunk, skip_special_tokens=True) for chunk in tokens_chunks]
    
        return text_chunks
    #----------------------------------------------------------------------------------------------

    @classmethod
    def split_openai_context(cls, api_key, model, src_text: str, n_tokens: 120000):
        tokenizer       = tiktoken.encoding_for_model(model)
        tokens          = tokenizer.encode(src_text)
        tokens_chunks   = [tokens[i:i + n_tokens] for i in range(0, len(tokens), n_tokens)]
        text_chunks     = [tokenizer.decode(chunk) for chunk in tokens_chunks]
        
        return text_chunks    
    #----------------------------------------------------------------------------------------------


    def check_no_answer(text:str):
        return text.upper().startswith("NO LO SE")
    #----------------------------------------------------------------------------------------------

    def __init__(self, context: str|None=None, question: str|None=None):
        self._context   = context
        self._question  = question
    #----------------------------------------------------------------------------------------------

    @property
    def question(self): return self._question
    #----------------------------------------------------------------------------------------------

    @property
    def context(self): return self._context
    #----------------------------------------------------------------------------------------------

    @context.setter
    def context(self, value): self._context = value
    #----------------------------------------------------------------------------------------------

    @question.setter
    def question(self, value): self._question = value
    #----------------------------------------------------------------------------------------------

    def get(self, context: str|None = None, question: str|None = None):
        if context:     self._context   = context
        if question:    self._question  = question

        prompt  = f"Contexto: {self._context}\r\n"
        prompt += f"Pregunta: {self._question}\r\n"
        prompt += "Si no hay respuesta o no la conoces dime: No encuentro la respuesta\r\n"
        prompt += "Respuesta:"

        return prompt
    #----------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------