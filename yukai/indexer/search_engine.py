import  faiss
import  numpy                       as      np
import  os
import  pickle

from    sentence_transformers       import  SentenceTransformer
from    typing                      import  List, Dict
#--------------------------------------------------------------------------------------------------

class ClinicalDocument:
    def __init__(self, patient_id: str, path: str):
        self._patient_id = patient_id
        self._path = path
        self._text = self._load_text()
    #----------------------------------------------------------------------------------------------

    def _load_text(self) -> str:
        with open(self._path, 'r', encoding='utf-8') as f:
            return f.read()
    #----------------------------------------------------------------------------------------------

    @property
    def text(self):
        return self._text
    #----------------------------------------------------------------------------------------------

    @property
    def path(self):
        return self._path
    #----------------------------------------------------------------------------------------------

    @property
    def patient_id(self):
        return self._patient_id
    #----------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------

class PatientCorpus:
    def __init__(self, patient_dir: str):
        self._patient_id    = os.path.basename(patient_dir)
        self._documents     = self._load_documents(str(patient_dir))
    #----------------------------------------------------------------------------------------------

    def _load_documents(self, patient_dir: str) -> List[ClinicalDocument]:
        documents = []
        for file in os.listdir(patient_dir):
            if file.endswith(".txt"):
                full_path = os.path.join(patient_dir, file)
                documents.append(ClinicalDocument(self._patient_id, full_path))
        return documents
    #----------------------------------------------------------------------------------------------

    @property
    def patient_id(self):
        return self._patient_id
    #----------------------------------------------------------------------------------------------

    @property
    def documents(self):
        return self._documents
    #----------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------

class PatientSearchEngine:
    def __init__(self, model_name: str = 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'):
        self._model                                         = SentenceTransformer(model_name) if model_name else None
        self._patient_indexes: Dict[str, faiss.IndexFlatL2] = { }
        self._patient_metadata: Dict[str, List[Dict]]       = { }
    #----------------------------------------------------------------------------------------------

    def build_index_for_patient(self, patient_corpus: PatientCorpus, save_dir: str = None):
        texts       = [doc.text for doc in patient_corpus.documents]
        embeddings  = self._model.encode(texts, batch_size=16, show_progress_bar=True)
        embeddings  = np.array(embeddings).astype('float32')

        dimension   = embeddings.shape[1]
        index       = faiss.IndexFlatL2(dimension)
        index.add(embeddings)

        patient_id                          = patient_corpus.patient_id
        self._patient_indexes[patient_id]   = index
        self._patient_metadata[patient_id]  = [{'path': doc.path} for doc in patient_corpus.documents]

        if save_dir:
            self.save_index(patient_id, save_dir)
    #----------------------------------------------------------------------------------------------

    def save_index(self, patient_id: str, save_dir: str):
        os.makedirs(save_dir, exist_ok=True)
        index       = self._patient_indexes[patient_id]
        metadata    = self._patient_metadata[patient_id]

        faiss.write_index(index, os.path.join(save_dir, f"{patient_id}.index"))
        with open(os.path.join(str(save_dir), f"{patient_id}_meta.pkl"), 'wb') as f:
            pickle.dump(metadata, f)
    #----------------------------------------------------------------------------------------------

    def load_index(self, patient_id: str, save_dir: str):
        index_path  = os.path.join(save_dir, f"{patient_id}.index")
        meta_path   = os.path.join(save_dir, f"{patient_id}_meta.pkl")

        if os.path.exists(index_path) and os.path.exists(meta_path):
            index = faiss.read_index(index_path)
            with open(meta_path, 'rb') as f:
                metadata = pickle.load(f)

            self._patient_indexes[patient_id]   = index
            self._patient_metadata[patient_id]  = metadata
        else:
            raise FileNotFoundError(f"Index or metadata not found for patient {patient_id} in {save_dir}")
    #----------------------------------------------------------------------------------------------

    def query_patient(self, patient_id: str, question: str, top_k: int = 5) -> List[Dict]:
        if patient_id not in self._patient_indexes:
            raise ValueError(f"No index loaded for patient {patient_id}")

        query_embedding = self._model.encode([question]).astype('float32')
        index           = self._patient_indexes[patient_id]
        metadata        = self._patient_metadata[patient_id]

        distances, indices = index.search(query_embedding, top_k)

        results = []
        for i in indices[0]:
            if 0 <= i < len(metadata):
                results.append({
                    'path': metadata[i]['path'],
                    'score': float(distances[0][i])
                })
        return results
    #----------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------