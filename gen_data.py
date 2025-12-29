import json
import os
from src.etl.extractor import DataExtractor

# 1. Generate Data
data = DataExtractor().extract()

# 2. Ensure Directory Exists
os.makedirs('dags/data', exist_ok=True)

# 3. Save to JSON
with open('dags/data/raw_data.json', 'w') as f:
    json.dump(data, f)

print("✅ Data generated successfully.")