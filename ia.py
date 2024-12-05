#https://github.com/meta-llama/llama-recipes/blob/main/recipes/use_cases/customerservice_chatbots/RAG_chatbot/RAG_Chatbot_Example.ipynb

# Hugging face Token: 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
from    docmanager  import  DocumentManager, DocumentManager2
from    inferenceclient   import  InferenceModelClient
from    rag         import  TGIRAGPipeline
#--------------------------------------------------------------------------------------------------

def main_1():
    docs_path       =   "/home/caminante/Documentos/proyectos/iA/data/docs/"
    doc_mngr        =   DocumentManager \
                        (
                            index_path  = "/home/caminante/Documentos/proyectos/iA/data/faiss/faiss_index",
                            hash_path   = "/home/caminante/Documentos/proyectos/iA/data/faiss/indexed_docs.pkl"
                        )
    rag_pipeline    =   TGIRAGPipeline()
    question        =   "¿Cuál es el precio del seguro del coche?"
    answer          =   rag_pipeline.run(question, doc_mngr.load(docs_path))

    print(answer)
#--------------------------------------------------------------------------------------------------

def main():
    doc_mngr    = DocumentManager2()
    
    print("Cargando los documentos")
    doc_mngr.load()

    client      = InferenceModelClient()
    
    print("Preguntando al modelo")
    
    #response = client.run_query("¿Quién es el tomador del seguro?")
    #client.question_answering("¿Quién es el tomador del seguro?")
    client.text_generation("¿Cuál es la prima del seguro de coche?")
    print("------ Respuesta del modelo")
main()