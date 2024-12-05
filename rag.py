import  pathlib
import  requests

from    docmanager  import DocumentManager
#--------------------------------------------------------------------------------------------------

class TGIRAGPipeline:
    def __init__(self, tgi_server="http://localhost:8080/generate"):
        self._tgi_server    = tgi_server
    #----------------------------------------------------------------------------------------------

    def run(self,   question: str, 
                    doc_mngr: DocumentManager):
        relevant_docs   = doc_mngr.retreive_relevant_chunks(question)
        
        for doc in relevant_docs:
            prompt = f"Contexto: {doc}\n\nPregunta: {question}\n\nRespuesta:"
            print(prompt)
            print("------------------------------------")

            # Enviar solicitud al servidor TGI
            response = requests.post \
            (   
                self._tgi_server,
                json={"inputs": prompt, "parameters": {"max_new_tokens": 50, "temperature": 0.7}},
            )
        
            if response.status_code == 200:
                print(response.json()["generated_text"])
                return response.json()["generated_text"]
            else:
                print(response.text)
                raise Exception(f"Error al generar texto: {response.status_code}, {response.text}")
    #----------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------

