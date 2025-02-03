import  joblib
import  os
import  pathlib

from    backend.db                          import NoSQLDB
from    sklearn.feature_extraction.text     import TfidfVectorizer
from    sklearn.metrics.pairwise            import cosine_similarity
#--------------------------------------------------------------------------------------------------

STORAGE_PATH = (pathlib.Path(__file__).parent / "../../data").resolve()
#--------------------------------------------------------------------------------------------------

class DocumentClassifier:
    def __init__(self, storage_path=STORAGE_PATH):
        self.storage_path   = storage_path
        self.db_path        = self.storage_path / "dbs/documents.fs"
        self.db             = NoSQLDB(self.db_path)
        self.vectorizer     = TfidfVectorizer()
        self.tfidf_matrix   = None

        if not os.path.exists(self.storage_path):
            os.makedirs(self.storage_path)
        self.load_processed_data()
    #----------------------------------------------------------------------------------------------

    def add_document(self, ref_id, doc_id, content, tags=None, keywords=None):
        """Adds or updates a document in the database."""
        tags        = tags or []
        keywords    = keywords or []

        document_data = \
        {
            "ref-id":   ref_id,
            "content":  content,
            "tags":     tags,
            "keywords": keywords
        }

        self.db.update(ref_id, doc_id, document_data)
    #----------------------------------------------------------------------------------------------

    def get_all_documents(self, ref_id):
        """Retrieves all documents from the database."""
        return [ doc for _, doc in self.db.get(ref_id).items() ]
    #----------------------------------------------------------------------------------------------

    def process_documents(self):
        """Processes documents using TF-IDF vectorization."""
        documents           = self.get_all_documents()
        contents            = [ doc["content"] for doc in documents ]
        self.tfidf_matrix   = self.vectorizer.fit_transform(contents)

        joblib.dump(self.vectorizer,    os.path.join(self.storage_path, "vectorizer.pkl"))
        joblib.dump(self.tfidf_matrix,  os.path.join(self.storage_path, "tfidf_matrix.pkl"))
    #----------------------------------------------------------------------------------------------

    def load_processed_data(self):
        """Loads processed TF-IDF data if it exists."""
        try:
            self.vectorizer     = joblib.load(os.path.join(self.storage_path, "vectorizer.pkl"))
            self.tfidf_matrix   = joblib.load(os.path.join(self.storage_path, "tfidf_matrix.pkl"))
        except FileNotFoundError:
            print("No processed data found. Please run process_documents().")
    #----------------------------------------------------------------------------------------------

    def classify_question(self, ref_id, question, threshold=0.5):
        """Classifies whether documents are relevant to a given question."""
        if self.tfidf_matrix is None:
            raise ValueError("TF-IDF data not processed. Run process_documents() first.")

        # Vectorize the question for TF-IDF similarity
        question_vector = self.vectorizer.transform([question])
        similarities    = cosine_similarity(question_vector, self.tfidf_matrix)[0]

        # Extract keywords and tags from the question
        question_keywords = question.lower().split()  # Simple tokenization for demo purposes

        relevant_docs = [ ]
        for i, similarity in enumerate(similarities):
            ref_docs = self.db.get(ref_id)
            doc_keys = list(ref_docs.keys())
            doc_data = ref_docs[doc_keys[i]]

            # Calculate additional relevance score based on tags and keywords
            keyword_matches     = len(set(doc_data["keywords"]) & set(question_keywords))
            tag_matches         = len(set(doc_data["tags"]) & set(question_keywords))
            additional_score    = 0.1 * (keyword_matches + tag_matches)  # Weight adjustment

            total_score = similarity + additional_score
            if total_score >= threshold:
                relevant_docs.append \
                ({
                    "id":               doc_keys[i],
                    "similarity":       similarity,
                    "additional_score": additional_score,
                    "total_score":      total_score,
                    "tags":             doc_data["tags"],
                    "keywords":         doc_data["keywords"]
                })

        return sorted(relevant_docs, key=lambda x: x["total_score"], reverse=True)
    #----------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------

# Usage example
if __name__ == "__main__":
    classifier = DocumentClassifier()

    # Add or update documents
    classifier.add_document("doc1", "This document is about machine learning and AI.", tags=["AI", "ML"], keywords=["machine learning", "artificial intelligence"])
    classifier.add_document("doc2", "This text discusses deep learning techniques.", tags=["Deep Learning"], keywords=["deep learning", "neural networks"])
    classifier.add_document("doc3", "Unrelated topic about gardening and plants.", tags=["Gardening"], keywords=["gardening", "plants"])

    # Process documents (run once after adding or updating documents)
    classifier.process_documents()

    # Classify a question
    question = "What is deep learning?"
    relevant_docs = classifier.classify_question(question, threshold=0.2)

    print("Relevant documents:")
    for doc in relevant_docs:
        print(f"Document ID: {doc['id']}, Similarity: {doc['similarity']:.2f}, Tags: {doc['tags']}, Keywords: {doc['keywords']}")
