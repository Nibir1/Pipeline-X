"""
scripts/test_retrieval.py

Role: Verification & RAG Simulation (CLI)
Description:
    This script tests if the pipeline successfully indexed data into Qdrant.
    It performs a "Semantic Search" identical to the API logic:
    1. Converts a text query into a vector using the shared Embedder class.
    2. Queries Qdrant for the nearest neighbors.
    3. Prints the results to prove data ingestion worked.
"""

import sys
import os

# Add the project root to python path so we can import from src
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.ai.embedder import TextEmbedder
from qdrant_client import QdrantClient

def test_retrieval(query_text: str):
    print(f"\n🔎 Query: '{query_text}'")
    print("-" * 60)

    # 1. Initialize Client
    # Default to localhost because this script is usually run from the host machine,
    # not inside the docker network.
    qdrant_host = os.getenv("QDRANT_HOST", "localhost")
    qdrant_port = int(os.getenv("QDRANT_PORT", 6333))
    
    try:
        client = QdrantClient(host=qdrant_host, port=qdrant_port)
        collection_name = "pipeline_x_docs"
        
        # Check if collection exists first
        collections = client.get_collections()
        exists = any(c.name == collection_name for c in collections.collections)
        if not exists:
            print(f"❌ Collection '{collection_name}' not found. Did the Airflow pipeline run?")
            return

        # 2. Embed the Query
        # Use the unified class method (same as API)
        embedder = TextEmbedder()
        query_vector = embedder.embed_text(query_text)

        # 3. Search Qdrant
        search_result = client.search(
            collection_name=collection_name,
            query_vector=query_vector,
            limit=3  # Get top 3 matches
        )

        # 4. Display Results
        if not search_result:
            print("❌ No results found. The collection might be empty.")
            return

        print(f"✅ Found {len(search_result)} relevant chunks:\n")
        
        for i, hit in enumerate(search_result):
            score = hit.score
            payload = hit.payload or {}
            
            # Extract text flexibly (handles 'text', 'page_content', or 'content')
            content = payload.get('text') or payload.get('page_content') or payload.get('content') or "[No Text Stored]"
            source = payload.get('source', 'Unknown')
            category = payload.get('category', 'N/A')

            print(f"[{i+1}] Relevance: {score:.4f}")
            print(f"    Source:   {source} ({category})")
            print(f"    Content:  \"{content[:150]}...\"") # Truncate for readability
            print("")

    except Exception as e:
        print(f"❌ Connection Error: {e}")
        print("   -> Is Qdrant running? (docker ps)")
        print("   -> Are you running this from the host? (localhost vs qdrant)")

if __name__ == "__main__":
    # Test queries based on your mock data themes
    test_retrieval("What is the financial outlook for Q4?")
    test_retrieval("What is the status of Project Alpha?")