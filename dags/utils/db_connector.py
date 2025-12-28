"""
dags/utils/db_connector.py

Role: Database Interaction Layer
Description:
    Unified connector for Postgres (via COPY) and Qdrant.
"""

import os
import pandas as pd
import io
import uuid
from sqlalchemy import create_engine, text
from qdrant_client import QdrantClient
from qdrant_client.http import models
from dotenv import load_dotenv

load_dotenv()

class DatabaseConnector:
    """
    Unified connector for Postgres and Qdrant.
    """

    def __init__(self):
        # POSTGRES
        self.pg_user = os.getenv("POSTGRES_USER", "airflow")
        self.pg_pass = os.getenv("POSTGRES_PASSWORD", "airflow")
        self.pg_host = os.getenv("POSTGRES_HOST", "postgres")
        self.pg_port = os.getenv("POSTGRES_PORT", "5432")
        self.pg_db = os.getenv("POSTGRES_DB", "airflow")
        self.pg_url = f"postgresql+psycopg2://{self.pg_user}:{self.pg_pass}@{self.pg_host}:{self.pg_port}/{self.pg_db}"
        self.pg_engine = create_engine(self.pg_url)

        # QDRANT
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

        # 1. Postgres Table
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
        with self.pg_engine.begin() as conn:
            conn.execute(text(create_table_sql))

        # 2. Qdrant Collection
        if not self.qdrant_client.collection_exists(self.collection_name):
            print(f"[DB CONNECTOR] Creating Qdrant collection '{self.collection_name}'...")
            self.qdrant_client.create_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(
                    size=self.vector_size,
                    distance=models.Distance.COSINE
                )
            )
        else:
            print(f"[DB CONNECTOR] Qdrant collection '{self.collection_name}' exists.")

    def save_metadata_to_postgres(self, df: pd.DataFrame):
        """
        Saves metadata using efficient Postgres COPY protocol.
        """
        if df.empty:
            return

        print(f"[DB CONNECTOR] Saving {len(df)} rows to Postgres...")
        staging_table = 'staging_analytics_metadata'
        raw_conn = self.pg_engine.raw_connection()
        
        try:
            with raw_conn.cursor() as cur:
                # Create Staging
                cur.execute(f"""
                    CREATE TABLE IF NOT EXISTS {staging_table} (
                        id VARCHAR(50), title TEXT, author VARCHAR(100), 
                        created_at TIMESTAMP, category VARCHAR(50)
                    )
                """)
                cur.execute(f"TRUNCATE TABLE {staging_table}")
                
                # Buffer Data
                output = io.StringIO()
                df[['id', 'title', 'author', 'created_at', 'category']].to_csv(output, sep='\t', header=False, index=False)
                output.seek(0)
                
                # COPY
                cur.copy_expert(f"COPY {staging_table} FROM STDIN", output)

                # Upsert
                upsert_sql = f"""
                INSERT INTO analytics_metadata (id, title, author, created_at, category)
                SELECT id, title, author, created_at, category FROM {staging_table}
                ON CONFLICT (id) DO UPDATE 
                SET title = EXCLUDED.title, author = EXCLUDED.author, category = EXCLUDED.category;
                """
                cur.execute(upsert_sql)
                cur.execute(f"DROP TABLE IF EXISTS {staging_table}")
            
            raw_conn.commit()
            print("[DB CONNECTOR] Metadata saved successfully.")
            
        except Exception as e:
            raw_conn.rollback()
            raise e
        finally:
            raw_conn.close()

    def save_vectors_to_qdrant(self, chunks: list):
        """
        Upserts vectors to Qdrant.
        """
        if not chunks:
            return

        print(f"[DB CONNECTOR] Upserting {len(chunks)} vectors to Qdrant...")
        
        points = []
        for chunk in chunks:
            point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{chunk['doc_id']}_{chunk['chunk_index']}"))
            
            # Ensure metadata is flat and serializable
            payload = chunk.get('metadata', {}).copy()
            # Explicitly ensure page_content is there (though chunker puts it in metadata now)
            if 'page_content' not in payload:
                payload['page_content'] = chunk.get('text', '')

            points.append(models.PointStruct(
                id=point_id,
                vector=chunk['vector'],
                payload=payload 
            ))

        self.qdrant_client.upsert(
            collection_name=self.collection_name,
            points=points
        )
        print("[DB CONNECTOR] Vectors upserted successfully.")