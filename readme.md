# ML Classifier Trainer

A complete system for training, deploying, and managing custom image classification models on edge devices.

![ML Classifier Trainer Main Screen](placeholder_images/main_screen.png)

## Overview

ML Classifier Trainer is an end-to-end solution for creating binary image classifiers without writing code. The system consists of three main components:

1. **Desktop Application**: For data collection, model training, and management
2. **Backend API**: For model storage, device registration, and result collection
3. **Edge Devices**: For running inference with the trained models (e.g., Raspberry Pi)

This system allows you to quickly create custom image classifiers for specific use cases (e.g., quality control, object detection, presence verification) and deploy them to edge devices for real-time inference.

## System Architecture

```
┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐
│                 │         │                 │         │                 │
│  Desktop App    │ ◄─────► │  Backend API    │ ◄─────► │  Edge Devices   │
│  (PySide6/Qt)   │  REST   │  (Flask)        │  REST   │  (Raspberry Pi) │
│                 │  API    │                 │  API    │                 │
└─────────────────┘         └─────────────────┘         └─────────────────┘
       ▲                           ▲                           ▲
       │                           │                           │
       ▼                           ▼                           ▼
┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐
│  Local Storage  │         │  PostgreSQL &   │         │  TFLite Models  │
│  - Project Data │         │  AWS S3 Storage │         │  - Inference    │
│  - Model Files  │         │  - Results      │         │  - Camera Input │
└─────────────────┘         └─────────────────┘         └─────────────────┘
```

## Setup and Deployment

### Prerequisites

- Python 3.8+ installed on all systems
- Basic familiarity with command line interfaces
- For edge devices: Raspberry Pi 3+ or similar with camera module
- Network connectivity between all components

### 1. Backend API Setup

The backend server handles model storage, device management, and result collection.

#### Installation

```bash
# Clone the server repository
git clone https://github.com/yourusername/ml-classifier-api.git
cd ml-classifier-api/Backend

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env file with your settings

# Initialize the database
flask db init
flask db migrate -m "Initial migration"
flask db upgrade

# Start the development server
python run.py
```

#### Configuration Options

Edit the `.env` file to configure:

- `FLASK_APP` and `FLASK_ENV`: Flask configuration
- `DATABASE_URL`: PostgreSQL connection string
- `API_KEY`: Authentication key for secure endpoints
- `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_DEFAULT_REGION`: AWS credentials
- `S3_BUCKET_NAME`: S3 bucket for model storage

#### AWS Deployment

The project includes a complete Terraform infrastructure setup for AWS and a GitHub Actions workflow for CI/CD:

1. Set up necessary AWS credentials and permissions
2. Configure your GitHub repository secrets:
   - `AWS_ACCESS_KEY_ID`
   - `AWS_SECRET_ACCESS_KEY`
   - `EB_APP_NAME`
   - `EB_ENV_NAME`
3. Push to your repository to trigger the GitHub Actions workflow

The infrastructure will deploy to AWS Elastic Beanstalk with:

- RDS PostgreSQL database
- S3 buckets for model storage
- Proper IAM roles and security groups

### 2. Desktop Application Setup

#### Installation from Source

```bash
# Clone the desktop app repository
git clone https://github.com/yourusername/ml-classifier-trainer.git
cd ml-classifier-trainer

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py
```

#### Pre-built Binaries

Download the pre-built application for your platform from the [Releases](https://github.com/yourusername/ml-classifier-trainer/releases) page.

#### First Run Setup

On first run, you'll be prompted to:

1. Enter the API endpoint (URL of your backend server)
2. Enter your API key

![First Run Setup](placeholder_images/first_run.png)

### 3. Raspberry Pi Device Setup

The Raspberry Pi client automatically captures images from the camera, classifies them using the downloaded model, and uploads results to the API.

#### Automated Installation

```bash
# SSH into your Raspberry Pi
ssh admin@your-pi-ip-address

# Download the installation script
wget https://github.com/yourusername/ml-classifier-device/raw/main/setup_scripts/pi_install_script.sh

# Make the script executable
chmod +x pi_install_script.sh

# Run the installation script (edit with your values)
sudo ./pi_install_script.sh
```

During installation, you'll need to provide:

- API URL (e.g., https://your-api-endpoint.elasticbeanstalk.com)
- API key for authentication
- Capture interval (in seconds)
- Confidence threshold for classification

#### Manual Setup

If you prefer manual installation:

```bash
# Clone the device repository
git clone https://github.com/yourusername/ml-classifier-device.git
cd ml-classifier-device/RasberryPiApp

# Install required packages
sudo apt-get update
sudo apt-get install -y python3-pip python3-opencv libatlas-base-dev

# Install Python dependencies
pip3 install requests pillow tflite-runtime

# Run the client (edit with your values)
python3 pi_client.py --api https://your-api-endpoint.com --apikey your-api-key --interval 60
```

The client will automatically:

1. Register with the API server if not already registered
2. Check for and download new models
3. Capture images and perform classification
4. Upload results to the server

## Usage Guide

### Creating a New Project

1. Launch the desktop application
2. Go to the **Setup** tab
3. Click **New Project** and enter a project name
4. A new project folder will be created with the necessary structure

![Create New Project](placeholder_images/new_project.png)

### Collecting Training Data

#### Using Camera

1. Go to the **Collect Images** tab
2. Select the **Camera Capture** section
3. Click **Start Camera**
4. Click **Capture Positive** to capture positive examples
5. Click **Capture Negative** to capture negative examples

![Camera Capture](placeholder_images/camera_capture.png)

#### Importing Images

1. Go to the **Collect Images** tab
2. Select the **Import Images** section
3. Choose either **Import Folder** or **Import Files**
4. Repeat for both positive and negative examples

![Import Images](placeholder_images/import_images.png)

### Training a Model

1. Go to the **Train Model** tab
2. Set training parameters (epochs, batch size, learning rate)
3. Click **Train Model**
4. Monitor training progress and log
5. Once training is complete, click **Convert to TFLite**

![Train Model](placeholder_images/train_model.png)

### Deploying a Model

1. Go to the **Deploy Model** tab
2. Ensure the model has been trained and converted
3. Click **Deploy to Cloud**
4. The model will be uploaded to the backend server

![Deploy Model](placeholder_images/deploy_model.png)

### Managing Devices

1. Go to the **Devices** tab
2. Click **Register New Device** or manage existing devices
3. Use **Assign Model** to deploy a model to a specific device

![Manage Devices](placeholder_images/devices.png)

### Viewing Results

1. Go to the **Results** tab
2. Filter by device, model, or other criteria
3. View classification results and statistics

![View Results](placeholder_images/results.png)

## Technologies Used

### Desktop Application

- **PySide6**: Qt for Python GUI framework
- **TensorFlow/Keras**: For model training
- **OpenCV**: For camera integration and image processing
- **Requests**: For API communication

### Backend API

- **Flask**: Lightweight WSGI web application framework
- **Flask-SQLAlchemy**: ORM for database interactions
- **Flask-Migrate**: For database schema migrations
- **Boto3**: AWS SDK for S3 model storage
- **API Key Authentication**: For securing API endpoints

### Edge Device

- **TensorFlow Lite**: For model inference
- **OpenCV**: For camera integration and image processing
- **Raspberry Pi**: Hardware platform for edge computing
- **GPIO**: For hardware integration (lights, sensors, etc.)

## Development

### Building from Source

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
pytest

# Build executable
pyinstaller --name="ML-Classifier-Trainer" --windowed main.py
```
