import  hashlib
import  pathlib
import  pickle

from    collections                             import defaultdict
from    langchain_community.embeddings          import HuggingFaceEmbeddings
from    langchain_community.document_loaders    import TextLoader, PyPDFLoader, PyPDFDirectoryLoader
from    langchain_community.docstore.in_memory  import InMemoryDocstore
from    langchain_community.vectorstores        import FAISS
from    langchain.text_splitter                 import RecursiveCharacterTextSplitter 
#--------------------------------------------------------------------------------------------------

DEFAULT_DATA_PATH       = pathlib.Path(__file__).parent / "../data"
TOKENIZER_MODEL_NAME    = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
#--------------------------------------------------------------------------------------------------

def get_faiss_db_path(): return  DEFAULT_DATA_PATH / "faiss/db_faiss"
#--------------------------------------------------------------------------------------------------

def get_tokenizer_model(): return TOKENIZER_MODEL_NAME
#--------------------------------------------------------------------------------------------------

def setup_doc_manger_paths(data_path: None|str|pathlib.Path = None, tokenizer_model: None|str=None):
    global  DEFAULT_DATA_PATH
    global  TOKENIZER_MODEL_NAME

    if data_path is not None:
        DEFAULT_DATA_PATH = pathlib.Path(data_path)
    if tokenizer_model is not None:
        TOKENIZER_MODEL_NAME = tokenizer_model
#--------------------------------------------------------------------------------------------------


class DocumentManager:
    def __init__(self):
        
        for k in [  DEFAULT_DATA_PATH / "docs/new", 
                    DEFAULT_DATA_PATH / "docs/consolidated", 
                    DEFAULT_DATA_PATH / "faiss", 
                    DEFAULT_DATA_PATH / "docs/hashes"]:
            
            k.mkdir(parents=True, exist_ok=True)

        self._new_docs_path             = DEFAULT_DATA_PATH / "docs/new"
        self._consolidates_docs_path    = DEFAULT_DATA_PATH / "docs/consolidated"
        self._db_faiss_path             = DEFAULT_DATA_PATH / "faiss/db_faiss"
        self._indexed_docs_path         = DEFAULT_DATA_PATH / "docs/hasesh/indexed_docs.pkl"
        self._tokenizer_model           = TOKENIZER_MODEL_NAME
    #----------------------------------------------------------------------------------------------

    def get_doc_hash(self, doc_path: pathlib.Path):
        hasher = hashlib.md5()
        with open(doc_path, "rb") as f:
            hasher.update(f.read())
        return hasher.hexdigest()
    #----------------------------------------------------------------------------------------------

    def load_indexed_hashes(self):
        if not self._indexed_docs_path.exists():
            return {}
        with open(self._indexed_docs_path, "rb") as f:
            return pickle.load(f)
    #----------------------------------------------------------------------------------------------

    def save_indexed_hashes(self, hashes):
        with open(self._indexed_docs_path, "wb") as f:
            pickle.dump(hashes, f)
    #----------------------------------------------------------------------------------------------

    def load(self):
        if self._db_faiss_path.exists():
            indexed_hashes  = self.load_indexed_hashes()
            pdf_docs        = self._new_docs_path.glob("*.pdf")
            
            for pdf in pdf_docs:
                pdf_hash = self.get_doc_hash(pdf)

                if pdf_hash in indexed_hashes:
                    counter = 0
                    while True:
                        if counter == 0:
                            new_name = self._consolidates_docs_path /pdf.name
                        else:
                            new_name = self._consolidates_docs_path / f"{pdf.stem}- ({counter}){pdf.suffix}"
                        if new_name.exists():
                            counter += 1
                        else:
                            pdf.rename(new_name)
                            break
            
            pdf_docs        = list(self._new_docs_path.glob("*.pdf"))

            if len(pdf_docs) > 0:
                loader          = PyPDFDirectoryLoader(str(self._new_docs_path))
                documents       = loader.load()
                text_splitter   = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=10)
                splits          = text_splitter.split_documents(documents)
                embeddings      = HuggingFaceEmbeddings(model_name=self._tokenizer_model)
                db              = FAISS.load_local \
                (   str(self._db_faiss_path), 
                    embeddings, 
                    allow_dangerous_deserialization=True
                )
                db.add_documents(splits)
                db.save_local(str(self._db_faiss_path))

                for pdf in pdf_docs: pdf.rename(f"{pdf.parent}/../consolidated/{pdf.name}")
        else:
            pdf_docs        = self._new_docs_path.glob("*.pdf")

            if len([pdf_docs]) > 0:
                loader          = PyPDFDirectoryLoader(str(self._new_docs_path))
                documents       = loader.load()
                text_splitter   = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=10)
                splits          = text_splitter.split_documents(documents)
                embeddings      = HuggingFaceEmbeddings(model_name=self._tokenizer_model)
                db              = FAISS.from_documents(splits, embeddings)
                db.save_local(str(self._db_faiss_path))

                for pdf in pdf_docs: pdf.rename(f"{pdf.parent}/../consolidated/{pdf.name}")
    #----------------------------------------------------------------------------------------------

    def retrieve_relevant_pages(self, query, k=5):
        """Recuperar páginas relevantes de FAISS."""
        if not self._db_faiss_path.exists():
            raise ValueError("La base de datos FAISS no existe.")
        
        embeddings  = HuggingFaceEmbeddings(model_name=self._tokenizer_model)
        db          = FAISS.load_local \
        (
            str(self._db_faiss_path), 
            embeddings, 
            allow_dangerous_deserialization=True
        )

        # Realizar la búsqueda
        results = db.similarity_search_with_score(query, k=k)
        
        # Agrupar por páginas
        pages = defaultdict(list)
        for result, score in results:
            page = result.metadata.get("page", "Desconocido")
            pages[page].append(result.page_content)

        # Combinar textos por página
        combined_pages = {
            page: " ".join(fragments) for page, fragments in pages.items()
        }
        
        return combined_pages
    #----------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------

class LocalFAISS:
    def __init__(self):
        self._db_path           = DEFAULT_DATA_PATH / "faiss/db_faiss"
        self._tokenizer_model   = TOKENIZER_MODEL_NAME
        self._db                = None
    #----------------------------------------------------------------------------------------------

    def load_db(self):
        if self._db is None:
            if self._db_path.exists():
                embeddings  = HuggingFaceEmbeddings(model_name=self._tokenizer_model)
                self._db    = FAISS.load_local \
                (
                    str(self._db_path), 
                    embeddings, 
                    allow_dangerous_deserialization=True
                )
        return self
    #----------------------------------------------------------------------------------------------

    def is_ready(self): return self._db is not None
    #----------------------------------------------------------------------------------------------

    def retreive_relevant_pages(self, query, k=5) -> dict[str, str]:
        if self._db is None:
            raise ValueError("La base de datos FAISS no existe.")

        results = self._db.similarity_search_with_score(query, k=k)
        
        # Agrupar por páginas
        pages = defaultdict(list)
        for result, score in results:
            page = result.metadata.get("page", "Desconocido")
            pages[page].append(result.page_content)

        # Combinar textos por página
        combined_pages = \
        {
            page: " ".join(fragments) for page, fragments in pages.items()
        }
        
        return combined_pages
    #----------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------
