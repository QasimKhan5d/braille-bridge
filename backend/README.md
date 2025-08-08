# Braille Bridge Backend

FastAPI backend for the Braille Bridge application, providing braille processing, audio generation, and educational management capabilities.

## Project Structure

```
backend/
├── app/                    # Main application code
│   ├── main.py           # FastAPI application entry point
│   ├── run.py            # Server runner
│   ├── db.py             # Database configuration
│   ├── routers/          # API route definitions
│   ├── models/           # Data models
│   ├── services/         # Business logic services
│   └── utils/            # Utility functions
├── models/               # AI/ML models
│   └── yolo11n.pt       # YOLO model for object detection
├── preprocessing/        # Data preprocessing scripts
├── scripts/             # Utility scripts
│   ├── insert_sample_submission.py
│   └── cleanup_data.py
├── docs/                # Documentation files
│   ├── diagram2json.txt
│   └── json2script.txt
├── data/                # Sample data files
├── uploads/             # File upload directory
├── gemma-3N-finetune/   # Gemma model fine-tuning
├── requirements.txt      # Python dependencies
├── .env                 # Environment variables
├── .env.example         # Environment template
└── db.json             # SQLite database
```

## Setup

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Environment Setup**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Run the Server**
   ```bash
   python app/run.py
   ```

## API Endpoints

### Braille Processing
- `POST /braille/convert` - Convert text to braille
- `POST /braille/decode` - Convert braille to text

### Audio Processing
- `POST /audio/generate` - Generate audio from text
- `POST /audio/process` - Process audio files

### Educational Management
- `GET /students` - List all students
- `POST /students` - Create new student
- `GET /assignments` - List assignments
- `POST /assignments` - Create assignment
- `GET /submissions` - List submissions
- `POST /submissions` - Submit assignment

### File Management
- `POST /upload` - Upload files
- `GET /files/{file_id}` - Download files

## Development

### Running in Development Mode
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Database
The application uses SQLite for data storage. The database file is located at `db.json`.

### Models
- **YOLO Model**: Located in `models/yolo11n.pt` for object detection
- **Gemma Models**: Fine-tuned models in `gemma-3N-finetune/`

### Scripts
Utility scripts are located in the `scripts/` directory:
- `insert_sample_submission.py` - Insert sample data
- `cleanup_data.py` - Clean up data files

## Features

- **Braille Conversion**: Text to braille and vice versa
- **Audio Generation**: Text-to-speech using Gemma models
- **Object Detection**: YOLO-based diagram processing
- **File Management**: Upload and download capabilities
- **Student Management**: Track student progress
- **Assignment System**: Create and manage educational content

## Dependencies

- FastAPI
- SQLAlchemy
- Pydantic
- Uvicorn
- PyTorch
- Transformers
- OpenCV
- NumPy
- Pandas

## Environment Variables

Create a `.env` file with the following variables:
```
DATABASE_URL=sqlite:///./db.json
UPLOAD_DIR=./uploads
MODEL_PATH=./models
```