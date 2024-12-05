from langchain.embeddings       import OpenAIEmbeddings
from langchain.embeddings       import HuggingFaceEmbeddings
from langchain.embeddings.base  import Embeddings
from langchain.vectorstores     import FAISS
from sentence_transformers      import SentenceTransformer
#--------------------------------------------------------------------------------------------------

class FaissIndexer:
    def __init__(self, model_nane="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"):
        self._model_name    = model_nane
        self._vector_store  = None
    #----------------------------------------------------------------------------------------------

    def create_faiss_index(self, documents, embedding_model="openai"):
        embeddings          = HuggingFaceEmbeddings(self._model_name)
        self._vector_store  = FAISS.from_documents(documents, embeddings)
        return self
    #----------------------------------------------------------------------------------------------
    
    def retreive_relevant_chunks(self, question: str, top_k=3):
        return self._vector_store.similarity_search(question, k=top_k)
    #----------------------------------------------------------------------------------------------

    @property
    def vector_store(self): return self._vector_store
    #----------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------