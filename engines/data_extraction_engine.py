# data_extraction_engine.py

import os
import json
import time
import sqlite3
import re
from datetime import datetime

class DataExtractionEngine:
    def __init__(self):
        self.extraction_queue_path = "data/extraction"
        self.submission_queue_path = "data/submission"
        self.db_path = "db/submission_store.db"
        
        # Create necessary directories
        os.makedirs(self.extraction_queue_path, exist_ok=True)
        os.makedirs(self.submission_queue_path, exist_ok=True)
        os.makedirs("db", exist_ok=True)
        
        self.init_database()
        self.load_extraction_templates()

    def init_database(self):
        """Initialize submission store database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS submission_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                submission_id TEXT,
                processing_id TEXT,
                document_type TEXT,
                extracted_data TEXT,
                confidence_score REAL,
                timestamp TEXT,
                status TEXT
            )
        ''')
        
        conn.commit()
        conn.close()

    def load_extraction_templates(self):
        """Load data extraction templates for different document types"""
        self.extraction_templates = {
            "insurance_policy": {
                "fields": [
                    {"name": "policy_number", "patterns": [r"policy\s+number[:\s]+([A-Z0-9-]+)", r"policy[:\s]+([A-Z0-9-]+)"]},
                    {"name": "policyholder", "patterns": [r"policyholder[:\s]+([A-Za-z\s]+)", r"insured[:\s]+([A-Za-z\s]+)"]},
                    {"name": "coverage_type", "patterns": [r"coverage[:\s]+([A-Za-z\s]+)", r"insurance[:\s]+([A-Za-z\s]+)"]},
                    {"name": "premium", "patterns": [r"premium[:\s]+\$?([0-9,]+)", r"cost[:\s]+\$?([0-9,]+)"]},
                    {"name": "deductible", "patterns": [r"deductible[:\s]+\$?([0-9,]+)"]}
                ]
            },
            "claim_form": {
                "fields": [
                    {"name": "claim_number", "patterns": [r"claim\s+number[:\s]+([A-Z0-9-]+)", r"claim[:\s]+([A-Z0-9-]+)"]},
                    {"name": "incident_date", "patterns": [r"date\s+of\s+incident[:\s]+([0-9/-]+)", r"incident\s+date[:\s]+([0-9/-]+)"]},
                    {"name": "damage_amount", "patterns": [r"damage[:\s]+\$?([0-9,]+)", r"estimated[:\s]+\$?([0-9,]+)"]},
                    {"name": "claimant", "patterns": [r"claimant[:\s]+([A-Za-z\s]+)", r"name[:\s]+([A-Za-z\s]+)"]}
                ]
            }
        }

    def extract_data_from_text(self, text, document_type):
        """Extract structured data from text based on document type"""
        extracted_data = {}
        
        if document_type not in self.extraction_templates:
            return extracted_data
        
        template = self.extraction_templates[document_type]
        
        for field in template["fields"]:
            field_name = field["name"]
            extracted_data[field_name] = None
            
            for pattern in field["patterns"]:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    extracted_data[field_name] = match.group(1).strip()
                    break
        
        return extracted_data

    def calculate_extraction_confidence(self, extracted_data):
        """Calculate confidence score based on extracted fields"""
        total_fields = len(extracted_data)
        filled_fields = sum(1 for value in extracted_data.values() if value is not None)
        
        if total_fields == 0:
            return 0.0
        
        return (filled_fields / total_fields) * 100

    def store_extraction_result(self, submission_id, processing_id, document_type, extracted_data, confidence):
        """Store extraction result in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        extracted_data_json = json.dumps(extracted_data)
        
        cursor.execute('''
            INSERT INTO submission_data 
            (submission_id, processing_id, document_type, extracted_data, confidence_score, timestamp, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (submission_id, processing_id, document_type, extracted_data_json, confidence, datetime.now().isoformat(), 'extracted'))
        
        conn.commit()
        conn.close()

    def send_to_matching_engine(self, submission_id, processing_id, document_type, extracted_data):
        """Send extracted data to matching/rule engine"""
        matching_data = {
            "submission_id": submission_id,
            "processing_id": processing_id,
            "document_type": document_type,
            "extracted_data": extracted_data,
            "timestamp": datetime.now().isoformat(),
            "source": "data_extraction_engine",
            "status": "pending"
        }
        
        request_file = os.path.join(self.submission_queue_path, f"extracted_{submission_id}.json")
        
        with open(request_file, 'w') as f:
            json.dump(matching_data, f, indent=2)
        
        print(f"Sent to matching engine: {request_file}")

    def process_extraction_requests(self):
        """Process extraction requests from classifier engine"""
        print("Data Extraction Engine started - Monitoring for requests...")
        
        while True:
            try:
                # Check for new extraction requests
                if os.path.exists(self.extraction_queue_path):
                    for filename in os.listdir(self.extraction_queue_path):
                        if filename.startswith("classified_") and filename.endswith(".json"):
                            request_file = os.path.join(self.extraction_queue_path, filename)
                            
                            try:
                                with open(request_file, 'r') as f:
                                    request_data = json.load(f)
                                
                                processing_id = request_data.get("processing_id", "unknown")
                                document_type = request_data.get("document_type", "unknown")
                                extracted_text = request_data.get("extracted_text", "")
                                
                                if extracted_text and document_type != "unknown":
                                    print(f"Extracting data from {document_type}: {processing_id}")
                                    
                                    # Extract structured data
                                    extracted_data = self.extract_data_from_text(extracted_text, document_type)
                                    
                                    # Calculate confidence
                                    confidence = self.calculate_extraction_confidence(extracted_data)
                                    
                                    # Generate submission ID
                                    submission_id = f"SUB_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                                    
                                    # Store result
                                    self.store_extraction_result(submission_id, processing_id, document_type, extracted_data, confidence)
                                    
                                    # Send to matching engine
                                    self.send_to_matching_engine(submission_id, processing_id, document_type, extracted_data)
                                    
                                    print(f"Data extraction completed: {submission_id} (confidence: {confidence:.1f}%)")
                                    print(f"Extracted data: {extracted_data}")
                                    
                                    # Remove processed request
                                    os.remove(request_file)
                                
                            except Exception as e:
                                print(f"Error processing {request_file}: {e}")
                
                time.sleep(2)  # Check every 2 seconds
                
            except KeyboardInterrupt:
                print("Data Extraction Engine stopped")
                break
            except Exception as e:
                print(f"Data Extraction error: {e}")
                time.sleep(5)

if __name__ == "__main__":
    extractor = DataExtractionEngine()
    extractor.process_extraction_requests()