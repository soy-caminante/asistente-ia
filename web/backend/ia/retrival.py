import  os
import  pathlib

from    datasets import load_dataset
from    haystack                                            import Document, Pipeline
from    haystack.components.writers                         import DocumentWriter
from    haystack.components.embedders                       import HuggingFaceAPIDocumentEmbedder, HuggingFaceAPITextEmbedder
from    haystack.components.joiners                         import DocumentJoiner
from    haystack.components.preprocessors.document_splitter import DocumentSplitter
from    haystack.components.rankers                         import TransformersSimilarityRanker
from    haystack.components.retrievers.in_memory            import InMemoryBM25Retriever, InMemoryEmbeddingRetriever
from    haystack.document_stores.in_memory                  import InMemoryDocumentStore
from    haystack.utils                                      import ComponentDevice, Secret
#--------------------------------------------------------------------------------------------------

STORAGE_PATH = (pathlib.Path(__file__).parent / "../../data").resolve()
#--------------------------------------------------------------------------------------------------

class DocumentRetrivalMngr:
    def __init__(self, ref_id, path=STORAGE_PATH, log_fcn=None):
        path = pathlib.Path(path) / f"faiss{ref_id}"
        path.mkdir(parents=True, exist_ok=True)

        self._document_store    = InMemoryDocumentStore()
        self._ref_id    = ref_id
        self._log_fcn   = log_fcn
    #----------------------------------------------------------------------------------------------

    def log(self, info):
        if self._log_fcn is not None: self._log_fcn(info)
    #----------------------------------------------------------------------------------------------

    def index_documents(self, folder_path):
        def pretty_print_results(prediction):
            for doc in prediction["documents"]:
                print(doc.meta["title"], "\t", doc.score)
                print(doc.meta["abstract"])
                print("\n", "\n")

        self.log("Cargando datos")
        docs = [ ]
        for doc in pathlib.Path(folder_path).glob('*.txt'):
            self.log(doc.name)
            with open(doc) as f:
                docs.append(Document(content=f.read(), meta={"title": str(doc.name)})) #, "abstract": doc["content"], "pmid": doc["id"]})

        # dataset = load_dataset("anakin87/medrag-pubmed-chunk", split="train")

        # docs = []
        # for doc in dataset:
        #     docs.append(
        #         Document(content=doc["contents"], meta={"title": doc["title"], "abstract": doc["content"], "pmid": doc["id"]})
        #     )
        document_splitter = DocumentSplitter(split_by="word", split_length=512, split_overlap=32)
        document_embedder = HuggingFaceAPIDocumentEmbedder \
        (
            api_type    = "serverless_inference_api",
            api_params  = {"model": "jinaai/jina-embeddings-v2-base-es", "trust_remote_code": True },#{ "model": "BAAI/bge-small-en-v1.5"},# {"model": "dccuchile/bert-base-spanish-wwm-cased"},
            token       = Secret.from_token(os.getenv('hf_api_key'))        
        )

        document_writer = DocumentWriter(self._document_store)

        indexing_pipeline = Pipeline()
        indexing_pipeline.add_component("document_splitter",    document_splitter)
        indexing_pipeline.add_component("document_embedder",    document_embedder)
        indexing_pipeline.add_component("document_writer",      document_writer)

        indexing_pipeline.connect("document_splitter", "document_embedder")
        indexing_pipeline.connect("document_embedder", "document_writer")

        self.log("Indexando documentos")
        indexing_pipeline.run({"document_splitter": {"documents": docs}})

        self._text_embedder = HuggingFaceAPITextEmbedder \
        (
            api_type    = "serverless_inference_api",
            api_params  = {"model": "jinaai/jina-embeddings-v2-base-es", "trust_remote_code": True }, #{ "model": "BAAI/bge-small-en-v1.5"},# 
            token       = Secret.from_token(os.getenv('hf_api_key'))        
        ) 
        self._embedding_retriever   = InMemoryEmbeddingRetriever(self._document_store)
        self._bm25_retriever        = InMemoryBM25Retriever(self._document_store)

        document_joiner = DocumentJoiner()
        ranker          = TransformersSimilarityRanker \
        (
            model       = "BAAI/bge-reranker-base",
            token       = Secret.from_token(os.getenv('hf_api_key'))
        )

        hybrid_retrieval = Pipeline()
        hybrid_retrieval.add_component("text_embedder",         self._text_embedder)
        hybrid_retrieval.add_component("embedding_retriever",   self._embedding_retriever)
        hybrid_retrieval.add_component("bm25_retriever",        self._bm25_retriever)
        hybrid_retrieval.add_component("document_joiner",       document_joiner)
        hybrid_retrieval.add_component("ranker",                ranker)

        hybrid_retrieval.connect("text_embedder",       "embedding_retriever")
        hybrid_retrieval.connect("bm25_retriever",      "document_joiner")
        hybrid_retrieval.connect("embedding_retriever", "document_joiner")
        hybrid_retrieval.connect("document_joiner",     "ranker")

        query = "Dolencia del paciente"

        self.log("Recuperación híbrida")
        result = hybrid_retrieval.run \
        (
            { "text_embedder": {"text": query}, "bm25_retriever": {"query": query}, "ranker": {"query": query} }
        )

        pretty_print_results(result["ranker"])
    #----------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------


# # ✅ Función para indexar documentos desde una carpeta

# # ✅ Función para hacer preguntas utilizando Chain-of-Thought
# def ask_question_chain_of_thought(question, retriever):
#     # Paso 1: Recuperar documentos relevantes
#     docs = retriever.retrieve(query=question, top_k=5)

#     # Paso 2: Crear resúmenes intermedios para cada documento
#     summaries = []
#     for doc in docs:
#         context = doc.content
#         prompt = f"Por favor, proporciona un resumen detallado del siguiente documento:\n\n{context}\n\nResumen:"
#         response = openai.Completion.create(
#             engine="gpt-4",
#             prompt=prompt,
#             max_tokens=500,
#             n=1,
#             stop=None,
#             temperature=0.5
#         )
#         summaries.append(response["choices"][0]["text"].strip())

#     # Paso 3: Crear un contexto final usando los resúmenes
#     combined_context = "\n".join(summaries)
#     final_prompt = f"Contexto:\n{combined_context}\n\nPregunta: {question}\nRespuesta:"
    
#     # Paso 4: Generar la respuesta final usando ChatGPT
#     final_response = openai.Completion.create(
#         engine="gpt-4",
#         prompt=final_prompt,
#         max_tokens=1000,
#         n=1,
#         stop=None,
#         temperature=0.5
#     )

#     print("Respuesta final:")
#     print(final_response["choices"][0]["text"].strip())

# # ✅ Crear el retriever
# retriever = create_retriever()

# # ✅ Indexar documentos si es necesario
# index_documents("ruta_a_tu_carpeta_de_documentos", retriever)

# # ✅ Hacer una pregunta utilizando Chain-of-Thought
# pregunta = "¿Qué es la inteligencia artificial?"
# ask_question_chain_of_thought(pregunta, retriever)

