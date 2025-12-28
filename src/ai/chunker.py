"""
src/ai/chunker.py

Role: Text Splitting (Chunking)
Description:
    This module splits long text documents into smaller chunks (windows).
    This is essential for RAG (Retrieval Augmented Generation) because:
    1. Embedding models have token limits (usually 512).
    2. Smaller chunks provide more precise semantic search results.
"""

from langchain.text_splitter import RecursiveCharacterTextSplitter
from typing import List, Dict, Any

class TextChunker:
    """
    Wraps LangChain's text splitter logic.
    """

    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        """
        Args:
            chunk_size (int): Maximum tokens/chars per chunk.
            chunk_overlap (int): Overlap between chunks to maintain context.
        """
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", " ", ""]
        )

    def chunk_documents(self, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Iterates through raw documents and splits their 'content' field.
        
        Args:
            raw_data (List[Dict]): List of dicts containing 'content' and metadata.
            
        Returns:
            List[Dict]: A flattened list of chunks. Each chunk has:
                        - 'id': Original doc ID
                        - 'chunk_id': Unique ID for the chunk
                        - 'text': The chunk text
                        - 'metadata': Original metadata
        """
        print("[CHUNKER] Splitting documents into chunks...")
        chunked_docs = []

        for doc in raw_data:
            original_id = doc.get("id")
            text = doc.get("content", "")
            
            # Perform the split
            chunks = self.splitter.split_text(text)
            
            for i, chunk_text in enumerate(chunks):
                chunked_docs.append({
                    "doc_id": original_id,
                    "chunk_index": i,
                    "text": chunk_text,
                    "metadata": {
                        "title": doc.get("title"),
                        "author": doc.get("author"),
                        "category": doc.get("category"),
                        "created_at": doc.get("created_at")
                    }
                })

        print(f"[CHUNKER] Produced {len(chunked_docs)} chunks from {len(raw_data)} documents.")
        return chunked_docs

# Quick test block
if __name__ == "__main__":
    chunker = TextChunker()
    mock_data = [{"id": "1", "content": "Sentence one. " * 50, "title": "Test"}]
    print(len(chunker.chunk_documents(mock_data)))