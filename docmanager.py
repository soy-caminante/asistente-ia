import  faiss
import  hashlib
import  pathlib
import  pickle

from    langchain_community.embeddings          import HuggingFaceEmbeddings
from    langchain_community.document_loaders    import TextLoader, PyPDFLoader, PyPDFDirectoryLoader
from    langchain_community.docstore.in_memory  import InMemoryDocstore
from    langchain_community.vectorstores        import FAISS
from    langchain.text_splitter                 import RecursiveCharacterTextSplitter 
#--------------------------------------------------------------------------------------------------

class DocumentManager:
    def __init__(self,  model       = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
                        index_path  = "faiss_index", 
                        hash_path   = "indexed_docs.pkl"):
        self._documents     = [ ]
        self._vector_store  = None
        self._index_path    = pathlib.Path(index_path)
        self._hash_path     = pathlib.Path(hash_path)
        self._model_name    = model
    #----------------------------------------------------------------------------------------------

    @staticmethod
    def get_doc_has(doc_path: pathlib.Path):
        hasher = hashlib.md5()
        with open(doc_path, "rb") as f:
            hasher.update(f.read())
        return hasher.hexdigest()
    #----------------------------------------------------------------------------------------------
    
    def load(self, docs_path: pathlib.Path | list[pathlib.Path]):
        def load_indexed_hashes():
            if not self._hash_path.exists():
                return {}
            with open(self._hash_path, "rb") as f:
                return pickle.load(f)

        def save_indexed_hashes(hashes):
            with open(self._hash_path, "wb") as f:
                pickle.dump(hashes, f)

        def load_faiss_index():
            if self._index_path.exists():
                # Leer índice FAISS
                index           = faiss.read_index(str(self._index_path))
                docstore_path   = str(self._index_path) + ".docstore.pkl"
                if pathlib.Path(docstore_path).exists():
                    with open(docstore_path, "rb") as f:
                        docstore = pickle.load(f)
                else:
                    docstore = InMemoryDocstore({})

                # Construir el index_to_docstore_id
                index_to_docstore_id = { k: k for k in docstore._dict.keys() }

                # Reconstruir index_to_docstore_id basado en las claves del docstore
                index_to_docstore_id = {i: doc_id for i, doc_id in enumerate(docstore._dict.keys())}
                
                # Verificar tamaño del índice
                if index.ntotal != len(index_to_docstore_id):
                    print(f"Advertencia: El índice tiene {index.ntotal} entradas, pero index_to_docstore_id tiene {len(index_to_docstore_id)} claves.")
                    # Reconstruir FAISS con los datos actuales
                    faiss.reset()

                return FAISS \
                (
                    embedding_function  = HuggingFaceEmbeddings(model_name=self._model_name),
                    index               = index,
                    docstore            = docstore,
                    index_to_docstore_id= index_to_docstore_id
                )            
            else:
                return None
            
        def save_faiss_index():
            # Guardar índice FAISS
            faiss.write_index(self._vector_store.index, str(self._index_path))
            docstore_path = str(self._index_path) + ".docstore.pkl"
            with open(docstore_path, "wb") as f:
                pickle.dump(self._vector_store.docstore, f)  

        new_docs            = [ ]
        indexed_hashes      = load_indexed_hashes()
        self._vector_store  = load_faiss_index()
        
        if self._vector_store is None:
            index               = faiss.IndexFlatL2(384)  # Dimensiones del modelo de embeddings
            docstore            = InMemoryDocstore({})
            self._vector_store  = FAISS \
            (
                embedding_function=HuggingFaceEmbeddings(model_name=self._model_name),
                index=index,
                docstore=docstore,
                index_to_docstore_id={}
            )
            
        if not isinstance(docs_path, list):
            docs_path = [ docs_path ]

        for src_path in docs_path:
            txt_docs    = list(pathlib.Path(src_path).glob("*.txt"))
            pdf_docs    = list(pathlib.Path(src_path).glob("*.pdf"))
            docs        = txt_docs + pdf_docs

            for path in docs:
                doc_hash = self.get_doc_has(path)

                if not doc_hash in indexed_hashes:
                    if path.suffix == ".txt":
                        loader  = TextLoader(str(path))
                    elif path.suffix == ".pdf":
                        loader = PyPDFLoader(str(path))
                    else:
                        raise Exception(f"Documento con extensión no soportada {path.suffix}")

                    new_docs.extend(loader.load_and_split())
                    indexed_hashes[doc_hash] = str(path)

        if new_docs:
            self._vector_store.add_documents(new_docs)

        save_indexed_hashes(indexed_hashes)
        save_faiss_index()

        return self
    #----------------------------------------------------------------------------------------------
    
    def retreive_relevant_chunks(self, question: str, top_k=3):
        return self._vector_store.similarity_search(question, k=top_k)
    #----------------------------------------------------------------------------------------------

    @property
    def documents(self): return self._documents    
    #----------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------

class DocumentManager2:
    def __init__(self,  new_docs            = pathlib.Path("/home/caminante/Documentos/proyectos/iA/data/docs2/new"),
                        consolidated_docs   = pathlib.Path("/home/caminante/Documentos/proyectos/iA/data/docs2/consolidated"),
                        db_faiss_path       = pathlib.Path("/home/caminante/Documentos/proyectos/iA/data/faiss2/db_faiss"),
                        indexed_docs_path   = pathlib.Path("/home/caminante/Documentos/proyectos/iA/data/docs/hasesh/indexed_docs.pkl"),
                        model_name          = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"):
        self._new_docs_path             = new_docs
        self._consolidates_docs_path    = consolidated_docs
        self._db_faiss_path             = db_faiss_path
        self._indexed_docs_path         = indexed_docs_path
        self._model_name                = model_name
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
                            new_name = pathlib.Path(f"{pdf.parent}/../consolidated/{pdf.name}")
                        else:
                            new_name = pathlib.Path(f"{pdf.parent}/../consolidated/{pdf.stem}- ({counter}){pdf.suffix}")
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
                embeddings      = HuggingFaceEmbeddings(model_name=self._model_name)
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
                embeddings      = HuggingFaceEmbeddings(model_name=self._model_name)
                db              = FAISS.from_documents(splits, embeddings)
                db.save_local(str(self._db_faiss_path))

                for pdf in pdf_docs: pdf.rename(f"{pdf.parent}/../consolidated/{pdf.name}")
    #----------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------
