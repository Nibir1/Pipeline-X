# Pipeline-X | Applied AI Data Platform

> 🚀 **A containerized End-to-End ELT, Vectorization, and Retrieval Pipeline connecting Raw Data with GenAI Orchestration.**

[![Pipeline-X Demo](https://img.youtube.com/vi/S7Es1ZTmpKw/maxresdefault.jpg)](https://youtu.be/S7Es1ZTmpKw)

> 📺 **[Watch the full end-to-end demo](https://youtu.be/S7Es1ZTmpKw)** featuring the dual-stream ingestion and RAG retrieval.

<br />

![Status](https://img.shields.io/badge/Status-Production%20Ready-success?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.10-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Airflow](https://img.shields.io/badge/Apache%20Airflow-2.9-017CEE?style=for-the-badge&logo=apacheairflow&logoColor=white)
![Postgres](https://img.shields.io/badge/Postgres-15-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)
![Qdrant](https://img.shields.io/badge/Vector_DB-Qdrant-b91d47?style=for-the-badge&logo=qdrant&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.32-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white)

**Pipeline-X** is a reference architecture for building "Data Foundations for AI". It demonstrates the complete lifecycle of a modern data platform: orchestrating the cleaning of data for SQL Analytics while simultaneously generating vector embeddings for AI Retrieval Augmented Generation (RAG).

### Why this exists
Building reliable data pipelines for AI is complex. Pipeline-X solves common engineering pitfalls by demonstrating a robust, unified architecture:

1.  **Dual-Stream Processing:** Orchestrates a single workflow that splits data into structured metadata (for SQL Warehousing) and unstructured chunks (for Vector Search), keeping Analytics and AI in sync.
2.  **Robust Ingestion Protocol:** Implements low-level **Postgres COPY** protocols to bypass common ORM bottlenecks and dependency conflicts (Pandas/SQLAlchemy), ensuring high-performance data loading.
3.  **Decoupled Service Layer:** Unlike simple scripts, this exposes data via a **FastAPI** microservice, allowing frontend applications (Streamlit) to consume RAG capabilities without direct database access.

---

## System Architecture

The application is built on a containerized microservices architecture managed by Docker Compose:

1.  **Orchestrator (Apache Airflow):** The "Manager." It schedules the DAGs that fetch raw data, transform it using Pandas, and trigger vectorization tasks.
2.  **Storage Layer (Hybrid):**
    * **PostgreSQL:** Stores structured metadata (Author, Date, Category) for traditional analytics.
    * **Qdrant:** Stores high-dimensional vector embeddings for semantic search.
3.  **Service Layer (FastAPI):** A lightweight REST API that handles embedding generation and vector similarity search.
4.  **User Interface (Streamlit):** An interactive "Corporate Search" dashboard that allows users to query the knowledge base in natural language.

## Key Features

-   **Idempotent Pipelines:** The Airflow DAG uses "Upsert" logic, allowing the pipeline to run multiple times without creating duplicate records or vectors.
-   **Local AI Inference:** Uses `sentence-transformers/all-MiniLM-L6-v2` running locally on CPU, eliminating external API costs for embedding generation.
-   **Semantic Search:** Enables context-aware retrieval. Searching for "Financial performance" retrieves documents categorized as "Financial Reports" even if the keywords don't match exactly.
-   **Automated Quality Checks:** Includes CI/CD workflows for linting and logic verification, ensuring code quality before deployment.

---

## Tech Stack

### Orchestration & Compute
-   **Manager:** Apache Airflow 2.9 (Dockerized)
-   **Language:** Python 3.10
-   **Transformation:** Pandas 2.2

### Storage & AI
-   **Warehouse:** PostgreSQL 15
-   **Vector DB:** Qdrant (Rust-based engine)
-   **AI Framework:** LangChain (Chunking), Sentence-Transformers (Embeddings)

### Interface & API
-   **Backend:** FastAPI, Uvicorn
-   **Frontend:** Streamlit
-   **Networking:** HTTPX, Pydantic

### DevOps
-   **Containerization:** Docker, Docker Compose
-   **Automation:** Makefiles for sequential build orchestration & environment cleanup.

---

## Getting Started

### Prerequisites

-   Docker Desktop installed
-   Make (Optional, but recommended for automation)

### Installation

1.  **Clone the repository**
    ```bash
    git clone https://github.com/Nibir1/Pipeline-X.git
    cd Pipeline-X
    ```

2.  **Set Environment Variables**
    Create a `.env` file in the root directory (defaults are provided in the repo):
    ```bash
    AIRFLOW_UID=50000
    POSTGRES_USER=airflow
    POSTGRES_PASSWORD=airflow
    QDRANT_HOST=qdrant
    API_URL=http://localhost:8000/docs
    ```

3.  **Build and Run**
    ```bash
    make build
    ```

The `make` command handles the sequential build process to avoid race conditions. Once complete:
-   **Frontend UI:** [http://localhost:8501](http://localhost:8501)
-   **Airflow UI:** [http://localhost:8080](http://localhost:8080) (User: `admin` / Pass: `admin`)
-   **API Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)

### Testing & Validation

The project includes specific verification scripts to prove the "Applied AI" capabilities.

To verify the semantic search logic without the UI:
1.  Enter the scheduler container:
    ```bash
    make shell
    ```
2.  Run the verification script:
    ```bash
    python scripts/test_retrieval.py
    ```

*This will validate that a query for "Technical Specs" correctly retrieves documents with the "Technical" category.*

### How It Works

**The Ingestion Pipeline (Airflow DAG)**
1.  **Extract:** Generates mock JSON business reports (Financial, Technical).
2.  **Transform:** Pandas cleans timestamps and standardizes author names.
3.  **Load (SQL):** Metadata is pushed to Postgres using the high-speed `COPY` protocol.
4.  **Vectorize (AI):** Text is split into 500-token chunks and embedded using `MiniLM`.
5.  **Index:** Vectors + Payload are upserted into Qdrant.

**The Retrieval Flow (RAG)**
1.  **User Query:** "How is the Q4 revenue?" entered in Streamlit.
2.  **API Call:** Frontend sends request to FastAPI.
3.  **Embedding:** FastAPI embeds the query using the same model as ingestion.
4.  **Search:** Qdrant finds the nearest neighbors via Cosine Similarity.
5.  **Display:** Results and context are returned to the user.

## Project Structure

```text
pipeline-x/
├── docker-compose.yml       # Orchestration (Airflow, DBs, API, UI)
├── Makefile                 # Build automation scripts
├── dags/                    # Airflow DAGs
│   ├── ingestion_pipeline.py # Main ELT + AI workflow
│   └── utils/               # Robust DB Connectors
├── src/                     # Core Logic
│   ├── etl/                 # Extractors & Transformers
│   ├── ai/                  # Chunking & Embedding logic
│   ├── api/                 # FastAPI Backend
│   └── ui/                  # Streamlit Frontend
├── requirements.txt         # Python Dependencies
└── Dockerfile               # Custom Airflow Image
```

## Roadmap
- [x] Core Physics Engine (60Hz Loop)
- [x] AI Voice Control & JSON Parsing
- [x] Weather Simulation (Physics + Visuals)
- [x] Automated Captain's Logs
- [ ] Digital Twin Replay System
- [ ] Fleet Management (Multi-Vessel Support)

---

## Developer Spotlight

**Nahasat Nibir** — Building intelligent, high‑performance developer tools and AI‑powered systems in Go and Python.

- GitHub: https://github.com/Nibir1
- LinkedIn: https://www.linkedin.com/in/nibir-1/
- ArtStation: https://www.artstation.com/nibir

---