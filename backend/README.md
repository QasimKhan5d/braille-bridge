# BrailleBridge Backend

A FastAPI-based backend service for processing braille images, managing assignments, and providing educational tools for braille learning.

## Setup

    source venv/bin/activate
    pip install -r requirements.txt
    pip install moshi-mlx

### Setup louis (braille translator)

    cd liblouis-3.34.0
    make uninstall          # optional, cleans previous install
    make clean              # optional
    ./configure --enable-ucs4 --prefix=/opt/homebrew
    make
    sudo make install
    cd python && python setup.py install

## Architecture

### Core Services
- **FastAPI Server** (`main.py`) - REST API with CORS support for frontend integration
- **Database Layer** (`db.py`) - TinyDB-based local storage for assignments, submissions, and student profiles
- **YOLO Braille Reader** (`yolo_to_text.py`) - Computer vision pipeline for detecting and reading braille characters
- **Braille Decoder** (`braille_decoder.py`) - Converts braille patterns to Urdu text using Louis library
- **Lesson Pack Generator** (`lesson_pack_service.py`) - Creates educational content packages

### AI/ML Components
- **Gemma-3N Fine-tuned Model** - Custom model for image-to-text processing and diagram analysis
- **YOLO11n** - Object detection model trained for braille character recognition
- **TTS Services** (`tts_service.py`, `tts_mlx.py`) - Text-to-speech conversion for audio feedback

### Key Features
- **Assignment Management** - Create, distribute, and grade braille assignments
- **Auto-grading** - Automated evaluation of student submissions using AI
- **Progress Tracking** - Real-time progress monitoring with server-sent events
- **Student Analytics** - Feedback analysis and learning insights
- **Multi-format Support** - Handles images, audio, and text content

## API Endpoints

### Braille Processing
- `POST /api/process-braille` - Convert braille images to text
- `POST /api/text-to-braille` - Convert text to braille notation

### Assignment Workflow
- `POST /api/assignments` - Create new assignments
- `GET /api/assignments` - List all assignments
- `POST /api/assignments/{id}/submit` - Submit student work
- `POST /api/submissions/{id}/autograde` - Grade submissions

### Educational Tools
- `POST /api/lesson-pack` - Generate lesson packages
- `POST /api/feedback/analyze` - Analyze student performance
- `GET /api/students` - Student profile management

## Technical Stack

- **Framework**: FastAPI with Uvicorn ASGI server
- **Database**: TinyDB (JSON-based local storage)
- **Computer Vision**: Ultralytics YOLO, PIL/Pillow
- **AI/ML**: Transformers, Ollama, Gemma-3N
- **Braille Processing**: Louis library (Urdu Grade-1)
- **Audio**: TTS with MLX optimization

## Running the Server

```bash
python run.py
```

Server starts on `http://localhost:8000` with auto-reload enabled.

## Dependencies

Core dependencies include FastAPI, Ultralytics, Transformers, Louis, TinyDB, and various ML libraries. See `requirements.txt` for complete list.