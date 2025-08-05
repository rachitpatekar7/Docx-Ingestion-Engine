# Insurance-AI Project

## Overview
The Insurance-AI project is designed to streamline and automate various processes related to insurance data management, including data ingestion, optical character recognition (OCR), classification, and reporting. This project aims to enhance efficiency and accuracy in handling insurance-related data.

## Project Structure
The project is organized into several directories and files, each serving a specific purpose:

- **README.md**: Documentation for the project.
- **.env**: Configuration for environment variables.
- **requirements.txt**: Lists Python dependencies.
- **data/**: Contains directories for different types of data:
  - **lake/**: Raw data storage.
  - **ingestion/**: Data ingestion processes.
  - **ocr/**: Files related to Optical Character Recognition.
  - **classifier/**: Files for classification tasks.
  - **submission/**: Files related to data submission.
  - **templates/**: Template files used in the project.
  - **rules/**: Storage for processing or classification rules.
- **engines/**: Contains various engines for processing data:
  - **email_listener.py**: Processes incoming emails.
  - **file_listener.py**: Monitors file changes or uploads.
  - **ingestion_engine.py**: Logic for ingesting data.
  - **ocr_engine.py**: Processes images and extracts text.
  - **classifier_engine.py**: Classification logic.
  - **submission_orchestrator.py**: Manages the submission process.
  - **data_extraction_engine.py**: Extracts data from sources.
  - **matching_rule_engine.py**: Matches rules against data.
  - **report_builder.py**: Builds reports based on data.
  - **notification_engine.py**: Handles notifications.
- **ui/**: User interface components:
  - **dashboard.py**: Visualizes data and results.
  - **chatbot.py**: User interaction interface.
  - **template_manager.py**: Manages templates.
  - **prompt_manager.py**: Handles user prompts.
  - **rule_extractor.py**: Extracts rules from data or input.
- **models/**: Contains machine learning models and related scripts:
  - **data_preparation.py**: Prepares data for analysis.
  - **rule_embedding.py**: Implements rule embedding techniques.
  - **model_training.py**: Trains machine learning models.
  - **model_validation.py**: Validates model performance.
  - **model_deployment.py**: Deploys trained models.
- **db/**: Databases for storing various data:
  - **ingestion_store.db**: Stores ingested data.
  - **ocr_store.db**: Stores OCR processed data.
  - **classifier_store.db**: Stores classification results.
  - **submission_store.db**: Stores submission data.
  - **template_store.db**: Stores templates.
  - **rules_store.db**: Stores rules.

## Setup Instructions
1. Clone the repository:
   ```
   git clone <repository-url>
   ```
2. Navigate to the project directory:
   ```
   cd Insurance-AI
   ```
3. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Configure environment variables in the `.env` file.

## Usage Guidelines
- Ensure that the necessary data is placed in the appropriate directories under `data/`.
- Run the desired engine scripts from the `engines/` directory to process data.
- Use the UI components in the `ui/` directory to interact with the system and visualize results.

## Contributing
Contributions are welcome! Please submit a pull request or open an issue for any suggestions or improvements.