import  tiktoken
from    transformers import AutoTokenizer
#--------------------------------------------------------------------------------------------------

class CompactEncoder:
    # Mapeo de campos con sus índices
    FIELD_MAP = \
    {
        "documento": 0,
        "edad": 1,
        "sexo": 2,
        "fecha": 3,
        "motivo": 4,
        "síntomas": 5,
        "estado físico": 6,
        "medicación": 7,
        "tratamiento": 8,
        "recomendaciones": 9,
        "ingresos": 10,
        "comentarios": 11,
        "diagnósticos": 12,
        "antecedentes familiares": 13,
        "factores riesgo cardivascular": 14,
        "alergias": 15,
        "operaciones": 16,
        "implantes": 17,
        "otros": 18,
        "keywords": 19,
        "tags": 20
    }
    #----------------------------------------------------------------------------------------------

    # Delimitadores
    FIELD_DELIM = "|"
    LIST_DELIM = ";"
    ESCAPE_CHAR = "¬"
    #----------------------------------------------------------------------------------------------

    def __init__(self):
        pass
    #----------------------------------------------------------------------------------------------

    def _sanitize(self, text):
        if not isinstance(text, str):
            text = str(text)
        return text.replace(self.FIELD_DELIM, self.ESCAPE_CHAR).replace(self.LIST_DELIM, self.ESCAPE_CHAR)
    #----------------------------------------------------------------------------------------------

    def encode(self, data: dict) -> str:
        parts = []
        for field, index in self.FIELD_MAP.items():
            if field in data:
                value = data[field]
                if value is None: continue
                if isinstance(value, list):
                    encoded = self.LIST_DELIM.join(self._sanitize(v) for v in value)
                else:
                    encoded = self._sanitize(value)
                parts.append(f"{index}.{encoded}")
        return self.FIELD_DELIM.join(parts)
    #----------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------

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

    def get_doctor_system_promt(self):
        return  "Eres un asistente médico experto en comprensión de documentos clínicos."
    #----------------------------------------------------------------------------------------------
    
    def get_doctor_user_prompt(self):
        return  "Eres un asistente médico. A continuación tienes una serie de documentos clínicos seguido de una pregunta." + \
                "Formato del documento: cada campo se codifica como n.valor. Campos múltiples separados por |. Listas separadas por ;.Delimitadores internos reemplazados por ¬.Mapeo:0:nombre documento,1=edad,2=sexo,3=fecha documento,4=motivo,5=síntomas,6=estado físico,7=medicación,8=tratamiento,9=recomendaciones,10=ingresos,11=comentarios,12=diagnósticos,13=antecedentes familiares,14=factores riesgo cardiovascular,15=alergias,16=operaciones,17=implantes,18=otros,19=keywords,20=tags\n" + \
                "Debes responder únicamente basándote en el contenido del texto indicando el documento y la fecha. Si no encuentras la información necesaria para responder con seguridad, responde: 'No se encuentra esa información en el documento'" + \
                "Texto clínico:\n" +\
                "<<<" + \
                f"{self._context}" + "\n" + \
                ">>>" + \
                "Pregunta:" + "\n" + \
                f"{self._question}" + "\n" + \
                "Respuesta"    
    #----------------------------------------------------------------------------------------------

    def get_indexer_system_promt(self):
        return  "Eres un asistente médico que estructura información clínica. " + \
                "Analiza el siguiente texto clínico y organiza la información en las siguientes categorías, " + \
                "devolviendo los datos en formato JSON con campos:\n" + \
                "edad: edad del paciente\n" + \
                "sexo: sexo del paciente\n" + \
                "motivo: motivo de la visista\n" + \
                "síntomas: sintomatología referida por el paciente\n" + \
                "esatdo físico: estado físico del paciente\n" + \
                "medicación: medicación pautada o referida\n" + \
                "tratamiento: tratamiento recomendado\n" + \
                "recomendaciones: instrucciones dadas al paciente\n" + \
                "ingresos: ingresos hospitalarios\n" + \
                "comentarios: comentatios recogidos en el documento\n"  + \
                "diagnósticos: diagnóstico efectuado\n" + \
                "antecedentes familiares: antecedentes familiares\n" + \
                "factores riesgo cardivascular: factores de riesgo cardiovascular del paciente\n" + \
                "alergias: alergias del paciente\n" + \
                "operaciones: operaciones sufridas por el paciente\n" + \
                "implantes: implantes que tiene el paciente\n" + \
                "otros: cualquier cosa no recogida en los campos anteriores\n" + \
                "keywords: keywords del texto\n" + \
                "tags: tags del texto\n" + \
                "si algún campo no está presente no lo incluyas\n" + \
                "condensa la información lo más posible. se sucinto y conciso\n" + \
                "retorna únicamente el json"
    #----------------------------------------------------------------------------------------------

    def get_indexer_user_prompt(self):
        return  "Texto clínico\n:" + \
                f"{self._context}" + "\n" + \
                "Devuelve la información estructurada como JSON por categoría."
    #----------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------