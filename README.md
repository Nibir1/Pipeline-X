# Pipeline-X | Applied AI Data Platform

> 🚀 **A Hybrid Cloud, Big Data-Ready ELT & RAG Pipeline connecting Raw Data with GenAI Orchestration.**

[![Pipeline-X Demo](https://img.youtube.com/vi/S7Es1ZTmpKw/maxresdefault.jpg)](https://youtu.be/S7Es1ZTmpKw)

> 📺 **[Watch the full end-to-end demo](https://youtu.be/S7Es1ZTmpKw)** featuring dual-stream ingestion and RAG retrieval.

<br />

![Status](https://img.shields.io/badge/Status-Production%20Ready-success?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.10-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Spark](https://img.shields.io/badge/Apache%20Spark-3.5-E25A1C?style=for-the-badge&logo=apachespark&logoColor=white)
![Azure](https://img.shields.io/badge/Azure-Cloud-0078D4?style=for-the-badge&logo=microsoftazure&logoColor=white)
![Terraform](https://img.shields.io/badge/Terraform-IaC-7B42BC?style=for-the-badge&logo=terraform&logoColor=white)
![Airflow](https://img.shields.io/badge/Apache%20Airflow-2.9-017CEE?style=for-the-badge&logo=apacheairflow&logoColor=white)
![Postgres](https://img.shields.io/badge/Postgres-15-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)
![Qdrant](https://img.shields.io/badge/Vector_DB-Qdrant-b91d47?style=for-the-badge&logo=qdrant&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white)

**Pipeline-X** is a reference architecture for building "Data Foundations for AI". It demonstrates the complete lifecycle of a modern data platform: orchestrating distributed data processing (Spark), managing hybrid cloud infrastructure (Terraform/Azure), and generating vector embeddings for AI Retrieval Augmented Generation (RAG).

### Why this exists
Building reliable data pipelines for AI is complex. Pipeline-X solves common engineering pitfalls by demonstrating a robust, unified architecture that scales from "Local Dev" to "Enterprise Cloud":

1.  **Hybrid Cloud Architecture:** Deploys storage resources to **Microsoft Azure** using **Terraform (IaC)**, connecting local microservices to managed cloud databases.
2.  **Big Data Ready:** Features a dual-mode transformation layer. It uses **Pandas** for speed on small data and includes an integrated **Apache Spark Cluster** for distributed processing of massive datasets.
3.  **Dual-Stream Processing:** Orchestrates a workflow that splits data into structured metadata (for SQL Warehousing) and unstructured chunks (for Vector Search), keeping Analytics and AI in sync.
4.  **Decoupled Service Layer:** Exposes data via a **FastAPI** microservice, allowing frontend applications (Streamlit) to consume RAG capabilities without direct database access.

---

## System Architecture

The application is built on a containerized microservices architecture managed by Docker Compose, connected to Azure Cloud:

1.  **Orchestrator (Apache Airflow):** The "Manager." It schedules DAGs, monitors dependencies, and triggers Spark jobs.
2.  **Compute Engine:**
    * **Local Executor:** Runs lightweight Python/Pandas tasks.
    * **Apache Spark Cluster:** A Master/Worker setup for distributed ETL and Parquet file generation.
3.  **Storage Layer (Hybrid):**
    * **Azure Database for PostgreSQL:** Managed Cloud Database storing structured metadata (Author, Date, Category).
    * **Qdrant (Local):** Stores high-dimensional vector embeddings for semantic search.
4.  **Service Layer (FastAPI):** A lightweight REST API that handles embedding generation and vector similarity search.
5.  **User Interface (Streamlit):** An interactive "Corporate Search" dashboard for natural language querying.

---

## Tech Stack

### Infrastructure & Cloud
-   **Cloud Provider:** Microsoft Azure (Sweden Central Region)
-   **IaC:** Terraform
-   **Database:** Azure Database for PostgreSQL (Flexible Server)

### Orchestration & Big Data
-   **Manager:** Apache Airflow 2.9
-   **Distributed Compute:** Apache Spark 3.5.1 (PySpark)
-   **Local Transform:** Pandas 2.2

### AI & Storage
-   **Vector DB:** Qdrant
-   **AI Framework:** LangChain (Chunking), Sentence-Transformers (Embeddings)

### Interface & API
-   **Backend:** FastAPI, Uvicorn
-   **Frontend:** Streamlit

---

## Getting Started

### Prerequisites

-   Docker Desktop installed
-   Make (Optional, but recommended)
-   **Optional:** Azure CLI & Terraform (Only required if deploying infrastructure)

### Installation

1.  **Clone the repository**
    ```bash
    git clone https://github.com/Nibir1/Pipeline-X.git
    cd Pipeline-X
    ```

2.  **Infrastructure Setup (Optional - Hybrid Mode)**
    If you want to use Azure Cloud Storage, use the provided Terraform scripts:
    ```bash
    cd infra
    terraform init
    terraform apply
    # Copy the 'db_host' output to your .env file
    ```

3.  **Set Environment Variables**
    Create a `.env` file in the root directory. Update `POSTGRES_HOST` if using Azure, or keep it `postgres` for local testing.
    ```bash
    AIRFLOW_UID=50000
    POSTGRES_HOST=pipeline-x-db-xxxx.postgres.database.azure.com  # Or 'postgres' for local
    POSTGRES_USER=airflow_admin
    POSTGRES_PASSWORD=SecurePassword123!
    POSTGRES_DB=airflow
    QDRANT_HOST=qdrant
    API_URL=http://localhost:8000/docs
    ```

4.  **Build and Run**
    ```bash
    make build
    ```

The `make` command handles the sequential build process. Once complete:
-   **Frontend UI:** [http://localhost:8501](http://localhost:8501)
-   **Airflow UI:** [http://localhost:8080](http://localhost:8080)
-   **Spark Master UI:** [http://localhost:8081](http://localhost:8081)

### Testing & Validation

The project includes specific verification scripts for AI and Big Data.

**1. Verify Semantic Search (RAG)**
```bash
make shell
python scripts/test_retrieval.py
```

**2. Verify Spark Cluster (Big Data) Run the PySpark transformer to process raw data into Parquet format:**
```bash
make shell
# Generate mock data first
python gen_data.py
# Submit job to Spark Cluster
python src/etl/spark_transformer.py
```

## Project Structure

```text
pipeline-x/
├── docker-compose.yml        # Orchestration (Airflow, Spark, API, UI)
├── Makefile                  # Build automation scripts
├── infra/                    # Terraform Infrastructure as Code (Azure)
│   ├── main.tf               # Cloud Resource Definitions
│   └── .gitignore            # Excludes Terraform state/binaries
├── dags/                     # Airflow DAGs
│   ├── ingestion_pipeline.py # Main ELT + AI workflow
│   └── utils/                # DB Connectors
├── src/                      # Core Logic
│   ├── etl/                  # Extractors & Transformers
│   │   ├── extractor.py      # Data Generator
│   │   └── spark_transformer.py # PySpark Logic
│   ├── ai/                   # Chunking & Embedding logic
│   ├── api/                  # FastAPI Backend
│   └── ui/                   # Streamlit Frontend
├── requirements.txt          # Python Dependencies
└── Dockerfile                # Custom Airflow Image (includes OpenJDK)
```

## Roadmap
- [x] Core Pipeline: End-to-End ELT with Airflow
- [x] RAG Integration: Vector Search with Qdrant & LangChain
- [x] Hybrid Cloud: Azure Database deployment via Terraform
- [x] Big Data Engine: Apache Spark Integration
- [ ] Kubernetes: Helm Chart deployment

---

## Developer Spotlight

**Nahasat Nibir** — Building intelligent, high‑performance developer tools and AI‑powered systems in Go and Python.

- GitHub: https://github.com/Nibir1
- LinkedIn: https://www.linkedin.com/in/nibir-1/
- ArtStation: https://www.artstation.com/nibir

---