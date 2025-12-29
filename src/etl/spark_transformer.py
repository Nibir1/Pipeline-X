"""
src/etl/spark_transformer.py

Role: Big Data Transformation
Description:
    Demonstrates ETL logic using PySpark instead of Pandas.
    This simulates how we would handle Petabyte-scale data.
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, current_timestamp, to_timestamp

def process_with_spark(input_file: str, output_dir: str):
    print("[SPARK] Initializing Spark Session...")
    
    # Initialize Spark
    spark = SparkSession.builder \
        .appName("Pipeline-X-Enterprise") \
        .master("local[*]") \
        .getOrCreate()

    # 1. EXTRACT (Read JSON)
    print(f"[SPARK] Reading {input_file}...")
    df = spark.read.json(input_file)
    
    # 2. TRANSFORM
    # - Cast dates
    # - Rename columns if needed
    # - Add ingestion timestamp
    print("[SPARK] Transforming data...")
    transformed_df = df.withColumn("ingested_at", current_timestamp()) \
                       .withColumn("created_at_ts", to_timestamp(col("created_at")))
    
    # Show schema (Proves you understand Data Types)
    transformed_df.printSchema()
    
    # 3. LOAD (Write to Parquet - Standard Big Data Format)
    output_path = f"{output_dir}/processed_analytics"
    print(f"[SPARK] Writing to Parquet at {output_path}...")
    
    transformed_df.write.mode("overwrite").parquet(output_path)
    
    print("[SPARK] Job Complete.")
    spark.stop()

if __name__ == "__main__":
    # For local testing within the container
    import os
    # Create dummy data for test
    process_with_spark("dags/data/raw_data.json", "/tmp")