"""
src/api/main.py

Role: Retrieval API Service (RAG Backend)
Description:
    A FastAPI application that serves as the interface for the RAG pipeline.
    It exposes endpoints to:
    1. Health check the service.
    2. Perform semantic search (querying Qdrant).
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import sys
import os

# Ensure we can import from src if running locally without Docker PYTHONPATH
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))

from src.ai.embedder import TextEmbedder
from qdrant_client import QdrantClient

# 1. Configuration
app = FastAPI(title="Pipeline-X RAG API", version="1.0")

# Connect to Qdrant (Vector DB)
# Uses environment variable 'QDRANT_HOST' (defaulting to 'qdrant' for Docker)
QDRANT_HOST = os.getenv("QDRANT_HOST", "qdrant")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", 6333))
client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

# Initialize Embedder (Same one used in Airflow)
# This loads the model into memory once when the API starts
print("[API] Loading Embedding Model...")
embedder = TextEmbedder()
print("[API] Model Loaded.")

# --- Models ---
class QueryRequest(BaseModel):
    question: str       # Frontend sends 'question'
    top_k: int = 3      # Frontend sends 'top_k'

@app.get("/health")
def health_check():
    """Heartbeat endpoint for Docker healthchecks."""
    return {"status": "healthy", "service": "api"}

@app.post("/search")
def search_knowledge_base(request: QueryRequest):
    """
    Semantic Search Endpoint:
    1. Embeds the user's question.
    2. Searches Qdrant for the most similar chunks.
    3. Returns the context found.
    """
    try:
        print(f"[API] Searching for: {request.question}")
        
        # 1. Vectorize the Question
        # Note: embedder.embed_text returns a list of floats
        query_vector = embedder.embed_text(request.question)
        
        # 2. Search Qdrant
        # We query the collection 'pipeline_x_docs' populated by Airflow
        hits = client.search(
            collection_name="pipeline_x_docs",
            query_vector=query_vector,
            limit=request.top_k
        )
        
        # 3. Format Results
        results = []
        for hit in hits:
            # Robust Payload Extraction:
            # Different chunkers might save text as 'text', 'page_content', or 'content'
            payload = hit.payload or {}
            text_content = payload.get("text") or payload.get("page_content") or payload.get("content") or "No text available"
            
            results.append({
                "score": hit.score,
                "text": text_content,
                "source": payload.get("source", "Unknown")
            })
            
        return {"results": results, "count": len(results)}

    except Exception as e:
        print(f"[ERROR] Search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# For local testing without Docker
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)