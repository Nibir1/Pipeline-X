"""
src/etl/extractor.py

Role: Data Source Simulation
Description:
    This module simulates fetching raw data from an external source (e.g., an API or S3 bucket).
    Since we don't have a real upstream API, we generate realistic mock data (Business Reports).
    
    In a real scenario, this would use 'requests' or 'boto3'.
"""

import json
import random
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any

class DataExtractor:
    """
    Simulates the extraction of raw documents from a business system.
    """

    def __init__(self, num_records: int = 10):
        """
        Initialize the extractor.
        
        Args:
            num_records (int): The number of mock documents to generate per run.
        """
        self.num_records = num_records
        self.categories = ["Financial Report", "Technical Spec", "Meeting Minutes", "Project Plan"]
        self.authors = ["Alice Smith", "Bob Jones", "Charlie Day", "Dana Lee"]

    def _generate_content(self, category: str) -> str:
        """
        Helper to generate context-aware mock text content based on category.
        """
        if category == "Financial Report":
            return (
                f"The Q{random.randint(1,4)} revenue exceeded expectations by {random.randint(5, 20)}%. "
                "Key drivers included strong performance in the cloud sector and reduced operational costs. "
                "The board recommends a stock buyback program to increase shareholder value. "
                "Risks remain in the supply chain sector due to geopolitical instability."
            )
        elif category == "Technical Spec":
            return (
                "The new microservices architecture will utilize Kubernetes for orchestration. "
                "We are migrating from a monolithic SQL database to a sharded NoSQL solution. "
                "Latency requirements are strict: 99th percentile must be under 50ms. "
                "All internal communication will happen via gRPC protected by mTLS."
            )
        else:
            return (
                "This is a general internal document regarding operational efficiency. "
                "Employees are reminded to complete their compliance training by end of month. "
                "The cafeteria menu will be updated starting next week to include more vegan options."
            )

    def extract(self) -> List[Dict[str, Any]]:
        """
        Main method to 'fetch' data.
        
        Returns:
            List[Dict]: A list of raw document dictionaries.
        """
        print(f"[EXTRACTOR] Generating {self.num_records} mock documents...")
        data = []

        for _ in range(self.num_records):
            category = random.choice(self.categories)
            doc = {
                "id": str(uuid.uuid4()),
                "title": f"{category} - {datetime.now().year}",
                "author": random.choice(self.authors),
                "created_at": (datetime.now() - timedelta(days=random.randint(0, 30))).isoformat(),
                "category": category,
                "content": self._generate_content(category),
                "raw_metadata": {"source": "legacy_system_v1", "priority": "high"}
            }
            data.append(doc)
        
        print(f"[EXTRACTOR] Successfully generated {len(data)} documents.")
        return data

# Quick test block to verify the code works if run directly
if __name__ == "__main__":
    extractor = DataExtractor(num_records=2)
    print(json.dumps(extractor.extract(), indent=2))