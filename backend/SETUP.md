# BrailleBridge Setup Guide

This guide will help you set up BrailleBridge after cloning from scratch.

## Environment Configuration

The application now supports environment-based configuration for easy deployment and development.

### Frontend Environment Variables

Create a `.env` file in the project root with:

```bash
# Frontend Configuration (Vite environment variables must be prefixed with VITE_)
VITE_API_BASE_URL=http://localhost:8000
VITE_FRONTEND_URL=http://localhost:5173
```

### Backend Environment Variables

Create a `.env` file in the `backend/` directory with:

```bash
# Server Configuration
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
BACKEND_RELOAD=true

# Frontend URL for CORS
FRONTEND_URL=http://localhost:5173

# Logging
LOG_LEVEL=INFO
```

## Quick Start

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd braille-bridge
   ```

2. **Set up Frontend**
   ```bash
   # Install dependencies
   npm install
   
   # Create environment file
   cp .env.example .env  # Edit as needed
   
   # Start development server
   npm run dev
   ```

3. **Set up Backend**
   ```bash
   cd backend
   
   # Create virtual environment (optional but recommended)
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   
   # Install dependencies
   pip install -r requirements.txt
   
   # Create environment file
   cp .env.example .env  # Edit as needed
   
   # Start server
   python run.py
   ```

## Production Deployment

For production deployment, update the environment variables:

### Frontend (.env)
```bash
VITE_API_BASE_URL=https://your-api-domain.com
VITE_FRONTEND_URL=https://your-frontend-domain.com
```

### Backend (.env)
```bash
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
BACKEND_RELOAD=false
FRONTEND_URL=https://your-frontend-domain.com
LOG_LEVEL=WARNING
```

## Required Files

The following files are required for the application to work:

1. **YOLO Model**: `backend/yolo11n.pt` (5.5MB) - For braille image processing
2. **Gemma Model**: Accessed via Ollama - For audio processing and translation
3. **Upload Directories**: Created automatically on startup

## Troubleshooting

### Common Issues

1. **CORS Errors**: Ensure `FRONTEND_URL` in backend matches your frontend URL
2. **API Connection Errors**: Verify `VITE_API_BASE_URL` points to your backend
3. **Missing Model Files**: Check that `yolo11n.pt` exists in `backend/` directory
4. **Port Conflicts**: Change `BACKEND_PORT` or `VITE_FRONTEND_URL` port as needed

### Environment Variables Not Working?

- Frontend: Ensure variables are prefixed with `VITE_`
- Backend: Restart the server after changing `.env` files
- Check that `.env` files are in the correct directories