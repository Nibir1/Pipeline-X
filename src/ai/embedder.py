"""
src/ai/embedder.py

Role: Vector Embedding Engine
Description:
    Converts text into dense vector representations.
    Uses 'sentence-transformers' (HuggingFace) locally.
    
    Model: 'all-MiniLM-L6-v2'
    - Dimension: 384
    - Speed: Very fast (CPU friendly)
    
    Capabilities:
    1. Batch Mode: embed_chunks() -> Used by Airflow
    2. Real-Time Mode: embed_text() -> Used by API
"""

from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any, Union

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
        BATCH MODE (Used by Airflow):
        Generates embeddings for a list of chunks.
        
        Args:
            chunks (List[Dict]): Output from the Chunker.
            
        Returns:
            List[Dict]: The input list with a new 'vector' key added to each item.
        """
        if not chunks:
            return []

        print(f"[EMBEDDER] Generating embeddings for {len(chunks)} chunks...")
        
        # Extract just the text for batch processing (faster)
        # Handle cases where key might be 'text' or 'page_content'
        texts = [chunk.get("text", chunk.get("page_content", "")) for chunk in chunks]
        
        # Generate vectors
        vectors = self.model.encode(texts, show_progress_bar=True)
        
        # Attach vectors back to the chunk objects
        enriched_chunks = []
        for i, chunk in enumerate(chunks):
            # Convert numpy array to simple list for JSON serialization compatibility
            chunk["vector"] = vectors[i].tolist()
            enriched_chunks.append(chunk)
            
        print("[EMBEDDER] Embedding generation complete.")
        return enriched_chunks

    def embed_text(self, text: str) -> List[float]:
        """
        REAL-TIME MODE (Used by API):
        Generates an embedding for a single string query.
        
        Args:
            text (str): The user's question.
            
        Returns:
            List[float]: The vector representation.
        """
        # Encode returns a numpy array, convert to list for JSON serialization
        vector = self.model.encode(text)
        return vector.tolist()

# Quick test block
if __name__ == "__main__":
    embedder = TextEmbedder()
    
    # Test 1: Batch
    mock_chunks = [{"text": "This is a batch test.", "id": 1}]
    print("Batch Test:", len(embedder.embed_chunks(mock_chunks)[0]["vector"]))
    
    # Test 2: Real-time
    print("Real-Time Test:", len(embedder.embed_text("This is a query.")))