"""
src/api/main.py

Role: Retrieval API Service
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

# Ensure we can import from src
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))

from src.ai.embedder import TextEmbedder
from qdrant_client import QdrantClient

app = FastAPI(title="Pipeline-X RAG API", version="1.0")

# --- Models ---
class QueryRequest(BaseModel):
    query: str
    k: int = 3  # Number of results to return

class SearchResult(BaseModel):
    score: float
    text: str
    metadata: dict

# --- Dependencies ---
# Initialize these once at startup
qdrant_host = os.getenv("QDRANT_HOST", "qdrant") # Use 'localhost' if testing locally outside docker
qdrant_client = QdrantClient(host=qdrant_host, port=6333)
embedder = TextEmbedder()

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "pipeline-x-api"}

@app.post("/search", response_model=List[SearchResult])
def search_documents(request: QueryRequest):
    """
    Vector search endpoint.
    1. Embeds the user query.
    2. Searches Qdrant.
    3. Returns text and metadata.
    """
    try:
        # 1. Embed
        vector = embedder.model.encode(request.query).tolist()
        
        # 2. Search
        hits = qdrant_client.search(
            collection_name="pipeline_x_docs",
            query_vector=vector,
            limit=request.k
        )
        
        # 3. Format Response
        results = []
        for hit in hits:
            # Extract text from the payload we fixed in Phase 6
            content = hit.payload.get("page_content", "No content available.")
            
            results.append(SearchResult(
                score=hit.score,
                text=content,
                metadata={k: v for k, v in hit.payload.items() if k != "page_content"}
            ))
            
        return results
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# For local testing
if __name__ == "__main__":
    import uvicorn
    # If running locally, you might need to change qdrant_host to 'localhost' above manually
    uvicorn.run(app, host="0.0.0.0", port=8000)