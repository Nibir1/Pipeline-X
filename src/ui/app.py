"""
src/ui/app.py

Role: Frontend User Interface (Streamlit)
Description:
    A Modern Chatbot Interface for the Pipeline-X Knowledge Base.
    It connects to the FastAPI backend to perform RAG (Retrieval Augmented Generation).
"""

import streamlit as st
import requests
import os
import time

# ---------------------------------------------------------
# 1. CONFIGURATION
# ---------------------------------------------------------
st.set_page_config(
    page_title="Pipeline-X Intelligence",
    page_icon="🧠",
    layout="wide"
)

# Load API URL from Docker Environment
API_URL = os.getenv("API_URL", "http://localhost:8000")

# ---------------------------------------------------------
# 2. SIDEBAR (System Health)
# ---------------------------------------------------------
with st.sidebar:
    st.title("🚀 Pipeline-X")
    st.markdown("---")
    st.subheader("System Status")
    
    # Live Health Check
    api_status = "Unknown"
    status_color = "gray"
    try:
        r = requests.get(f"{API_URL}/health", timeout=2)
        if r.status_code == 200:
            api_status = "Online"
            status_color = "green"
            st.success(f"✅ API Online")
        else:
            api_status = "Error"
            status_color = "red"
            st.error(f"❌ API Error: {r.status_code}")
    except:
        api_status = "Offline"
        status_color = "red"
        st.error("❌ API Offline")

    st.markdown("---")
    st.markdown("### 🏗 Architecture")
    st.info(
        """
        - **Orchestration:** Airflow (Docker)
        - **Storage:** Azure Data Lake Gen2
        - **Database:** Azure PostgreSQL
        - **Vector DB:** Qdrant
        - **Compute:** Spark (Hybrid)
        """
    )
    
    if st.button("Clear Chat History"):
        st.session_state.messages = []
        st.rerun()

# ---------------------------------------------------------
# 3. MAIN CHAT INTERFACE
# ---------------------------------------------------------
st.header("🧠 Enterprise Knowledge Search")
st.caption("Ask natural language questions about your ingested business documents.")

# Initialize Chat History in Session State
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display Previous Messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ---------------------------------------------------------
# 4. QUERY HANDLING
# ---------------------------------------------------------
if prompt := st.chat_input("What is the priority of the financial outlook?"):
    
    # 1. Show User Message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. Generate Assistant Response
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        with st.spinner("Analyzing Knowledge Base..."):
            try:
                # --- CALL BACKEND API ---
                payload = {"question": prompt, "top_k": 3}
                response = requests.post(f"{API_URL}/search", json=payload)
                
                if response.status_code == 200:
                    data = response.json()
                    results = data.get("results", [])
                    
                    if not results:
                        full_response = "I searched the knowledge base but couldn't find any relevant documents matching your query."
                    else:
                        # Format the output beautifully
                        full_response += f"**I found {len(results)} relevant insights:**\n\n"
                        
                        for i, res in enumerate(results):
                            score = res.get('score', 0)
                            text = res.get('text', 'N/A')
                            source = res.get('source', 'Unknown')
                            
                            # Add divider between results
                            if i > 0: full_response += "\n---\n"
                            
                            full_response += f"#### 📄 Insight {i+1} (Relevance: {score:.2f})\n"
                            full_response += f"> *\"{text}\"*\n"
                            full_response += f"**Source:** `{source}`\n"
                            
                else:
                    full_response = f"⚠️ **Backend Error:** The API returned status code {response.status_code}."
                    
            except requests.exceptions.ConnectionError:
                full_response = "❌ **Connection Error:** Could not connect to the Backend API. Is the Docker container running?"
            except Exception as e:
                full_response = f"❌ **Error:** {str(e)}"

        # 3. Display Final Response
        message_placeholder.markdown(full_response)
        
        # 4. Save to History
        st.session_state.messages.append({"role": "assistant", "content": full_response})