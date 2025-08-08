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
└── .gitignore      # Git ignore rules
```

## Getting Started

### Prerequisites

- Node.js (for frontend)
- Python 3.8+ (for backend)
- Ollama


### Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. Run the backend server:
   ```bash
   python app/run.py
   ```

### Frontend Setup

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

- **Braille Processing**: Convert text to braille and vice versa
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

## Development

### Backend Development
- Main application: `backend/app/main.py`
- Database models: `backend/app/models/`
- Services: `backend/app/services/`
- API routes: `backend/app/routers/`

### Frontend Development
- Main app: `frontend/src/App.tsx`
- Components: `frontend/src/components/`
- Pages: `frontend/src/pages/`
- Services: `frontend/src/services/`
- Utilities: `frontend/src/utils/`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test both frontend and backend
5. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
