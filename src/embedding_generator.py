import os
import json
import numpy as np
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

def generate_embeddings(chunks_file: str = "chunks.json", 
                        embeddings_file: str = "embeddings.npy", 
                        metadata_file: str = "metadata.json",
                        model_name: str = "dmis-lab/biobert-v1.1"):
    """
    Loads chunks.json, computes embeddings using BioBERT via SentenceTransformers,
    and saves the vectors to embeddings.npy and mapping info to metadata.json.
    """
    if not os.path.exists(chunks_file):
        print(f"Chunks file '{chunks_file}' not found. Please run chunk generator first.")
        return

    # Load chunks
    with open(chunks_file, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    if not chunks:
        print("No chunks found in chunks.json.")
        return

    print(f"Loaded {len(chunks)} chunks. Loading BioBERT model '{model_name}'...")
    
    # Load SentenceTransformer model
    # SentenceTransformer handles downloading the model and using GPU if available
    try:
        model = SentenceTransformer(model_name)
    except Exception as e:
        print(f"Failed to load BioBERT model: {e}")
        return

    print("Computing embeddings (this might take a moment)...")
    
    # Extract texts for encoding
    texts = [chunk["text"] for chunk in chunks]
    
    # Generate embeddings
    # show_progress_bar=True integrates natively with tqdm in sentence_transformers
    embeddings = model.encode(
        texts, 
        batch_size=32, 
        show_progress_bar=True,
        convert_to_numpy=True
    )

    # Save embeddings to npy file
    np.save(embeddings_file, embeddings)
    print(f"Saved embedding vectors of shape {embeddings.shape} to {embeddings_file}.")

    # Save metadata mapping file
    # We save the IDs, texts, and metadata dictionaries aligned with the npy indices
    metadata_list = []
    for i, chunk in enumerate(chunks):
        metadata_list.append({
            "index": i,
            "id": chunk["id"],
            "text": chunk["text"],
            "metadata": chunk["metadata"]
        })

    with open(metadata_file, "w", encoding="utf-8") as f:
        json.dump(metadata_list, f, indent=2, ensure_ascii=False)
        
    print(f"Saved metadata mappings to {metadata_file}.")

if __name__ == "__main__":
    generate_embeddings()
