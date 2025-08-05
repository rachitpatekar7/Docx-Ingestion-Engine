import os
import json
import time
import sqlite3
from datetime import datetime

class MatchingRuleEngine:
    def __init__(self):
        self.submission_queue_path = "data/submission"
        self.report_queue_path = "data/reports"
        self.db_path = "db/submission_store.db"
        
        # Create necessary directories
        os.makedirs(self.report_queue_path, exist_ok=True)
        os.makedirs("db", exist_ok=True)
        
        self.init_database()
        self.load_business_rules()

    def init_database(self):
        """Initialize or update submission store database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Add scorecard and appetite columns if they don't exist
        cursor.execute("PRAGMA table_info(submission_data)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'scorecard_data' not in columns:
            cursor.execute('ALTER TABLE submission_data ADD COLUMN scorecard_data TEXT')
        if 'appetite_data' not in columns:
            cursor.execute('ALTER TABLE submission_data ADD COLUMN appetite_data TEXT')
        if 'risk_score' not in columns:
            cursor.execute('ALTER TABLE submission_data ADD COLUMN risk_score REAL')
        
        conn.commit()
        conn.close()

    def load_business_rules(self):
        """Load business rules for insurance processing"""
        self.insurance_rules = {
            "auto_insurance": {
                "risk_factors": {
                    "high_premium": {"threshold": 1000, "weight": 0.3},
                    "low_deductible": {"threshold": 500, "weight": 0.2},
                    "new_policy": {"weight": 0.1}
                },
                "appetite_rules": {
                    "accept": {"max_premium": 2000, "min_deductible": 250},
                    "review": {"max_premium": 3000, "min_deductible": 100},
                    "decline": {"max_premium": 5000, "min_deductible": 0}
                }
            },
            "home_insurance": {
                "risk_factors": {
                    "high_premium": {"threshold": 800, "weight": 0.3},
                    "low_deductible": {"threshold": 1000, "weight": 0.2},
                    "new_policy": {"weight": 0.1}
                },
                "appetite_rules": {
                    "accept": {"max_premium": 1500, "min_deductible": 500},
                    "review": {"max_premium": 2500, "min_deductible": 250},
                    "decline": {"max_premium": 4000, "min_deductible": 0}
                }
            }
        }

    def evaluate_risk_score(self, extracted_data, document_type):
        """Calculate risk score based on extracted data"""
        risk_score = 0.0
        scorecard = {}
        
        # Determine insurance type
        coverage_type = extracted_data.get("coverage_type", "").lower()
        insurance_type = "auto_insurance" if "auto" in coverage_type else "home_insurance"
        
        if insurance_type not in self.insurance_rules:
            return risk_score, scorecard
        
        rules = self.insurance_rules[insurance_type]["risk_factors"]
        
        # Check premium risk
        premium_str = extracted_data.get("premium", "0")
        try:
            premium = float(premium_str.replace(",", "").replace("$", ""))
            if premium > rules["high_premium"]["threshold"]:
                risk_score += rules["high_premium"]["weight"]
                scorecard["high_premium"] = True
            else:
                scorecard["high_premium"] = False
        except:
            premium = 0
        
        # Check deductible risk
        deductible_str = extracted_data.get("deductible", "0")
        try:
            deductible = float(deductible_str.replace(",", "").replace("$", ""))
            if deductible < rules["low_deductible"]["threshold"]:
                risk_score += rules["low_deductible"]["weight"]
                scorecard["low_deductible"] = True
            else:
                scorecard["low_deductible"] = False
        except:
            deductible = 0
        
        # New policy factor
        risk_score += rules["new_policy"]["weight"]
        scorecard["new_policy"] = True
        scorecard["calculated_premium"] = premium
        scorecard["calculated_deductible"] = deductible
        
        return risk_score, scorecard

    def determine_appetite(self, extracted_data, risk_score):
        """Determine appetite decision based on rules"""
        coverage_type = extracted_data.get("coverage_type", "").lower()
        insurance_type = "auto_insurance" if "auto" in coverage_type else "home_insurance"
        
        if insurance_type not in self.insurance_rules:
            return "review", "Unknown insurance type"
        
        rules = self.insurance_rules[insurance_type]["appetite_rules"]
        
        # Extract premium and deductible
        try:
            premium = float(extracted_data.get("premium", "0").replace(",", "").replace("$", ""))
            deductible = float(extracted_data.get("deductible", "0").replace(",", "").replace("$", ""))
        except:
            return "review", "Invalid premium or deductible data"
        
        # Apply appetite rules
        if (premium <= rules["accept"]["max_premium"] and 
            deductible >= rules["accept"]["min_deductible"] and 
            risk_score < 0.3):
            return "accept", f"Premium: ${premium}, Deductible: ${deductible}, Risk Score: {risk_score:.2f}"
        
        elif (premium <= rules["review"]["max_premium"] and 
              deductible >= rules["review"]["min_deductible"] and 
              risk_score < 0.6):
            return "review", f"Premium: ${premium}, Deductible: ${deductible}, Risk Score: {risk_score:.2f}"
        
        else:
            return "decline", f"Premium: ${premium}, Deductible: ${deductible}, Risk Score: {risk_score:.2f}"

    def update_submission_with_results(self, submission_id, scorecard_data, appetite_data, risk_score):
        """Update submission record with scorecard and appetite results"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE submission_data 
            SET scorecard_data = ?, appetite_data = ?, risk_score = ?, status = ?
            WHERE submission_id = ?
        ''', (json.dumps(scorecard_data), json.dumps(appetite_data), risk_score, 'processed', submission_id))
        
        conn.commit()
        conn.close()

    def send_to_report_builder(self, submission_id, processing_id, document_type, extracted_data, scorecard_data, appetite_data):
        """Send processed data to report builder"""
        report_data = {
            "submission_id": submission_id,
            "processing_id": processing_id,
            "document_type": document_type,
            "extracted_data": extracted_data,
            "scorecard_data": scorecard_data,
            "appetite_data": appetite_data,
            "timestamp": datetime.now().isoformat(),
            "source": "matching_rule_engine",
            "status": "pending"
        }
        
        request_file = os.path.join(self.report_queue_path, f"processed_{submission_id}.json")
        
        with open(request_file, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        print(f"Sent to report builder: {request_file}")

    def process_matching_requests(self):
        """Process matching requests from data extraction engine"""
        print("Matching/Rule Engine started - Monitoring for requests...")
        
        while True:
            try:
                # Check for new matching requests
                if os.path.exists(self.submission_queue_path):
                    for filename in os.listdir(self.submission_queue_path):
                        if filename.startswith("extracted_") and filename.endswith(".json"):
                            request_file = os.path.join(self.submission_queue_path, filename)
                            
                            try:
                                with open(request_file, 'r') as f:
                                    request_data = json.load(f)
                                
                                submission_id = request_data.get("submission_id", "unknown")
                                processing_id = request_data.get("processing_id", "unknown")
                                document_type = request_data.get("document_type", "unknown")
                                extracted_data = request_data.get("extracted_data", {})
                                
                                if extracted_data:
                                    print(f"Processing rules for: {submission_id}")
                                    
                                    # Calculate risk score and scorecard
                                    risk_score, scorecard = self.evaluate_risk_score(extracted_data, document_type)
                                    
                                    # Determine appetite
                                    appetite_decision, appetite_reason = self.determine_appetite(extracted_data, risk_score)
                                    
                                    appetite_data = {
                                        "decision": appetite_decision,
                                        "reason": appetite_reason,
                                        "risk_score": risk_score
                                    }
                                    
                                    # Update submission record
                                    self.update_submission_with_results(submission_id, scorecard, appetite_data, risk_score)
                                    
                                    # Send to report builder
                                    self.send_to_report_builder(submission_id, processing_id, document_type, 
                                                              extracted_data, scorecard, appetite_data)
                                    
                                    print(f"Rules processing completed: {submission_id}")
                                    print(f"Risk Score: {risk_score:.2f}, Decision: {appetite_decision}")
                                    print(f"Scorecard: {scorecard}")
                                    
                                    # Remove processed request
                                    os.remove(request_file)
                                
                            except Exception as e:
                                print(f"Error processing {request_file}: {e}")
                
                time.sleep(2)  # Check every 2 seconds
                
            except KeyboardInterrupt:
                print("Matching/Rule Engine stopped")
                break
            except Exception as e:
                print(f"Matching/Rule Engine error: {e}")
                time.sleep(5)

if __name__ == "__main__":
    engine = MatchingRuleEngine()
    engine.process_matching_requests()