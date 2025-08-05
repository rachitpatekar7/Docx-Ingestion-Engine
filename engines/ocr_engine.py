# ocr_engine.py

import os
import json
import time
import sqlite3
from datetime import datetime
import pytesseract
from PIL import Image

class OCREngine:
    def __init__(self):
        self.ocr_store_path = "data/ocr"
        self.ingestion_queue_path = "data/ingestion"
        self.classifier_queue_path = "data/classifier"
        self.db_path = "db/ocr_store.db"
        
        # Create necessary directories
        os.makedirs(self.ocr_store_path, exist_ok=True)
        os.makedirs(self.classifier_queue_path, exist_ok=True)
        os.makedirs("db", exist_ok=True)
        
        self.init_database()

    def init_database(self):
        """Initialize OCR results database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ocr_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                processing_id TEXT,
                file_uri TEXT,
                extracted_text TEXT,
                confidence_score REAL,
                timestamp TEXT,
                status TEXT
            )
        ''')
        
        conn.commit()
        conn.close()

    def extract_text_from_file(self, file_path):
        """Extract text using OCR"""
        try:
            # Handle different file types
            if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.tiff', '.bmp')):
                image = Image.open(file_path)
                text = pytesseract.image_to_string(image)
                confidence = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
                avg_confidence = sum([int(conf) for conf in confidence['conf'] if int(conf) > 0]) / len([conf for conf in confidence['conf'] if int(conf) > 0])
            else:
                # For non-image files, read as text
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    text = f.read()
                avg_confidence = 100.0  # Text files have 100% confidence
            
            return text.strip(), avg_confidence
        except Exception as e:
            print(f"Error extracting text from {file_path}: {e}")
            return "", 0.0

    def store_ocr_result(self, processing_id, file_uri, text, confidence):
        """Store OCR result in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO ocr_results 
            (processing_id, file_uri, extracted_text, confidence_score, timestamp, status)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (processing_id, file_uri, text, confidence, datetime.now().isoformat(), 'completed'))
        
        conn.commit()
        conn.close()

    def send_to_classifier(self, processing_id, file_uri, text):
        """Send extracted text to document classifier"""
        classifier_data = {
            "processing_id": processing_id,
            "file_uri": file_uri,
            "extracted_text": text,
            "timestamp": datetime.now().isoformat(),
            "source": "ocr_engine",
            "status": "pending"
        }
        
        request_file = os.path.join(self.classifier_queue_path, f"ocr_{processing_id}.json")
        
        with open(request_file, 'w') as f:
            json.dump(classifier_data, f, indent=2)
        
        print(f"Sent to classifier: {request_file}")

    def process_ocr_requests(self):
        """Process OCR requests from ingestion engine"""
        print("OCR Engine started - Monitoring for requests...")
        
        while True:
            try:
                # Check for new OCR requests
                if os.path.exists(self.ingestion_queue_path):
                    for filename in os.listdir(self.ingestion_queue_path):
                        if filename.startswith("request_") and filename.endswith(".json"):
                            request_file = os.path.join(self.ingestion_queue_path, filename)
                            
                            try:
                                with open(request_file, 'r') as f:
                                    request_data = json.load(f)
                                
                                processing_id = request_data.get("timestamp", "unknown")
                                file_uri = request_data.get("file_uri")
                                
                                if file_uri and os.path.exists(file_uri):
                                    print(f"Processing OCR for: {file_uri}")
                                    
                                    # Extract text
                                    text, confidence = self.extract_text_from_file(file_uri)
                                    
                                    # Store result
                                    self.store_ocr_result(processing_id, file_uri, text, confidence)
                                    
                                    # Send to classifier
                                    self.send_to_classifier(processing_id, file_uri, text)
                                    
                                    print(f"OCR completed for {file_uri} - Confidence: {confidence:.2f}%")
                                    
                                    # Remove processed request
                                    os.remove(request_file)
                                
                            except Exception as e:
                                print(f"Error processing {request_file}: {e}")
                
                time.sleep(2)  # Check every 2 seconds
                
            except KeyboardInterrupt:
                print("OCR Engine stopped")
                break
            except Exception as e:
                print(f"OCR Engine error: {e}")
                time.sleep(5)

if __name__ == "__main__":
    ocr_engine = OCREngine()
    ocr_engine.process_ocr_requests()