import  torch
from    ia.modelloader              import ModelLoader
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
        self._riesgo_embd       = self._model.embed_prompt_tensor(self._riesgo_str)
        self._antecedentes_embd = self._model.embed_prompt_tensor(self._antecedentes_str)
        self._alergias_embd     = self._model.embed_prompt_tensor(self._alergias_str)
        self._medicacion_embd   = self._model.embed_prompt_tensor(self._medicacion_str)
        self._visitas_embd      = self._model.embed_prompt_tensor(self._visitas_str)
        self._ingresos_embd     = self._model.embed_prompt_tensor(self._ingresos_str)        
    #----------------------------------------------------------------------------------------------

    def get_embeddings(self, documents, question):
        question_embeddings = None
        if question == "riesgo":
            question_embeddings = self._riesgo_embd
        elif question == "antecedentes":
            question_embeddings = self._antecedentes_embd
        elif question == "alergias":
            question_embeddings = self._alergias_embd
        elif question == "medicacion":
            question_embeddings = self._medicacion_embd
        elif question == "visitas":
            question_embeddings = self._visitas_embd
        elif question == "ingresos":
            question_embeddings = self._ingresos_embd


        device = self._explanation_embd.device
        embeddings = [self._explanation_embd]

        for i, doc in enumerate(documents, start=1):
            tag = f"Documento {i}<<<"
            emb = self._model.embed_prompt_tensor(tag).to(device)  # shape: [1, Nᵢ, D]
            embeddings.append(emb)
            embeddings.append(doc)
        embeddings.append(question_embeddings)

        # Concatena por el eje de tokens (dim 1)
        return torch.cat(embeddings, dim=1)  # shape: [1, total_seq_len, D]
    #----------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------

class StructureEmbeddings:
    OP_NAME = "structure"
    #----------------------------------------------------------------------------------------------

    def __init__(self, model: ModelLoader):
        self._model                 =   model
        self._explanation_str       =   "system:" \
                                        "Eres un asistente médico que estructura información clínica en las siguientes categorías, " \
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
                                        "tags: tags del texto. "
        
        self._question_str          =   "user:Retorna la información en un json." \
                                        "si algún campo no está presente en el documento no lo incluyas en el json." + \
                                        "condensa la información lo más posible. se sucinto y conciso." + \
                                        "si alguna información no aparece o no se menciona, ni incluyas el campo ni lo indiques." + \
                                        "retorna únicamente el json"
        
        self._explanation_embd      = None
        self._question_embd         = None
    #----------------------------------------------------------------------------------------------

    def embed(self):
        _, self._explanation_embd   = self._model.embed_prompt_tensor(self._explanation_str)
        _, self._question_embd      = self._model.embed_prompt_tensor(self._question_str)
    #----------------------------------------------------------------------------------------------

    def get_embeddings(self, document: str):
        device      = self._explanation_embd.device
        embeddings  = [self._explanation_embd]
        embeddings.append(self._model.embed_prompt_tensor(document).to(device))
        embeddings.append(self._question_embd)

        # Concatena por el eje de tokens (dim 1)
        return torch.cat(embeddings, dim=1)  # shape: [1, total_seq_len, D]
    #----------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------

class ChatEmbeddings:
    OP_NAME = "chat"
    #----------------------------------------------------------------------------------------------

    def __init__(self, model: ModelLoader):
        self._model             =   model
        self._explanation_str   =   "system:" \
                                    "Eres un asistente médico experto en interpretación de historiales clínicos. Responde a las preguntas sobre este historial." \
                                    "Responde solo sobre el contenido del expediente. No inventes ni interpoles ni supongas nada."  \
                                    "Siempre que sea posible indica la fecha de la información que suministras." \
                                    "Formatea la respuesta en markdown. No resumas al final." \
                                    "El historial está estructurado de la siguiente manera:" \
                                    "edad del paciente**sexo del paciente**documento 1**documento 2**...**documento N" \
                                    "Formato de cada documento: cada campo se codifica como n.valor. Campos múltiples separados por |. Listas separadas por ;.Delimitadores internos reemplazados por ¬.Fin de documento ||. Mapeo:0:nombre documento,1=fecha documento,2=motivo,3=síntomas,4=estado físico,5=medicación,6=tratamiento,7=recomendaciones,8=ingresos,9=comentarios,19=diagnósticos,11=antecedentes familiares,12=factores riesgo cardiovascular,13=alergias,14=operaciones,15=implantes,16=otros." \
                                    "Documento:"
        self._explanation_embd  = None        
    #----------------------------------------------------------------------------------------------

    def embed(self):
        _, self._explanation_embd   = self._model.embed_prompt_tensor(self._explanation_str)
    #----------------------------------------------------------------------------------------------

    def get_embeddings(self, edad, sexo, documents, question):
        device = self._explanation_embd.device
        embeddings = [self._explanation_embd]
        embeddings.append(self._model.embed_prompt_tensor(f"{edad}**{sexo}").to(device))
        for doc in documents:
            tag = "**"
            emb = self._model.embed_prompt_tensor(tag).to(device)  # shape: [1, Nᵢ, D]
            embeddings.append(emb)
            embeddings.append(doc)

        # Concatena por el eje de tokens (dim 1)
        return torch.cat(embeddings, dim=1)  # shape: [1, total_seq_len, D]
    #----------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------
