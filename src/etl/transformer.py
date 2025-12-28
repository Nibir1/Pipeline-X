"""
src/etl/transformer.py

Role: Data Cleaning & Normalization
Description:
    This module handles the 'T' in ELT. It uses Pandas to clean raw data.
    It prepares the data for two destinations:
    1. Metadata -> SQL Database (Postgres)
    2. Content  -> Vector Store (Qdrant)
"""

import pandas as pd
from typing import List, Dict, Any

class DataTransformer:
    """
    Handles data cleaning and transformation using Pandas.
    """

    def __init__(self):
        pass

    def process_metadata(self, raw_data: List[Dict[str, Any]]) -> pd.DataFrame:
        """
        Converts raw list of dicts into a clean Pandas DataFrame for SQL storage.
        
        Steps:
        1. Convert to DataFrame.
        2. Convert 'created_at' to actual datetime objects.
        3. Standardize author names (uppercase).
        4. Select only relevant columns for the Data Warehouse.
        
        Args:
            raw_data (List[Dict]): The output from the Extractor.
            
        Returns:
            pd.DataFrame: A clean dataframe ready for Postgres insertion.
        """
        print("[TRANSFORMER] Processing metadata...")
        
        if not raw_data:
            print("[TRANSFORMER] No data to process.")
            return pd.DataFrame()

        df = pd.DataFrame(raw_data)

        # 1. Date Standardization
        df['created_at'] = pd.to_datetime(df['created_at'])

        # 2. String Normalization (Author names)
        df['author'] = df['author'].str.strip().str.title()

        # 3. Handle Missing Values (Imputation)
        df['category'] = df['category'].fillna('Uncategorized')

        # 4. Filter columns for SQL (We don't need the full text blob in SQL metadata table)
        # We keep 'content' in the dataframe temporarily if needed, but for SQL we pick specific columns
        metadata_df = df[['id', 'title', 'author', 'created_at', 'category']]

        print(f"[TRANSFORMER] Processed {len(metadata_df)} records for SQL.")
        return metadata_df

# Quick test block
if __name__ == "__main__":
    # Mock input
    sample_data = [{
        "id": "1", "title": "Test", "author": "bob ", 
        "created_at": "2024-01-01T10:00:00", "category": "Finance", "content": "..."
    }]
    transformer = DataTransformer()
    print(transformer.process_metadata(sample_data))