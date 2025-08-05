import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
import joblib

class ModelTrainer:
    def __init__(self, data, target_column):
        self.data = data
        self.target_column = target_column
        self.model = RandomForestClassifier()

    def preprocess_data(self):
        X = self.data.drop(columns=[self.target_column])
        y = self.data[self.target_column]
        return train_test_split(X, y, test_size=0.2, random_state=42)

    def train_model(self):
        X_train, X_test, y_train, y_test = self.preprocess_data()
        self.model.fit(X_train, y_train)
        predictions = self.model.predict(X_test)
        accuracy = accuracy_score(y_test, predictions)
        print(f"Model accuracy: {accuracy:.2f}")
        print(classification_report(y_test, predictions))

    def save_model(self, filename):
        joblib.dump(self.model, filename)
        print(f"Model saved to {filename}")

# Example usage:
# if __name__ == "__main__":
#     data = pd.read_csv('path_to_your_data.csv')
#     trainer = ModelTrainer(data, target_column='your_target_column')
#     trainer.train_model()
#     trainer.save_model('trained_model.pkl')