"""
dags/ingestion_pipeline.py

Role: Master Orchestrator
Description:
    This DAG defines the end-to-end workflow for Pipeline-X.
    It schedules the extraction, transformation, and loading of business documents.

Data Flow:
    1. Extract (Mock) -> [Raw JSON]
    2. Transform (SQL) -> [Clean Metadata] -> Postgres
    3. Transform (AI)  -> [Chunks + Vectors] -> Qdrant
"""

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago
from datetime import timedelta
import pandas as pd
import json

# Import our custom modules (The "Logic" and "Connectivity" layers)
from src.etl.extractor import DataExtractor
from src.etl.transformer import DataTransformer
from src.ai.chunker import TextChunker
from src.ai.embedder import TextEmbedder
from dags.utils.db_connector import DatabaseConnector

# ---------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------
default_args = {
    'owner': 'pipeline-x',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# ---------------------------------------------------------
# TASK WRAPPERS (The "Glue" Logic)
# ---------------------------------------------------------

def _extract_data(**kwargs):
    """
    Task 1: Fetch raw data.
    Returns: List[Dict] (JSON serializable for XCom)
    """
    extractor = DataExtractor(num_records=10)
    data = extractor.extract()
    return data

def _transform_metadata(ti, **kwargs):
    """
    Task 2: Clean metadata for SQL.
    Input: Raw data from Task 1 (via XCom).
    Output: List[Dict] (Serialized DataFrame).
    """
    # Pull data from previous task
    raw_data = ti.xcom_pull(task_ids='extract_data')
    
    # Process
    transformer = DataTransformer()
    df = transformer.process_metadata(raw_data)
    
    # --- BUG FIX START ---
    # Convert 'created_at' Timestamp objects to Strings so JSON serialization works.
    if 'created_at' in df.columns:
        df['created_at'] = df['created_at'].astype(str)
    # --- BUG FIX END ---

    # Convert DataFrame to Dict for XCom serialization
    # 'orient=records' creates a list of dicts: [{'col': val}, ...]
    return df.to_dict(orient='records')

def _load_postgres(ti, **kwargs):
    """
    Task 3: Load metadata to Postgres.
    Input: Cleaned metadata from Task 2 (via XCom).
    """
    clean_data_list = ti.xcom_pull(task_ids='transform_metadata')
    
    if not clean_data_list:
        print("No data to load to Postgres.")
        return

    # Convert back to DataFrame for the connector
    df = pd.DataFrame(clean_data_list)
    
    # Load
    db = DatabaseConnector()
    db.init_db_schema() 
    db.save_metadata_to_postgres(df)

def _vectorize_content(ti, **kwargs):
    """
    Task 4: Chunk and Embed text for AI.
    Input: Raw data from Task 1 (via XCom).
    Output: List[Dict] (Chunks with vectors).
    """
    raw_data = ti.xcom_pull(task_ids='extract_data')
    
    # 1. Chunking
    chunker = TextChunker()
    chunks = chunker.chunk_documents(raw_data)
    
    # 2. Embedding
    embedder = TextEmbedder()
    enriched_chunks = embedder.embed_chunks(chunks)
    
    return enriched_chunks

def _index_vectors(ti, **kwargs):
    """
    Task 5: Upsert vectors to Qdrant.
    Input: Vectorized chunks from Task 4 (via XCom).
    """
    vectors = ti.xcom_pull(task_ids='vectorize_content')
    
    db = DatabaseConnector()
    db.init_db_schema() # Ensure collection exists
    db.save_vectors_to_qdrant(vectors)

# ---------------------------------------------------------
# DAG DEFINITION
# ---------------------------------------------------------
with DAG(
    'pipeline_x_ingestion',
    default_args=default_args,
    description='End-to-End Ingestion: Extract -> SQL + Vector Store',
    schedule_interval='@daily',
    start_date=days_ago(1),
    tags=['elt', 'ai', 'rag'],
    catchup=False
) as dag:

    # 1. Extraction Task
    t1_extract = PythonOperator(
        task_id='extract_data',
        python_callable=_extract_data
    )

    # 2. SQL Stream Tasks
    t2_transform_sql = PythonOperator(
        task_id='transform_metadata',
        python_callable=_transform_metadata
    )

    t3_load_sql = PythonOperator(
        task_id='load_postgres',
        python_callable=_load_postgres
    )

    # 3. AI Stream Tasks
    t4_vectorize = PythonOperator(
        task_id='vectorize_content',
        python_callable=_vectorize_content
    )

    t5_index_vectors = PythonOperator(
        task_id='index_vectors',
        python_callable=_index_vectors
    )

    # -----------------------------------------------------
    # DEPENDENCIES (The Graph Structure)
    # -----------------------------------------------------
    
    t1_extract >> t2_transform_sql >> t3_load_sql
    t1_extract >> t4_vectorize >> t5_index_vectors