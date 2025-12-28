"""
src/ai/embedder.py

Role: Vector Embedding Generation
Description:
    Converts text chunks into dense vector representations.
    Uses 'sentence-transformers' (HuggingFace) locally.
    
    Model: 'all-MiniLM-L6-v2'
    - Dimension: 384
    - Speed: Very fast (CPU friendly)
"""

from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any

class TextEmbedder:
    """
    Wraps the SentenceTransformer model for generating embeddings.
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize the model. This will download the model weights on first run.
        """
        print(f"[EMBEDDER] Loading model: {model_name}...")
        self.model = SentenceTransformer(model_name)
        print("[EMBEDDER] Model loaded successfully.")

    def embed_chunks(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Generates embeddings for a list of chunks.
        
        Args:
            chunks (List[Dict]): Output from the Chunker.
            
        Returns:
            List[Dict]: The input list with a new 'vector' key added to each item.
        """
        print(f"[EMBEDDER] Generating embeddings for {len(chunks)} chunks...")
        
        # Extract just the text for batch processing (faster)
        texts = [chunk["text"] for chunk in chunks]
        
        # Generate vectors
        # show_progress_bar=True helps visualize in logs
        vectors = self.model.encode(texts, show_progress_bar=True)
        
        # Attach vectors back to the chunk objects
        enriched_chunks = []
        for i, chunk in enumerate(chunks):
            # Convert numpy array to simple list for JSON serialization compatibility
            chunk["vector"] = vectors[i].tolist()
            enriched_chunks.append(chunk)
            
        print("[EMBEDDER] Embedding generation complete.")
        return enriched_chunks

# Quick test block
if __name__ == "__main__":
    embedder = TextEmbedder()
    mock_chunks = [{"text": "This is a test sentence.", "id": 1}]
    print(embedder.embed_chunks(mock_chunks)[0]["vector"][:5]) # Print first 5 dims