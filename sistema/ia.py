#https://github.com/meta-llama/llama-recipes/blob/main/recipes/use_cases/customerservice_chatbots/RAG_chatbot/RAG_Chatbot_Example.ipynb

# Hugging face Token: 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
from    aimanager.docmanager          import  DocumentManager
from    aimanager.inferenceclient     import  InferenceModelClient
#--------------------------------------------------------------------------------------------------

def main():
    doc_mngr    = DocumentManager()
    
    print("Cargando los documentos")
    doc_mngr.load()

    client      = InferenceModelClient()

    if client.is_ready():
        print("Preguntando al modelo")
        client.text_generation("¿Cuándo caduca el seguro del coche?")
    else:
        print("El modelo no está listo")
main()