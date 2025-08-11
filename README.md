# 🚀 Email-to-Invoice Processing System

An intelligent, automated system that processes insurance-related emails, extracts invoice data from PDF/image attachments, and organizes everything in Google Drive with a user-friendly web interface.

## 🎯 What This System Does

This system creates a complete automated pipeline:

1. **📧 Email Monitoring**: Connects to Gmail and monitors for insurance-related emails
2. **📄 Document Processing**: Downloads PDF and image attachments from emails
3. **🔍 Data Extraction**: Uses OCR and AI to extract structured data from invoices
4. **☁️ Cloud Storage**: Automatically uploads results to Google Drive in organized folders
5. **🖥️ Web Interface**: Provides a real-time dashboard to monitor and control the process

---

## 🛠️ Complete Setup Guide (Start Here!)

Follow these steps **in order** to get the system running:

### Step 1: Prerequisites

Before starting, ensure you have:
- **Windows, macOS, or Linux** computer
- **Python 3.8 or higher** installed
- **Internet connection** for API access
- **Gmail account** (we'll set this up in Step 3)

#### Check Python Installation
```bash
python --version
# Should show Python 3.8.x or higher
```

If Python is not installed:
- **Windows/macOS**: Download from [https://www.python.org/downloads/](https://www.python.org/downloads/)
- **Linux**: `sudo apt install python3 python3-pip` (Ubuntu/Debian)

---

### Step 2: Download and Install the Project

```bash
# Clone the repository
git clone https://github.com/rachitpatekar7/Docx-Ingestion-Engine.git
cd Docx-Ingestion-Engine

# Create virtual environment (recommended)
python -m venv email_processor_env

# Activate virtual environment
# On Windows:
email_processor_env\Scripts\activate
# On macOS/Linux:
source email_processor_env/bin/activate

# Install main dependencies
pip install -r requirements.txt

# Install invoice reader dependencies
cd invoice_reader
pip install -r requirements.txt
cd ..
```

---

### Step 3: 🔑 Credential Setup (IMPORTANT!)

You need **4 credentials** to run this system. Follow each section carefully:

#### 3.1 Gmail App Password (Required)

**Why needed**: To securely connect to Gmail and read emails

**Steps to get Gmail App Password**:

1. **Open Gmail Settings**: [https://myaccount.google.com/security](https://myaccount.google.com/security)

2. **Enable 2-Factor Authentication** (if not already enabled):
   - Click "2-Step Verification"
   - Follow the setup process
   - Verify with your phone number

3. **Generate App Password**:
   - Go back to Security: [https://myaccount.google.com/security](https://myaccount.google.com/security)
   - Click "2-Step Verification" → "App passwords"
   - Select "Mail" from dropdown
   - Choose "Other" and type "Email Invoice Processor"
   - Click "Generate"
   - **Copy the 16-character password** (e.g., `abcd efgh ijkl mnop`)

4. **Where to use**: You'll enter this in the web interface later

---

#### 3.2 Google Drive API Credentials (Required)

**Why needed**: To automatically upload processed files to Google Drive

**Steps to get Google Drive API credentials**:

1. **Open Google Cloud Console**: [https://console.cloud.google.com/](https://console.cloud.google.com/)

2. **Create or Select Project**:
   - Click "Select a project" → "New Project"
   - Name: "Email Invoice Processor"
   - Click "Create"

3. **Enable Google Drive API**:
   - Go to [https://console.cloud.google.com/apis/library](https://console.cloud.google.com/apis/library)
   - Search "Google Drive API"
   - Click on "Google Drive API"
   - Click "Enable"

4. **Create Service Account**:
   - Go to [https://console.cloud.google.com/iam-admin/serviceaccounts](https://console.cloud.google.com/iam-admin/serviceaccounts)
   - Click "Create Service Account"
   - Name: "email-processor-service"
   - Click "Create and Continue"
   - Skip role assignment, click "Done"

5. **Generate Credentials File**:
   - Click on your newly created service account
   - Go to "Keys" tab
   - Click "Add Key" → "Create new key"
   - Choose "JSON"
   - Click "Create"
   - **Save the downloaded file as `credentials.json`** in your project root folder

6. **Share Google Drive Folder**:
   - Open [https://drive.google.com/](https://drive.google.com/)
   - Create a folder called "Email Invoice Processing"
   - Right-click folder → "Share"
   - Add the email address from your `credentials.json` file (looks like: `email-processor-service@project-name.iam.gserviceaccount.com`)
   - Give "Editor" permissions
   - Click "Send"

---

#### 3.3 Groq API Key (Required)

**Why needed**: For AI-powered invoice data extraction

**Steps to get Groq API key**:

1. **Sign up for Groq**: [https://console.groq.com/](https://console.groq.com/)

2. **Create Account**:
   - Click "Sign Up"
   - Use your email or GitHub account
   - Verify your email if required

3. **Generate API Key**:
   - Go to [https://console.groq.com/keys](https://console.groq.com/keys)
   - Click "Create API Key"
   - Name: "Email Invoice Processor"
   - Click "Submit"
   - **Copy the API key** (starts with `gsk_...`)

4. **Where to add**: Create `.env` file (see Step 4)

---

#### 3.4 Poppler Installation (Required for PDF processing)

**Why needed**: To convert PDF files to images for OCR processing

**Installation by Operating System**:

**Windows**:
```bash
# Download Poppler for Windows
# Go to: https://github.com/oschwartz10612/poppler-windows/releases/
# Download the latest release (e.g., Release-23.01.0-0.zip)
# Extract to: T:\github\Docx-Ingestion-Engine\invoice_reader\poppler\

# Or use our pre-configured path (if you cloned to T:\github\):
# The poppler folder should already be included in the project
```

**macOS**:
```bash
# Install using Homebrew
brew install poppler

# Or using MacPorts
sudo port install poppler
```

**Linux (Ubuntu/Debian)**:
```bash
sudo apt-get update
sudo apt-get install poppler-utils
```

---

### Step 4: 📝 Configure Environment Variables

Create configuration files with your credentials:

#### 4.1 Create `.env` file in `invoice_reader/` folder

```bash
# Navigate to invoice_reader folder
cd invoice_reader

# Create .env file
# On Windows (Command Prompt):
echo GROQ_API_KEY=your_groq_api_key_here > .env

# On Windows (PowerShell):
echo "GROQ_API_KEY=your_groq_api_key_here" | Out-File -FilePath .env -Encoding UTF8

# On macOS/Linux:
echo "GROQ_API_KEY=your_groq_api_key_here" > .env
```

**Replace `your_groq_api_key_here` with your actual Groq API key from Step 3.3**

Example `.env` file content:
```
GROQ_API_KEY=gsk_1234567890abcdef1234567890abcdef1234567890abcdef
```

#### 4.2 Verify credentials.json location

Make sure your Google Drive credentials file is in the correct location:
```
Docx-Ingestion-Engine/
├── credentials.json  ← Should be here
├── email_invoice_dashboard.py
├── requirements.txt
└── ...
```

---

### Step 5: 🧪 Test Your Setup

Before running the main application, let's test each component:

#### 5.1 Test Google Drive Connection
```bash
# From project root
cd engines
python test_drive_setup.py
```
**Expected output**: "✅ Google Drive connection successful!"

#### 5.2 Test Invoice Reader
```bash
# From project root
cd invoice_reader
python test_extraction.py
```
**Expected output**: OCR and AI processing test results

#### 5.3 Test Email Connection (Interactive)
```bash
# From project root
cd engines
python test_email_connection.py
```
**You'll be prompted for**: Gmail address and app password

---

### Step 6: 🚀 Run the Application

Now you're ready to start the system!

```bash
# Make sure you're in the project root directory
cd Docx-Ingestion-Engine

# Activate virtual environment (if not already active)
# Windows:
email_processor_env\Scripts\activate
# macOS/Linux:
source email_processor_env/bin/activate

# Start the web dashboard
python -m streamlit run email_invoice_dashboard.py
```

**The application will open in your browser at**: `http://localhost:8501`

---

### Step 7: 🖥️ Using the Web Interface

#### 7.1 First Time Setup
1. **Enter Gmail Credentials**:
   - Gmail Address: `your.email@gmail.com`
   - App Password: `abcd efgh ijkl mnop` (from Step 3.1)

2. **Click "Connect to Email"**
   - Wait for "✅ Connected to email server" message

#### 7.2 Processing Emails
1. **Check for New Emails**:
   - Click "🔍 Check Emails Once" for unread emails only
   - Click "🔄 Force Check All Emails" for last 3 days

2. **Monitor Progress**:
   - Watch real-time logs in the "📝 Processing Logs" section
   - See processing status for each email

3. **Access Results**:
   - Click the blue Google Drive buttons to open processed folders
   - Download CSV data using the download buttons

---

## 🔧 Dependencies Explained

### Main Application Dependencies (`requirements.txt`)
```
streamlit>=1.28.0          # Web interface framework
pandas>=1.5.0              # Data manipulation
python-dotenv>=0.19.0      # Environment variable loading
google-api-python-client   # Google Drive API
google-auth-httplib2       # Google authentication
google-auth-oauthlib       # Google OAuth
```

### Invoice Reader Dependencies (`invoice_reader/requirements.txt`)
```
easyocr>=1.7.0            # Optical Character Recognition
opencv-python>=4.8.0      # Image processing
pypdf>=3.0.0              # PDF text extraction
pdf2image>=3.1.0          # PDF to image conversion
langchain-groq>=0.1.0     # AI model integration
numpy>=1.24.0             # Numerical operations
pillow>=9.0.0             # Image manipulation
```

### System Dependencies
- **Poppler**: PDF processing (installed in Step 3.4)
- **Tesseract**: OCR engine (automatically installed with EasyOCR)

---

## 🎯 Key Features

### Email Processing
- ✅ **Smart Filtering**: Only processes insurance-related emails
- ✅ **Attachment Download**: Automatically saves PDF/image attachments
- ✅ **Duplicate Prevention**: Tracks processed emails to avoid reprocessing
- ✅ **Real-time Monitoring**: Live status updates and logging

### Document Processing
- ✅ **Multi-format Support**: PDF, JPG, PNG files
- ✅ **OCR Technology**: EasyOCR for scanned documents
- ✅ **AI Extraction**: Groq LLaMA for intelligent field recognition
- ✅ **Data Validation**: Automatic error checking and correction

### Cloud Integration
- ✅ **Google Drive Upload**: Automatic organization in timestamped folders
- ✅ **File Management**: CSV data, JSON metadata, original files
- ✅ **Shareable Links**: Easy access to processed results
- ✅ **Local Cleanup**: Files deleted after successful upload

### Web Interface
- ✅ **Real-time Dashboard**: Live processing status and logs
- ✅ **Interactive Controls**: Connect, process, monitor, download
- ✅ **Responsive Design**: Works on desktop and mobile
- ✅ **Error Handling**: Clear error messages and troubleshooting

---

## 🔍 Troubleshooting

### Common Issues and Solutions

#### "Failed to connect to Gmail"
**Possible causes**:
- ❌ Using regular password instead of App Password
- ❌ 2-Factor Authentication not enabled
- ❌ IMAP not enabled in Gmail

**Solutions**:
1. Verify you're using the 16-character App Password
2. Enable 2FA: [https://myaccount.google.com/security](https://myaccount.google.com/security)
3. Enable IMAP: [https://mail.google.com/mail/u/0/#settings/fwdandpop](https://mail.google.com/mail/u/0/#settings/fwdandpop)

#### "Google Drive authentication failed"
**Possible causes**:
- ❌ credentials.json file missing or in wrong location
- ❌ Google Drive API not enabled
- ❌ Service account not shared with Drive folder

**Solutions**:
1. Check `credentials.json` is in project root
2. Enable API: [https://console.cloud.google.com/apis/library](https://console.cloud.google.com/apis/library)
3. Share Drive folder with service account email

#### "Groq API error"
**Possible causes**:
- ❌ Invalid API key
- ❌ API key not in .env file
- ❌ Exceeded API rate limits

**Solutions**:
1. Verify API key: [https://console.groq.com/keys](https://console.groq.com/keys)
2. Check `.env` file exists in `invoice_reader/` folder
3. Wait and retry if rate limited

#### "Poppler not found error"
**Possible causes**:
- ❌ Poppler not installed
- ❌ Wrong path configuration

**Solutions**:
1. **Windows**: Download from [https://github.com/oschwartz10612/poppler-windows/releases/](https://github.com/oschwartz10612/poppler-windows/releases/)
2. **macOS**: `brew install poppler`
3. **Linux**: `sudo apt install poppler-utils`

#### "No emails found"
**Possible causes**:
- ❌ No insurance-related emails in last 3 days
- ❌ All emails already processed

**Solutions**:
1. Send test email with subject containing "insurance"
2. Use "Force Check All Emails" to reprocess
3. Click "Reset Email Cache" to clear processed list

---

## 🔐 Security Best Practices

### Credential Security
- ✅ **App Passwords**: More secure than regular passwords
- ✅ **Environment Variables**: Credentials not hardcoded
- ✅ **Local Files**: Deleted after cloud upload
- ✅ **API Rate Limiting**: Built-in protection against abuse

### Data Privacy
- ✅ **Targeted Processing**: Only insurance emails processed
- ✅ **Local Processing**: OCR done locally, not sent to external services
- ✅ **Secure APIs**: All connections use HTTPS
- ✅ **Audit Logging**: Complete record of all operations

---

## 📊 File Structure Explained

```
Docx-Ingestion-Engine/
├── 📄 email_invoice_dashboard.py      # Main web interface
├── 🔧 integrated_email_invoice_processor.py  # Core processing engine
├── 📋 requirements.txt                # Python dependencies
├── 🔑 credentials.json               # Google Drive API credentials
├── 📖 README.md                      # This documentation
│
├── 🔧 engines/                       # Core processing modules
│   ├── 📧 email_listener.py          # Gmail IMAP connection
│   ├── 🚀 drive_uploader.py          # Google Drive integration
│   ├── 🧪 test_email_connection.py   # Email testing utility
│   └── 🧪 test_drive_setup.py        # Drive testing utility
│
├── 🧾 invoice_reader/                 # Invoice processing system
│   ├── ⚙️ backend.py                 # OCR + AI processing
│   ├── 📝 .env                       # Groq API key (you create this)
│   ├── 📋 requirements.txt           # Invoice reader dependencies
│   ├── 🧪 test_extraction.py         # Invoice testing utility
│   └── 📂 poppler/                   # PDF processing tools
│
├── 📂 attachments/                   # Downloaded email attachments (auto-created)
├── 🗄️ db/                            # SQLite databases (auto-created)
├── 📜 logs/                          # Application logs (auto-created)
└── 💾 data/                          # Processed data storage (auto-created)
```

---

## 🚀 Quick Start Checklist

Use this checklist to ensure you have everything set up:

### ✅ Prerequisites
- [ ] Python 3.8+ installed
- [ ] Project downloaded and dependencies installed
- [ ] Virtual environment activated

### ✅ Credentials
- [ ] Gmail App Password generated
- [ ] Google Drive API credentials.json downloaded
- [ ] Groq API key obtained
- [ ] .env file created with Groq API key
- [ ] Poppler installed for your OS

### ✅ Testing
- [ ] Google Drive connection test passed
- [ ] Invoice reader test passed
- [ ] Email connection test passed

### ✅ Ready to Run
- [ ] Streamlit dashboard started
- [ ] Gmail credentials entered in web interface
- [ ] Successfully connected to email server

---

## 📞 Support and Help

### Getting Help
- **Issues**: Open an issue on [GitHub Issues](https://github.com/rachitpatekar7/Docx-Ingestion-Engine/issues)
- **Questions**: Use [GitHub Discussions](https://github.com/rachitpatekar7/Docx-Ingestion-Engine/discussions)
- **Documentation**: All functions are documented in the code

### Useful Links
- **Gmail App Passwords**: [https://support.google.com/accounts/answer/185833](https://support.google.com/accounts/answer/185833)
- **Google Cloud Console**: [https://console.cloud.google.com/](https://console.cloud.google.com/)
- **Groq Console**: [https://console.groq.com/](https://console.groq.com/)
- **Streamlit Documentation**: [https://docs.streamlit.io/](https://docs.streamlit.io/)

---

**🎉 Congratulations! You now have a fully automated email-to-invoice processing system!**

The system will monitor your Gmail, extract invoice data, and organize everything in Google Drive automatically. Happy processing! 🚀

python engines/run_email_listener.py

## Usage Guidelines
- Ensure that the necessary data is placed in the appropriate directories under `data/`.
- Run the desired engine scripts from the `engines/` directory to process data.
- Use the UI components in the `ui/` directory to interact with the system and visualize results.

## Contributing
Contributions are welcome! Please submit a pull request or open an issue for any suggestions or improvements.
