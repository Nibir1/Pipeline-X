"""
src/ui/app.py

Role: Frontend User Interface
Description:
    A Streamlit dashboard that allows users to query the RAG pipeline.
    It connects to the FastAPI backend to fetch results.
"""

import streamlit as st
import requests
import os
import json

# --- Configuration ---
# API_URL is injected by Docker Compose. Default to localhost for local testing.
API_URL = os.getenv("API_URL", "http://localhost:8000")

st.set_page_config(
    page_title="Pipeline-X | Corp Search",
    page_icon="🚀",
    layout="wide"
)

# --- Header ---
st.title("Pipeline-X")
st.subheader("Enterprise Knowledge Retrieval System")
st.markdown("---")

# --- Sidebar: System Status ---
with st.sidebar:
    st.header("System Status")
    
    # Check API Health
    try:
        response = requests.get(f"{API_URL}/health", timeout=2)
        if response.status_code == 200:
            st.success(f"✅ API Online ({API_URL})")
        else:
            st.error(f"❌ API Error: {response.status_code}")
    except requests.exceptions.ConnectionError:
        st.error("❌ API Offline (Connection Failed)")
        st.info("Ensure the 'api' container is running.")

    st.markdown("---")
    st.markdown("**Architecture:**")
    st.markdown("- **Orchestrator:** Apache Airflow")
    st.markdown("- **Vector DB:** Qdrant")
    st.markdown("- **LLM Backend:** Local (MiniLM)")
    st.markdown("- **Frontend:** Streamlit")

# --- Main Interface ---

# Search Input
query = st.text_input("Ask a question about the internal documents:", placeholder="e.g., What is the financial outlook for Q4?")

if query:
    if len(query) < 5:
        st.warning("Please enter a longer query.")
    else:
        with st.spinner("Searching vector index..."):
            try:
                # Call the Backend API
                payload = {"query": query, "k": 3}
                response = requests.post(f"{API_URL}/search", json=payload)
                
                if response.status_code == 200:
                    results = response.json()
                    
                    if not results:
                        st.info("No relevant documents found.")
                    else:
                        st.success(f"Found {len(results)} relevant documents.")
                        
                        # Display Results
                        for i, res in enumerate(results):
                            score = res.get("score", 0)
                            text = res.get("text", "No text available.")
                            metadata = res.get("metadata", {})
                            
                            # Create a clean card for each result
                            with st.expander(f"📄 Result {i+1}: {metadata.get('title', 'Untitled')} (Score: {score:.4f})", expanded=True):
                                st.markdown(f"**Category:** `{metadata.get('category', 'N/A')}`")
                                st.markdown(f"**Author:** {metadata.get('author', 'Unknown')}")
                                st.info(text)
                                st.caption(f"Doc ID: {res.get('metadata', {}).get('doc_id', 'N/A')}")
                                
                else:
                    st.error(f"Backend Error: {response.text}")
                    
            except Exception as e:
                st.error(f"Connection Error: {str(e)}")

# --- Footer ---
st.markdown("---")