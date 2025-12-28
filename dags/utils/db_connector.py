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
import io
from sqlalchemy import create_engine, text
from qdrant_client import QdrantClient
from qdrant_client.http import models
from dotenv import load_dotenv

# Load environment variables
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
        self.pg_host = os.getenv("POSTGRES_HOST", "postgres")
        self.pg_port = os.getenv("POSTGRES_PORT", "5432")
        self.pg_db = os.getenv("POSTGRES_DB", "airflow")
        
        self.pg_url = f"postgresql+psycopg2://{self.pg_user}:{self.pg_pass}@{self.pg_host}:{self.pg_port}/{self.pg_db}"
        self.pg_engine = create_engine(self.pg_url)

        # ---------------------------------------------------------
        # QDRANT CONFIGURATION
        # ---------------------------------------------------------
        self.qdrant_host = os.getenv("QDRANT_HOST", "qdrant")
        self.qdrant_port = int(os.getenv("QDRANT_PORT", 6333))
        self.qdrant_client = QdrantClient(host=self.qdrant_host, port=self.qdrant_port)
        
        self.collection_name = "pipeline_x_docs"
        self.vector_size = 384 

    def init_db_schema(self):
        """
        Ensures target tables and collections exist.
        """
        print("[DB CONNECTOR] Initializing database schemas...")

        # 1. Postgres: Create Analytics Table
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
        
        # FIX: Use engine.begin() which auto-commits on exit.
        with self.pg_engine.begin() as conn:
            conn.execute(text(create_table_sql))
            print("[DB CONNECTOR] Postgres table 'analytics_metadata' checked/created.")

        # 2. Qdrant: Create Collection
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
        Saves the Pandas DataFrame to Postgres using the Manual COPY pattern.
        This bypasses pandas.to_sql entirely to avoid version conflicts.
        """
        if df.empty:
            print("[DB CONNECTOR] No metadata to save.")
            return

        print(f"[DB CONNECTOR] Saving {len(df)} rows to Postgres...")
        staging_table = 'staging_analytics_metadata'
        
        # Get raw connection to use COPY
        raw_conn = self.pg_engine.raw_connection()
        
        try:
            with raw_conn.cursor() as cur:
                # 1. Create Staging Table Manually
                cur.execute(f"""
                    CREATE TABLE IF NOT EXISTS {staging_table} (
                        id VARCHAR(50),
                        title TEXT,
                        author VARCHAR(100),
                        created_at TIMESTAMP,
                        category VARCHAR(50)
                    )
                """)
                cur.execute(f"TRUNCATE TABLE {staging_table}") # Ensure it's empty
                
                # 2. Convert DataFrame to CSV in memory
                output = io.StringIO()
                # Ensure column order matches table definition exactly
                df[['id', 'title', 'author', 'created_at', 'category']].to_csv(output, sep='\t', header=False, index=False)
                output.seek(0)
                
                # 3. Use COPY expert to load data (Fastest method)
                cur.copy_expert(f"COPY {staging_table} FROM STDIN", output)
                print("[DB CONNECTOR] Staging table loaded via COPY.")

                # 4. Upsert from Staging to Production
                upsert_sql = f"""
                INSERT INTO analytics_metadata (id, title, author, created_at, category)
                SELECT id, title, author, created_at, category 
                FROM {staging_table}
                ON CONFLICT (id) DO UPDATE 
                SET title = EXCLUDED.title,
                    author = EXCLUDED.author,
                    category = EXCLUDED.category;
                """
                cur.execute(upsert_sql)
                
                # 5. Cleanup
                cur.execute(f"DROP TABLE IF EXISTS {staging_table}")
            
            raw_conn.commit()
            print("[DB CONNECTOR] Metadata saved successfully (Upsert complete).")
            
        except Exception as e:
            raw_conn.rollback()
            print(f"[DB CONNECTOR] Error saving metadata: {e}")
            raise e
        finally:
            raw_conn.close()

    def save_vectors_to_qdrant(self, chunks: list):
        """
        Upserts vectors to Qdrant.
        """
        if not chunks:
            print("[DB CONNECTOR] No vectors to save.")
            return

        print(f"[DB CONNECTOR] Upserting {len(chunks)} vectors to Qdrant...")
        
        points = []
        import uuid
        
        for chunk in chunks:
            # Generate a deterministic ID based on doc_id and chunk_index
            point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{chunk['doc_id']}_{chunk['chunk_index']}"))
            
            points.append(models.PointStruct(
                id=point_id,
                vector=chunk['vector'],
                payload=chunk['metadata']
            ))

        self.qdrant_client.upsert(
            collection_name=self.collection_name,
            points=points
        )
        print("[DB CONNECTOR] Vectors upserted successfully.")