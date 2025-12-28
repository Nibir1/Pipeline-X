"""
src/ai/chunker.py

Role: Text Splitting (Chunking)
Description:
    Splits long documents into smaller windows.
    CRITICAL UPDATE: Now includes the chunk text in the metadata so it can be retrieved.
"""

from langchain.text_splitter import RecursiveCharacterTextSplitter
from typing import List, Dict, Any

class TextChunker:
    """
    Wraps LangChain's text splitter logic.
    """

    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", " ", ""]
        )

    def chunk_documents(self, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Iterates through raw documents and splits their 'content' field.
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
                    "vector": [], # Placeholder, will be filled by embedder
                    "metadata": {
                        "title": doc.get("title"),
                        "author": doc.get("author"),
                        "category": doc.get("category"),
                        "created_at": doc.get("created_at"),
                        "page_content": chunk_text  # <--- CRITICAL FIX: Storing text in metadata
                    }
                })

        print(f"[CHUNKER] Produced {len(chunked_docs)} chunks from {len(raw_data)} documents.")
        return chunked_docs