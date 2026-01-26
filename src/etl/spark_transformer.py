"""
src/etl/spark_transformer.py

Role: Big Data Transformation Engine (Hybrid Cloud)
Description:
    Demonstrates Enterprise ETL logic using Apache Spark (PySpark).
    
    Production Capabilities:
    1. Hybrid Execution: Switches between Local Storage and Azure Data Lake.
    2. Self-Healing: Automatically creates missing Cloud Containers (Infrastructure as Code).
    3. Dependency Injection: Manually injects Hadoop-Azure JARs.
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, current_timestamp, to_timestamp, lit
from azure.storage.blob import BlobServiceClient # <--- Added for infrastructure management
import sys
import os

# ---------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------
APP_NAME = "Pipeline-X-Enterprise-ETL"

# Load Cloud Credentials
STORAGE_ACCOUNT = os.getenv("AZURE_STORAGE_ACCOUNT_NAME")
STORAGE_KEY = os.getenv("AZURE_STORAGE_ACCOUNT_KEY")

# JAR Paths (Must match where we downloaded them in Dockerfile)
AZURE_JARS = "/opt/spark-jars/hadoop-azure-3.3.4.jar,/opt/spark-jars/azure-storage-8.6.6.jar"

# Container Names
INPUT_CONTAINER = "raw-landing-zone"
OUTPUT_CONTAINER = "processed-data"

def ensure_azure_container_exists(container_name):
    """
    Uses the Azure SDK to create the container if it doesn't exist.
    This prevents Spark from crashing with 'Filesystem does not exist'.
    """
    try:
        print(f"[INFRA] Checking if container '{container_name}' exists...")
        connect_str = f"DefaultEndpointsProtocol=https;AccountName={STORAGE_ACCOUNT};AccountKey={STORAGE_KEY};EndpointSuffix=core.windows.net"
        blob_service_client = BlobServiceClient.from_connection_string(connect_str)
        
        container_client = blob_service_client.get_container_client(container_name)
        if not container_client.exists():
            container_client.create_container()
            print(f"[INFRA] ✅ Created missing container: {container_name}")
        else:
            print(f"[INFRA] Container '{container_name}' already exists.")
            
    except Exception as e:
        print(f"[WARN] Failed to check/create container. Spark might fail. Error: {e}")

def get_io_paths():
    """
    Determines if we are running in Cloud Mode (Azure) or Local Mode (Docker).
    """
    if STORAGE_ACCOUNT and STORAGE_KEY:
        print(f"[CONFIG] Detected Azure Credentials. Target: {STORAGE_ACCOUNT}")
        
        # Ensure the Output Container exists before Spark starts!
        ensure_azure_container_exists(OUTPUT_CONTAINER)
        
        inp = f"abfss://{INPUT_CONTAINER}@{STORAGE_ACCOUNT}.dfs.core.windows.net/raw_data.json"
        out = f"abfss://{OUTPUT_CONTAINER}@{STORAGE_ACCOUNT}.dfs.core.windows.net/analytics"
        return inp, out, True
    else:
        print("[CONFIG] No Cloud credentials found. Using Local Storage.")
        inp = "/opt/airflow/logs/raw_data.json"
        out = "/opt/airflow/logs/processed_lake"
        return inp, out, False

def process_with_spark():
    input_path, output_path, is_cloud_mode = get_io_paths()
    
    print(f"[SPARK] Starting Job: {APP_NAME}")
    
    # 1. INITIALIZE SESSION
    builder = SparkSession.builder \
        .appName(APP_NAME) \
        .master("local[*]") \
        .config("spark.driver.memory", "1g") \
        .config("spark.jars", AZURE_JARS)
    
    # If Cloud, inject the Authentication Key
    if is_cloud_mode:
        builder = builder.config(
            f"spark.hadoop.fs.azure.account.key.{STORAGE_ACCOUNT}.dfs.core.windows.net", 
            STORAGE_KEY
        )
        
    spark = builder.getOrCreate()
    spark.sparkContext.setLogLevel("WARN")

    # 2. EXTRACT
    print(f"[SPARK] Reading from: {input_path}")
    try:
        df = spark.read.json(input_path)
    except Exception as e:
        print(f"[ERROR] Spark Read Failed. Error: {e}")
        sys.exit(1)

    print(f"[SPARK] Raw Record Count: {df.count()}")
    
    # 3. TRANSFORM
    print("[SPARK] Applying transformations...")
    clean_df = df.withColumn("ingested_at", current_timestamp()) \
                 .withColumn("source_system", lit("Pipeline-X-Cloud-Ingestor"))
    
    if "created_at" in df.columns:
        clean_df = clean_df.withColumn("event_time", to_timestamp(col("created_at")))

    # 4. LOAD
    print(f"[SPARK] Writing processed data to: {output_path}")
    clean_df.write.mode("overwrite").parquet(output_path)
    
    print(f"[SPARK] ✅ Job Finished. Data Lake Updated.")
    spark.stop()

if __name__ == "__main__":
    process_with_spark()