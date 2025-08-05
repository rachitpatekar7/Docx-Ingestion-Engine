# classifier_engine.py

import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report
import joblib
import os
import json
import time
import sqlite3
from datetime import datetime
import re

class ClassifierEngine:
    def __init__(self, data_path):
        self.data_path = data_path
        self.model = RandomForestClassifier()
        self.classifier_queue_path = "data/classifier"
        self.extraction_queue_path = "data/extraction"
        self.db_path = "db/classifier_store.db"
        
        # Create necessary directories
        os.makedirs(self.extraction_queue_path, exist_ok=True)
        os.makedirs("db", exist_ok=True)
        
        self.init_database()
        self.load_classification_rules()

    def load_data(self):
        data = pd.read_csv(self.data_path)
        return data

    def preprocess_data(self, data):
        # Implement preprocessing steps here
        # For example, handling missing values, encoding categorical variables, etc.
        return data

    def train_model(self, data):
        X = data.drop('target', axis=1)  # Assuming 'target' is the label column
        y = data['target']
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        self.model.fit(X_train, y_train)
        predictions = self.model.predict(X_test)
        
        print(classification_report(y_test, predictions))

    def save_model(self, model_path):
        joblib.dump(self.model, model_path)

    def load_model(self, model_path):
        self.model = joblib.load(model_path)

    def predict(self, input_data):
        return self.model.predict(input_data)

    def init_database(self):
        """Initialize classifier results database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS classification_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                processing_id TEXT,
                file_uri TEXT,
                document_type TEXT,
                tags TEXT,
                confidence_score REAL,
                timestamp TEXT,
                status TEXT
            )
        ''')
        
        conn.commit()
        conn.close()

    def load_classification_rules(self):
        """Load document classification rules"""
        self.classification_rules = {
            "insurance_policy": {
                "keywords": ["policy", "coverage", "premium", "policyholder", "insurance"],
                "patterns": [r"policy\s+number", r"coverage\s+amount", r"premium", r"deductible"]
            },
            "claim_form": {
                "keywords": ["claim", "incident", "damage", "accident", "loss"],
                "patterns": [r"claim\s+number", r"date\s+of\s+incident", r"damage", r"accident"]
            },
            "correspondence": {
                "keywords": ["dear", "sincerely", "regards", "letter", "correspondence"],
                "patterns": [r"dear\s+\w+", r"sincerely", r"best\s+regards"]
            },
            "invoice": {
                "keywords": ["invoice", "bill", "payment", "amount due", "total"],
                "patterns": [r"invoice\s+number", r"amount\s+due", r"total", r"payment"]
            },
            "application": {
                "keywords": ["application", "apply", "applicant", "form"],
                "patterns": [r"application\s+for", r"applicant\s+name", r"date\s+of\s+birth"]
            }
        }

    def classify_document(self, text):
        """Classify document based on text content"""
        text_lower = text.lower()
        scores = {}
        
        for doc_type, rules in self.classification_rules.items():
            score = 0
            
            # Check keywords
            for keyword in rules["keywords"]:
                if keyword in text_lower:
                    score += 1
            
            # Check patterns
            for pattern in rules["patterns"]:
                if re.search(pattern, text_lower):
                    score += 2
            
            scores[doc_type] = score
        
        # Find best match
        if scores:
            best_type = max(scores.items(), key=lambda x: x[1])
            if best_type[1] > 0:
                confidence = min(best_type[1] * 20, 100)  # Scale to percentage
                tags = self.extract_tags(text, best_type[0])
                return best_type[0], tags, confidence
        
        return "unknown", [], 30

    def extract_tags(self, text, doc_type):
        """Extract relevant tags based on document type"""
        tags = []
        text_lower = text.lower()
        
        if doc_type == "insurance_policy":
            if "auto" in text_lower or "vehicle" in text_lower:
                tags.append("auto_insurance")
            if "home" in text_lower or "property" in text_lower:
                tags.append("home_insurance")
            if "life" in text_lower:
                tags.append("life_insurance")
        
        elif doc_type == "claim_form":
            if "auto" in text_lower or "vehicle" in text_lower:
                tags.append("auto_claim")
            if "property" in text_lower or "home" in text_lower:
                tags.append("property_claim")
            if "urgent" in text_lower:
                tags.append("urgent")
        
        elif doc_type == "correspondence":
            if "complaint" in text_lower:
                tags.append("complaint")
            if "inquiry" in text_lower:
                tags.append("inquiry")
        
        return tags

    def store_classification_result(self, processing_id, file_uri, doc_type, tags, confidence):
        """Store classification result in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        tags_str = ",".join(tags) if tags else ""
        
        cursor.execute('''
            INSERT INTO classification_results 
            (processing_id, file_uri, document_type, tags, confidence_score, timestamp, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (processing_id, file_uri, doc_type, tags_str, confidence, datetime.now().isoformat(), 'completed'))
        
        conn.commit()
        conn.close()

    def send_to_data_extraction(self, processing_id, file_uri, doc_type, tags, text):
        """Send classified document to data extraction engine"""
        extraction_data = {
            "processing_id": processing_id,
            "file_uri": file_uri,
            "document_type": doc_type,
            "tags": tags,
            "extracted_text": text,
            "timestamp": datetime.now().isoformat(),
            "source": "classifier_engine",
            "status": "pending"
        }
        
        request_file = os.path.join(self.extraction_queue_path, f"classified_{processing_id}.json")
        
        with open(request_file, 'w') as f:
            json.dump(extraction_data, f, indent=2)
        
        print(f"Sent to data extraction: {request_file}")

    def process_classification_requests(self):
        """Process classification requests from OCR engine"""
        print("Document Classifier started - Monitoring for requests...")
        
        while True:
            try:
                # Check for new classification requests
                if os.path.exists(self.classifier_queue_path):
                    for filename in os.listdir(self.classifier_queue_path):
                        if filename.startswith("ocr_") and filename.endswith(".json"):
                            request_file = os.path.join(self.classifier_queue_path, filename)
                            
                            try:
                                with open(request_file, 'r') as f:
                                    request_data = json.load(f)
                                
                                processing_id = request_data.get("processing_id", "unknown")
                                file_uri = request_data.get("file_uri")
                                extracted_text = request_data.get("extracted_text", "")
                                
                                if extracted_text:
                                    print(f"Classifying document: {file_uri}")
                                    
                                    # Classify document
                                    doc_type, tags, confidence = self.classify_document(extracted_text)
                                    
                                    # Store result
                                    self.store_classification_result(processing_id, file_uri, doc_type, tags, confidence)
                                    
                                    # Send to data extraction
                                    self.send_to_data_extraction(processing_id, file_uri, doc_type, tags, extracted_text)
                                    
                                    print(f"Classification completed: {doc_type} (confidence: {confidence:.1f}%) - Tags: {tags}")
                                    
                                    # Remove processed request
                                    os.remove(request_file)
                                
                            except Exception as e:
                                print(f"Error processing {request_file}: {e}")
                
                time.sleep(2)  # Check every 2 seconds
                
            except KeyboardInterrupt:
                print("Document Classifier stopped")
                break
            except Exception as e:
                print(f"Classifier error: {e}")
                time.sleep(5)

if __name__ == "__main__":
    classifier = ClassifierEngine("dummy_path")  # Pass a dummy path since we're not using CSV data
    classifier.process_classification_requests()