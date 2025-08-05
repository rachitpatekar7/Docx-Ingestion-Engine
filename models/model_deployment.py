# model_deployment.py

import joblib
import os

class ModelDeployer:
    def __init__(self, model_path, deployment_path):
        self.model_path = model_path
        self.deployment_path = deployment_path

    def load_model(self):
        if os.path.exists(self.model_path):
            model = joblib.load(self.model_path)
            return model
        else:
            raise FileNotFoundError(f"Model file not found at {self.model_path}")

    def deploy_model(self):
        model = self.load_model()
        joblib.dump(model, self.deployment_path)
        print(f"Model deployed successfully to {self.deployment_path}")

if __name__ == "__main__":
    model_path = "path/to/your/trained/model.pkl"  # Update with your model path
    deployment_path = "path/to/deployment/location/model.pkl"  # Update with your deployment path

    deployer = ModelDeployer(model_path, deployment_path)
    deployer.deploy_model()