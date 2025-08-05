# Data Preparation Module for Insurance-AI Project

import pandas as pd
from sklearn.model_selection import train_test_split

class DataPreparation:
    def __init__(self, data_path):
        self.data_path = data_path
        self.data = None

    def load_data(self):
        """Load data from the specified path."""
        self.data = pd.read_csv(self.data_path)
        return self.data

    def clean_data(self):
        """Perform data cleaning operations."""
        # Example cleaning operations
        self.data.dropna(inplace=True)
        self.data = self.data[self.data['column_name'] != 'unwanted_value']
        return self.data

    def split_data(self, target_column, test_size=0.2, random_state=42):
        """Split the data into training and testing sets."""
        X = self.data.drop(columns=[target_column])
        y = self.data[target_column]
        return train_test_split(X, y, test_size=test_size, random_state=random_state)

    def save_cleaned_data(self, output_path):
        """Save the cleaned data to a specified output path."""
        self.data.to_csv(output_path, index=False)