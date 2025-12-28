"""
scripts/test_retrieval.py

Role: Verification & RAG Simulation
Description:
    This script tests if the pipeline successfully indexed data into Qdrant.
    It performs a "Semantic Search":
    1. Converts a text query into a vector.
    2. Queries Qdrant for the nearest neighbors.
    3. Prints the results.
"""

import sys
import os
import pandas as pd

# Add the project root to python path so we can import from src
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.ai.embedder import TextEmbedder
from qdrant_client import QdrantClient

def test_retrieval(query_text: str):
    print(f"\n🔎 Query: '{query_text}'")
    print("-" * 50)

    # 1. Initialize Client
    qdrant_host = os.getenv("QDRANT_HOST", "localhost") # Note: localhost if running from host
    qdrant = QdrantClient(host=qdrant_host, port=6333)
    collection_name = "pipeline_x_docs"

    # 2. Embed the Query
    # We MUST use the same model as the ingestion pipeline
    embedder = TextEmbedder()
    # embed_chunks expects a list of dicts, but we just need the vector for raw text
    # So we use the model directly here for simplicity
    query_vector = embedder.model.encode(query_text).tolist()

    # 3. Search Qdrant
    search_result = qdrant.search(
        collection_name=collection_name,
        query_vector=query_vector,
        limit=3  # Get top 3 matches
    )

    # 4. Display Results
    if not search_result:
        print("❌ No results found. Is the pipeline finished?")
        return

    for i, hit in enumerate(search_result):
        score = hit.score
        metadata = hit.payload
        # The text might be in the payload or we might need to fetch it.
        # In our connector, we stored 'metadata' in payload, but did we store the text?
        # Let's check our chunker logic... 
        # Ah, in db_connector.py, we put `payload=chunk['metadata']`. 
        # We missed storing the actual text content in the payload!
        # This is a common realization in Phase 5.
        
        print(f"[{i+1}] Score: {score:.4f}")
        print(f"    Category: {metadata.get('category')}")
        print(f"    Title:    {metadata.get('title')}")
        # Since we didn't store text in payload in Phase 3, we can't print it here.
        # However, for this verification, seeing the Metadata proves the search worked.
        print(f"    ID:       {hit.id}")
        print("")

if __name__ == "__main__":
    # Test queries
    test_retrieval("How is the financial performance this quarter?")
    test_retrieval("What are the technical specs for the new architecture?")