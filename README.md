# BrailleBridge: AI-Powered Braille Literacy Tool

[![React](https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)](https://reactjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![PyTorch](https://img.shields.io/badge/PyTorch-%23EE4C2C.svg?style=for-the-badge&logo=PyTorch&logoColor=white)](https://pytorch.org/)
[![Ollama](https://img.shields.io/badge/Ollama-000000?style=for-the-badge&logo=ollama&logoColor=white)](https://ollama.ai/)

BrailleBridge is a comprehensive, AI-enhanced platform designed to empower educators in teaching Braille and supporting visually impaired students. It bridges the gap between traditional Braille learning and modern technology by providing tools for creating, distributing, and grading assignments in both visual and audio formats.

## Core Features

-   **Braille OCR**: Automatically converts images of Braille text into digital Urdu script using a fine-tuned YOLOv11 model.
-   **Audio-to-Text**: Transcribes student's audio responses in Urdu and translates them to English using the Gemma 3N model.
-   **Text-to-Braille**: Converts digital Urdu or English text into Grade 1 Braille.
-   **Assignment Management**: Enables teachers to create assignments with image-based diagrams and text/audio prompts.
-   **AI-Powered Grading**: Provides automated feedback and analysis of student submissions, identifying strengths and weaknesses.
-   **Student Profiles**: Tracks individual student progress with AI-generated insights.
-   **Lesson Pack Generation**: Bundles assignments and materials into distributable lesson packs.

## Tech Stack

-   **Frontend**: React, TypeScript, Vite, Material-UI
-   **Backend**: Python, FastAPI, Uvicorn
-   **AI/ML**:
    -   `ultralytics` (YOLOv11) for Braille OCR.
    -   `transformers` & `ollama` for running the `google/gemma-3n-E4B-it` model for audio processing and language tasks.
    -   `louis` for Braille translation.
-   **Database**: TinyDB for lightweight, file-based data storage.
-   **Environment**: Conda / Venv for Python, Node.js/npm for the frontend.

---

## Getting Started

### 1. Prerequisites

-   **Python 3.9+**
-   **Node.js v18+** and **npm**
-   **Ollama**: Install and run Ollama to serve the Gemma model.
    -   Download from [ollama.ai](https://ollama.ai/).
    -   After installation, pull the required model:
        ```bash
        ollama pull gemma3n:e2b
        ```
-   **liblouis**: A required library for Braille translation.
    -   For macOS with Homebrew:
        ```bash
        brew install liblouis
        ```
    -   For other systems, follow the manual build instructions in the **"liblouis Manual Installation"** section below.

### 2. Clone the Repository

```bash
git clone https://github.com/your-username/braille-bridge.git
cd braille-bridge
```

### 3. Backend Setup

The backend server runs on FastAPI and handles all the AI processing and data management.

#### a. Create a Virtual Environment

```bash
# Navigate to the backend directory
cd backend

# Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate

# On Windows, use:
# venv\Scripts\activate
```

#### b. Install Dependencies

```bash
# Install requirements
pip install -r requirements.txt

# Install moshi-mlx separately due to conflicting dependencies
pip install moshi-mlx
```

#### c. Download the YOLO11 Model

The fine-tuned YOLO model for Braille OCR is required. Make sure to place it in the `backend/` directory.
-   **Required File**: `backend/yolo11n.pt`

#### d. Configure Environment Variables

Create a `.env` file in the `backend/` directory.

```bash
# backend/.env
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
BACKEND_RELOAD=true
FRONTEND_URL=http://localhost:5173
LOG_LEVEL=INFO
```

### 4. Frontend Setup

The frontend is a React application built with Vite.

#### a. Install Dependencies

```bash
# Navigate to the project root directory (if you are in `backend`, go back)
cd ..

# Install npm packages
npm install
```

#### b. Configure Environment Variables

Create a `.env` file in the project's root directory.

```bash
# .env (in the root of the project)
VITE_API_BASE_URL=http://localhost:8000
VITE_FRONTEND_URL=http://localhost:5173
```

---

## Running the Application

You need to run both the backend and frontend servers.

#### 1. Start the Backend Server

```bash
# Make sure you are in the backend directory with the virtual environment activated
cd backend
source venv/bin/activate

# Run the server
python run.py
```

The API will be available at `http://localhost:8000`. You can view the documentation at `http://localhost:8000/docs`.

#### 2. Start the Frontend Development Server

Open a **new terminal** and navigate to the project root.

```bash
# From the project root
npm run dev
```

The application will be accessible at `http://localhost:5173`.

---

## liblouis Manual Installation (If Brew Fails)

If you cannot install `liblouis` via a package manager, you can build it from source. The source is included in the repo.

```bash
# Navigate to the liblouis directory
cd liblouis-3.34.0

# Optional: Clean previous installations
make uninstall
make clean

# Configure, build, and install
./configure --enable-ucs4 --prefix=/opt/homebrew
make
sudo make install

# Install the Python bindings
cd python && python setup.py install
```

## Data Preprocessing Scripts

The `backend/preprocessing` directory contains scripts used for generating the training data for the models. These are not required for running the application but are available for developers who wish to retrain or fine-tune the models.

-   `extract_urdu_body_texts.py`: Extracts text from Urdu news articles.
-   `chunk_urdu_texts.py`: Chunks large text files into smaller segments.
-   `convert_to_braille.py`: Converts Urdu text to Braille using `liblouis`.
-   `braille_synthetic_photo.py`: Generates synthetic images of Braille text for training the OCR model.
-   `generate_full_dataset.py`: A pipeline script to run the full data generation process.
