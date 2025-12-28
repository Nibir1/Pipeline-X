"""
dags/utils/db_connector.py

Role: Database Interaction Layer
Description:
    This module handles all external connections to storage systems.
    It encapsulates the logic for:
    1. Connecting to Postgres (via SQLAlchemy).
    2. Connecting to Qdrant (via QdrantClient).
    3. Creating necessary tables/collections if they don't exist.
"""

import os
import pandas as pd
from sqlalchemy import create_engine, text
from qdrant_client import QdrantClient
from qdrant_client.http import models
from dotenv import load_dotenv

# Load environment variables (useful if running locally outside Docker)
load_dotenv()

class DatabaseConnector:
    """
    Unified connector for Postgres and Qdrant.
    """

    def __init__(self):
        # ---------------------------------------------------------
        # POSTGRES CONFIGURATION
        # ---------------------------------------------------------
        self.pg_user = os.getenv("POSTGRES_USER", "airflow")
        self.pg_pass = os.getenv("POSTGRES_PASSWORD", "airflow")
        self.pg_host = os.getenv("POSTGRES_HOST", "postgres") # 'postgres' is the docker service name
        self.pg_port = os.getenv("POSTGRES_PORT", "5432")
        self.pg_db = os.getenv("POSTGRES_DB", "airflow")
        
        # Connection String: postgresql+psycopg2://user:pass@host:port/db
        self.pg_url = f"postgresql+psycopg2://{self.pg_user}:{self.pg_pass}@{self.pg_host}:{self.pg_port}/{self.pg_db}"
        self.pg_engine = create_engine(self.pg_url)

        # ---------------------------------------------------------
        # QDRANT CONFIGURATION
        # ---------------------------------------------------------
        self.qdrant_host = os.getenv("QDRANT_HOST", "qdrant")
        self.qdrant_port = int(os.getenv("QDRANT_PORT", 6333))
        self.qdrant_client = QdrantClient(host=self.qdrant_host, port=self.qdrant_port)
        
        # Vector Config
        self.collection_name = "pipeline_x_docs"
        self.vector_size = 384 # Matches all-MiniLM-L6-v2 dimensions

    def init_db_schema(self):
        """
        Ensures target tables and collections exist.
        """
        print("[DB CONNECTOR] Initializing database schemas...")

        # 1. Postgres: Create Analytics Table if not exists
        # We use a raw SQL execution for table creation to ensure constraints
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS analytics_metadata (
            id VARCHAR(50) PRIMARY KEY,
            title TEXT,
            author VARCHAR(100),
            created_at TIMESTAMP,
            category VARCHAR(50),
            ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        with self.pg_engine.connect() as conn:
            conn.execute(text(create_table_sql))
            print("[DB CONNECTOR] Postgres table 'analytics_metadata' checked/created.")

        # 2. Qdrant: Create Collection if not exists
        try:
            self.qdrant_client.get_collection(self.collection_name)
            print(f"[DB CONNECTOR] Qdrant collection '{self.collection_name}' exists.")
        except Exception:
            print(f"[DB CONNECTOR] Creating Qdrant collection '{self.collection_name}'...")
            self.qdrant_client.create_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(
                    size=self.vector_size,
                    distance=models.Distance.COSINE
                )
            )

    def save_metadata_to_postgres(self, df: pd.DataFrame):
        """
        Saves the Pandas DataFrame to Postgres.
        Uses 'append' mode but relies on the table's Primary Key to reject duplicates 
        (or we can handle it via an upsert in a more advanced version).
        
        For this simplified pipeline, we use 'to_sql' with error handling.
        """
        if df.empty:
            print("[DB CONNECTOR] No metadata to save.")
            return

        print(f"[DB CONNECTOR] Saving {len(df)} rows to Postgres...")
        
        # We write to a temp table first, then upsert to main table to handle duplicates gracefully
        # This is a common pattern to ensure Idempotency in SQL ELT
        with self.pg_engine.begin() as conn:
            # 1. Create Temp Table
            df.to_sql('temp_metadata', conn, if_exists='replace', index=False)
            
            # 2. Upsert (Insert ... ON CONFLICT DO NOTHING)
            # Note: This syntax is Postgres specific
            upsert_sql = """
            INSERT INTO analytics_metadata (id, title, author, created_at, category)
            SELECT id, title, author, created_at, category FROM temp_metadata
            ON CONFLICT (id) DO UPDATE 
            SET title = EXCLUDED.title,
                author = EXCLUDED.author,
                category = EXCLUDED.category;
            """
            conn.execute(text(upsert_sql))
            
            # 3. Clean up
            conn.execute(text("DROP TABLE temp_metadata"))
            
        print("[DB CONNECTOR] Metadata saved successfully (Upsert complete).")

    def save_vectors_to_qdrant(self, chunks: list):
        """
        Upserts vectors to Qdrant.
        """
        if not chunks:
            print("[DB CONNECTOR] No vectors to save.")
            return

        print(f"[DB CONNECTOR] Upserting {len(chunks)} vectors to Qdrant...")
        
        points = []
        for chunk in chunks:
            # Construct a PointStruct for each chunk
            # Point ID: We need a unique ID for the point. 
            # We can use UUIDs or a hash of the doc_id + chunk_index.
            # Using uuid provided by the chunker or generating one.
            import uuid
            
            points.append(models.PointStruct(
                id=str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{chunk['doc_id']}_{chunk['chunk_index']}")),
                vector=chunk['vector'],
                payload=chunk['metadata']  # Store metadata for retrieval filtering
            ))

        # Upsert is idempotent by default in Qdrant based on Point ID
        self.qdrant_client.upsert(
            collection_name=self.collection_name,
            points=points
        )
        print("[DB CONNECTOR] Vectors upserted successfully.")

# Quick test block
if __name__ == "__main__":
    # Note: This test assumes you are running 'docker-compose up' so the ports are exposed locally
    # If running from inside the container, this works automatically.
    # If running from your host machine, ensure 5432 and 6333 are mapped.
    
    try:
        connector = DatabaseConnector()
        connector.init_db_schema()
        print("Connection verification successful.")
    except Exception as e:
        print(f"Connection failed: {e}")
        print("Ensure Docker containers are running.")