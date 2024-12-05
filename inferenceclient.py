import  pathlib

#from langchain.schema import LLMResult
from langchain.prompts.prompt import PromptTemplate

from    langchain_community.llms.huggingface_text_gen_inference import HuggingFaceTextGenInference
from    langchain_community.embeddings                          import HuggingFaceEmbeddings
from    langchain_community.document_loaders                    import TextLoader, PyPDFLoader, PyPDFDirectoryLoader
from    langchain_community.docstore.in_memory                  import InMemoryDocstore
from    langchain_community.vectorstores                        import FAISS
from    langchain.chains                                        import RetrievalQA
from    langchain.text_splitter                                 import RecursiveCharacterTextSplitter 
from    huggingface_hub                                         import InferenceClient
from    text_generation                                         import client as TGIClient
from    huggingface_hub.inference._generated.types              import QuestionAnsweringOutputElement
#--------------------------------------------------------------------------------------------------

class InferenceModelClient:
    def __init__(self,  llama_host_port = "http://localhost:8080/",
                        db_faiss_path   = pathlib.Path("/home/caminante/Documentos/proyectos/iA/data/faiss2/db_faiss"),
                        model_name      = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
                        api_key         = "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"):
        self._llama_host_port   = llama_host_port
        self._db_faiss_path     = db_faiss_path
        self._model_name        = model_name
        self._api_key           = api_key
        self._client            = InferenceClient(api_key=self._api_key)
        self._db                = FAISS.load_local \
        (
            str(self._db_faiss_path), 
            HuggingFaceEmbeddings(model_name = self._model_name), 
            allow_dangerous_deserialization=True
        )
    #----------------------------------------------------------------------------------------------

    def run_query(self, query):
        embeddings      = HuggingFaceEmbeddings \
        (
            model_name = self._model_name
        )
        
        db = FAISS.load_local \
        (
            str(self._db_faiss_path), 
            embeddings, 
            allow_dangerous_deserialization=True
        )

        llm = HuggingFaceTextGenInference \
        (
            inference_server_url    = self._llama_host_port,
            max_new_tokens          = 256,
            top_k                   = 10,
            top_p                   = 0.9,
            typical_p               = 0.95,
            temperature             = 0.6,
            repetition_penalty      = 1,
            do_sample               = True,
            streaming               = True
        )

        template        = "Use the context to answer the question. {context}. Question: {question}" 
        retriever       = db.as_retriever(search_kwargs={"k": 6})
        qa_chain        = RetrievalQA.from_chain_type \
        (
            llm                 = llm, 
            retriever           = retriever,     
            chain_type_kwargs   =
            {
                "prompt": PromptTemplate \
                (
                    template        = template,
                    input_variables = ["context", "question"],
                ),
            }
        )

        return qa_chain({"query": query})
    #----------------------------------------------------------------------------------------------

    def question_answering(self, question):

        context_chunks  = self._db.similarity_search(question)
        context         = " ".join([doc.page_content for doc in context_chunks])

        response: QuestionAnsweringOutputElement | list[QuestionAnsweringOutputElement]
        response = self._client.question_answering \
        (
           
            question                    = question,
            context                     = context,
            model                       = "meta-llama/Llama-3.1-8B-Instruct",
            align_to_words              = True,
            doc_stride                  = 100,
            handle_impossible_answer    = True,
            max_answer_len              = 128,
            top_k                       = 5
        )

        if not isinstance(response, list):
            response = [ response ]

        for r in response:
            print(r.answer)

        return response
    #----------------------------------------------------------------------------------------------

    def text_generation(self, question):
        context_chunks  = self._db.similarity_search(question)
        context         = " ".join([doc.page_content for doc in context_chunks])

        prompt      = f"Contexto: {context}\n\nPregunta: {question}\n\nRespuesta:"
        response    = self._client.text_generation \
        (
            prompt,
            model           = "meta-llama/Llama-3.1-8B-Instruct",
            max_new_tokens  = 100,
            temperature     = 0.7,
            top_p           = 0.9
        )

        print(response)
        pass
        return response
#--------------------------------------------------------------------------------------------------