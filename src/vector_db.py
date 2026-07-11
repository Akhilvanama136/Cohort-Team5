import os
import json
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

def build_faiss_index(embeddings_file: str = "embeddings.npy", 
                      metadata_file: str = "metadata.json", 
                      index_file: str = "medical_db.faiss"):
    """
    Loads embeddings and creates a normalized FAISS index (for Cosine Similarity / Inner Product search).
    Saves the index to medical_db.faiss.
    """
    if not os.path.exists(embeddings_file) or not os.path.exists(metadata_file):
        print("Embeddings or metadata file not found. Please run embedding generator first.")
        return

    # Load embeddings
    embeddings = np.load(embeddings_file).astype('float32')
    
    # Load metadata to verify length matching
    with open(metadata_file, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    if len(embeddings) != len(metadata):
        print(f"Error: Dimension mismatch between embeddings ({len(embeddings)}) and metadata ({len(metadata)}).")
        return

    print(f"Loaded {len(embeddings)} embedding vectors. Dimension size: {embeddings.shape[1]}")

    # L2 normalize the vectors so that Inner Product search behaves as Cosine Similarity
    faiss.normalize_L2(embeddings)

    # Initialize Flat Inner Product Index
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatIP(dimension)
    
    # Add vectors to index
    index.add(embeddings)
    
    # Save the index file
    faiss.write_index(index, index_file)
    print(f"Successfully built FAISS index and saved to {index_file}.")

class MedicalRetriever:
    """
    Retrieval class to load the FAISS index and metadata, and perform semantic searches.
    """
    def __init__(self, index_file: str = "medical_db.faiss", 
                 metadata_file: str = "metadata.json",
                 model_name: str = "dmis-lab/biobert-v1.1"):
        self.index_file = index_file
        self.metadata_file = metadata_file
        self.model_name = model_name
        self.index = None
        self.metadata = None
        self.model = None

    def load(self):
        """Loads index, metadata, and BioBERT model."""
        if not os.path.exists(self.index_file) or not os.path.exists(self.metadata_file):
            raise FileNotFoundError("FAISS index or metadata mappings not found. Build them first.")

        print(f"Loading FAISS index from {self.index_file}...")
        self.index = faiss.read_index(self.index_file)
        
        print(f"Loading metadata from {self.metadata_file}...")
        with open(self.metadata_file, "r", encoding="utf-8") as f:
            self.metadata = json.load(f)

        print(f"Loading BioBERT model '{self.model_name}' for query encoding...")
        self.model = SentenceTransformer(self.model_name)
        print("Retriever is ready.")

    def search(self, query: str, top_k: int = 5, category: str = None):
        """
        Embeds the query, normalizes it, and queries FAISS for Top-K matches.
        Supports filtering by category if specified.
        """
        if self.index is None or self.metadata is None or self.model is None:
            self.load()

        # Embed query text
        query_vector = self.model.encode([query], convert_to_numpy=True).astype('float32')
        
        # Normalize for Cosine Similarity (Inner Product Flat index)
        faiss.normalize_L2(query_vector)

        # If category is provided, retrieve more candidates for post-filtering
        # Retrieve more candidates so we can apply post-filtering and metadata boosting
        search_k = max(top_k * 5, 50)
        scores, indices = self.index.search(query_vector, search_k)
        
        candidates = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:
                continue
            
            # Retrieve chunk metadata
            chunk_info = self.metadata[idx]
            chunk_category = chunk_info["metadata"].get("category", "")
            
            # Category filter check
            if category and chunk_category.lower() != category.lower():
                continue
            
            # Metadata-based disease keyword boost
            # If the chunk specifies a disease and that disease is mentioned in the query, boost its relevance
            chunk_disease = chunk_info["metadata"].get("disease", "")
            final_score = float(score)
            if chunk_disease and chunk_disease.lower() in query.lower():
                final_score += 0.08  # Give a significant boost for exact topic match

            candidates.append({
                "score": final_score,
                "text": chunk_info["text"],
                "source": chunk_info["metadata"]["source"],
                "category": chunk_category,
                "page": chunk_info["metadata"].get("page", 1)
            })
            
        # Sort candidates by boosted score and return the top_k
        candidates.sort(key=lambda x: x["score"], reverse=True)
        return candidates[:top_k]

if __name__ == "__main__":
    build_faiss_index()
