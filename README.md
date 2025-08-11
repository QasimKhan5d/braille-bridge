# Braille Bridge

A comprehensive application for braille education and learning, featuring both frontend and backend components.

## Project Structure

```
braille-bridge/
├── frontend/          # React TypeScript frontend application
│   ├── src/          # Source code
│   ├── public/       # Static assets
│   ├── package.json  # Frontend dependencies
│   └── ...
├── backend/          # Python FastAPI backend application
│   ├── app/         # Main application code
│   ├── services/    # Business logic services
│   ├── models/      # Data models
│   ├── preprocessing/ # Data preprocessing scripts
│   ├── requirements.txt # Python dependencies
│   └── ...
├── LICENSE          # Project license
├── setup.sh         # Automated setup script
└── .gitignore      # Git ignore rules
```

## Getting Started

### Prerequisites

- Node.js (for frontend)
- Python 3.8+ (for backend)
- Git (for cloning dependencies)
- Ollama

### Docker Setup (Recommended)

The easiest way to run Braille Bridge is using Docker, which requires minimal setup:

#### Using Docker Compose (Recommended)

1. Make sure you have Docker and Docker Compose installed
2. Clone the repository:
   ```bash
   git clone <repository-url>
   cd braille-bridge
   ```

3. Set up your environment file:
   ```bash
   cp backend/.env.example backend/.env
   # Edit backend/.env with your configuration
   ```

4. Build and run with Docker Compose:
   ```bash
   docker-compose up --build
   ```

5. Access the application:
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8000
   - Ollama: http://localhost:11434

#### Using Docker directly

1. Build the Docker image:
   ```bash
   docker build -t braille-bridge .
   ```

2. Run the container:
   ```bash
   docker run -p 5173:5173 -p 8000:8000 -p 11434:11434 \
     -v $(pwd)/backend/uploads:/app/backend/uploads \
     -v $(pwd)/backend/.env:/app/backend/.env \
     braille-bridge
   ```

### Local Setup

The easiest way to set up the project locally is using the automated setup script:

```bash
# Make the setup script executable
chmod +x setup.sh

# Run the setup script
./setup.sh
```

This script will:
1. Check for required prerequisites
2. Install and start Ollama service
3. Set up the Python virtual environment
4. Install liblouis library with UCS4 support
5. Install all Python dependencies
6. Set up the frontend dependencies
7. Create necessary configuration files

Remember to fill the `.env` in `backend/`

### Manual Setup

If you prefer to set up manually or the automated script fails, follow these steps:

#### Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install liblouis library:
   ```bash
   # Clone liblouis repository
   git clone https://github.com/liblouis/liblouis.git
   
   # Configure with UCS4 support
   cd liblouis
   ./configure --enable-ucs4
   
   # Build and install
   make
   sudo make install
   
   # Install Python bindings
   cd python
   python setup.py install
   cd ../..
   ```

4. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

5. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

6. Run the backend server:
   ```bash
   python app/run.py
   ```

#### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm run dev
   ```

## Features

- **Braille Processing**: Convert text to braille and vice versa using liblouis
- **Audio Processing**: Text-to-speech capabilities using Gemma models
- **Diagram Recognition**: Process and convert diagrams to accessible formats
- **Student Management**: Track student progress and assignments
- **Assignment System**: Create and manage educational assignments
- **Feedback System**: Provide feedback on student submissions

## Technology Stack

### Frontend
- React with TypeScript
- Vite for build tooling
- Modern UI components

### Backend
- FastAPI (Python)
- SQLite database
- Gemma AI models for processing
- YOLO for object detection
- Text-to-speech capabilities
- liblouis for braille translation
