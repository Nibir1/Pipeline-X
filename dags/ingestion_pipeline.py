"""
dags/ingestion_pipeline.py

Role: Master Orchestrator (Hybrid Cloud Edition)
Description:
    This DAG defines the end-to-end workflow for Pipeline-X.
    
    Architecture:
    1. Ingestion: Extract Mock Data -> Upload to Azure Data Lake (Landing Zone)
    2. Stream A (SQL): Pandas Transform -> Azure PostgreSQL
    3. Stream B (AI): LangChain Chunking -> Qdrant Vector Store
    4. Stream C (Big Data): PySpark Job -> Process Parquet in Azure Data Lake
"""

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.utils.dates import days_ago
from datetime import timedelta
import pandas as pd
import json
import os
from azure.storage.blob import BlobServiceClient

# Import our custom modules
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

def _extract_and_upload_to_cloud(**kwargs):
    """
    Task 1: Fetch raw data and Upload to Azure Data Lake (Landing Zone).
    """
    # 1. Generate Mock Data
    print("[EXTRACT] Generating data...")
    extractor = DataExtractor(num_records=100) # Increased scale for demo
    data = extractor.extract()
    
    # 2. Save locally temporarily (Buffer)
    local_filename = "raw_data.json"
    local_path = f"/opt/airflow/logs/{local_filename}"
    
    with open(local_path, 'w') as f:
        json.dump(data, f)
        
    # 3. Upload to Azure Data Lake
    # We use the Blob Service Client to put the file into the 'raw-landing-zone' container
    try:
        account_name = os.getenv('AZURE_STORAGE_ACCOUNT_NAME')
        account_key = os.getenv('AZURE_STORAGE_ACCOUNT_KEY')
        
        if not account_name or not account_key:
            print("[WARN] Cloud credentials missing. Skipping Cloud Upload (Running Local Mode).")
            # In Local Mode, we just leave the file on disk for Spark to find
        else:
            print(f"[CLOUD] Connecting to Azure Storage: {account_name}...")
            connect_str = f"DefaultEndpointsProtocol=https;AccountName={account_name};AccountKey={account_key};EndpointSuffix=core.windows.net"
            blob_service_client = BlobServiceClient.from_connection_string(connect_str)
            
            # Create container if not exists
            container_name = "raw-landing-zone"
            try:
                blob_service_client.create_container(container_name)
            except Exception:
                pass # Container likely exists
                
            # Upload Blob
            blob_client = blob_service_client.get_blob_client(container=container_name, blob=local_filename)
            with open(local_path, "rb") as data_file:
                blob_client.upload_blob(data_file, overwrite=True)
                
            print(f"[CLOUD] ✅ Successfully uploaded {local_filename} to Azure container '{container_name}'")

    except Exception as e:
        print(f"[ERROR] Failed to upload to Azure: {e}")
        # We don't raise an error here to allow the Local/SQL parts of the pipeline to continue
        # even if the Cloud connection fails (Graceful Degradation)

    return data

def _transform_metadata(ti, **kwargs):
    """
    Task 2: Clean metadata for SQL.
    Input: Raw data from Task 1 (via XCom).
    """
    raw_data = ti.xcom_pull(task_ids='extract_data')
    
    transformer = DataTransformer()
    df = transformer.process_metadata(raw_data)
    
    # Serialization Fix for Airflow XCom
    if 'created_at' in df.columns:
        df['created_at'] = df['created_at'].astype(str)

    return df.to_dict(orient='records')

def _load_postgres(ti, **kwargs):
    """
    Task 3: Load metadata to Postgres (Azure or Local).
    """
    clean_data_list = ti.xcom_pull(task_ids='transform_metadata')
    
    if not clean_data_list:
        print("No data to load.")
        return

    df = pd.DataFrame(clean_data_list)
    
    db = DatabaseConnector()
    db.init_db_schema() 
    db.save_metadata_to_postgres(df)

def _vectorize_content(ti, **kwargs):
    """
    Task 4: Chunk and Embed text for AI.
    """
    raw_data = ti.xcom_pull(task_ids='extract_data')
    
    # LangChain Chunking
    chunker = TextChunker()
    chunks = chunker.chunk_documents(raw_data)
    
    # Sentence-Transformers Embedding
    embedder = TextEmbedder()
    enriched_chunks = embedder.embed_chunks(chunks)
    
    return enriched_chunks

def _index_vectors(ti, **kwargs):
    """
    Task 5: Upsert vectors to Qdrant.
    """
    vectors = ti.xcom_pull(task_ids='vectorize_content')
    
    db = DatabaseConnector()
    db.init_db_schema()
    db.save_vectors_to_qdrant(vectors)

# ---------------------------------------------------------
# DAG DEFINITION
# ---------------------------------------------------------
with DAG(
    'pipeline_x_ingestion',
    default_args=default_args,
    description='Hybrid Cloud ELT: Azure Data Lake + Spark + Vector RAG',
    schedule_interval='@daily',
    start_date=days_ago(1),
    tags=['elt', 'ai', 'azure', 'spark'],
    catchup=False
) as dag:

    # 1. Ingestion (Cloud Landing Zone)
    t1_extract = PythonOperator(
        task_id='extract_data',
        python_callable=_extract_and_upload_to_cloud
    )

    # -----------------------------------------------------
    # STREAM A: SQL ANALYTICS
    # -----------------------------------------------------
    t2_transform_sql = PythonOperator(
        task_id='transform_metadata',
        python_callable=_transform_metadata
    )

    t3_load_sql = PythonOperator(
        task_id='load_postgres',
        python_callable=_load_postgres
    )

    # -----------------------------------------------------
    # STREAM B: AI RAG
    # -----------------------------------------------------
    t4_vectorize = PythonOperator(
        task_id='vectorize_content',
        python_callable=_vectorize_content
    )

    t5_index_vectors = PythonOperator(
        task_id='index_vectors',
        python_callable=_index_vectors
    )

    # -----------------------------------------------------
    # STREAM C: BIG DATA (Spark)
    # -----------------------------------------------------
    # Triggers the PySpark script which reads from Azure and processes data
    t6_spark_job = BashOperator(
        task_id='spark_transform_job',
        bash_command='python /opt/airflow/src/etl/spark_transformer.py'
    )

    # -----------------------------------------------------
    # DEPENDENCIES
    # -----------------------------------------------------
    
    # All streams wait for data to land in the cloud
    t1_extract >> t2_transform_sql >> t3_load_sql
    t1_extract >> t4_vectorize >> t5_index_vectors
    t1_extract >> t6_spark_job