# File: /Insurance-AI/engines/file_listener.py

import os
import time
import shutil
import json
from datetime import datetime

class FileListener:
    def __init__(self, directory_to_watch):
        self.directory_to_watch = directory_to_watch
        self.data_lake_path = "data/lake"
        self.ingestion_queue_path = "data/ingestion"
        
        # Create necessary directories
        os.makedirs(self.data_lake_path, exist_ok=True)
        os.makedirs(self.ingestion_queue_path, exist_ok=True)
        
        self.files_set = set(os.listdir(directory_to_watch))

    def store_to_data_lake(self, file_path):
        """Store file to data lake and return URI"""
        filename = os.path.basename(file_path)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        stored_filename = f"{timestamp}_{filename}"
        stored_path = os.path.join(self.data_lake_path, stored_filename)
        
        shutil.copy2(file_path, stored_path)
        return stored_path

    def send_to_ingestion_engine(self, file_uri, original_file):
        """Send file information to ingestion engine"""
        ingestion_data = {
            "file_uri": file_uri,
            "original_filename": original_file,
            "timestamp": datetime.now().isoformat(),
            "source": "file_listener",
            "status": "pending"
        }
        
        # Create ingestion request file
        request_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        request_file = os.path.join(self.ingestion_queue_path, f"request_{request_id}.json")
        
        with open(request_file, 'w') as f:
            json.dump(ingestion_data, f, indent=2)
        
        print(f"Sent to ingestion engine: {request_file}")

    def watch(self):
        print(f"Watching directory: {self.directory_to_watch}")
        while True:
            time.sleep(1)
            current_files_set = set(os.listdir(self.directory_to_watch))
            added_files = current_files_set - self.files_set
            removed_files = self.files_set - current_files_set

            if added_files:
                for file in added_files:
                    print(f"File added: {file}")
                    file_path = os.path.join(self.directory_to_watch, file)
                    
                    # Store to data lake
                    file_uri = self.store_to_data_lake(file_path)
                    print(f"Stored to data lake: {file_uri}")
                    
                    # Send to ingestion engine
                    self.send_to_ingestion_engine(file_uri, file)

            if removed_files:
                for file in removed_files:
                    print(f"File removed: {file}")

            self.files_set = current_files_set

if __name__ == "__main__":
    directory = "data/incoming"
    listener = FileListener(directory)
    listener.watch()