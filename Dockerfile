# Use Ubuntu as base image for better compatibility with liblouis
FROM ubuntu:22.04

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV NODE_ENV=development

# Install system dependencies (stable layer)
RUN apt-get update && apt-get install -y \
    curl \
    git \
    python3 \
    python3-pip \
    python3-venv \
    nodejs \
    npm \
    build-essential \
    autoconf \
    automake \
    libtool \
    pkg-config \
    libyaml-dev \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js 18.x using official binary (stable layer)
RUN curl -fsSL https://nodejs.org/dist/v18.20.8/node-v18.20.8-linux-$(uname -m | sed 's/x86_64/x64/;s/aarch64/arm64/').tar.xz -o node.tar.xz \
    && tar -xJf node.tar.xz -C /usr/local --strip-components=1 \
    && rm node.tar.xz

# Install Ollama (stable layer)
RUN curl -fsSL https://ollama.ai/install.sh | sh

# Pre-download Ollama Gemma3N model (stable layer - only rebuild if model changes)
RUN ollama serve & \
    sleep 5 && \
    ollama pull gemma3n && \
    pkill ollama

# Set working directory
WORKDIR /app

# Copy package files first for better caching
COPY frontend/package*.json ./frontend/
COPY backend/requirements.txt ./backend/

# Install frontend dependencies (stable layer - only rebuild if package.json changes)
WORKDIR /app/frontend
RUN npm install

# Install backend dependencies (stable layer - only rebuild if requirements.txt changes)
WORKDIR /app/backend
# Create a stable venv path outside the app tree so later COPY doesn't overwrite it
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --upgrade pip && pip install -r requirements.txt

# Configure Hugging Face cache for both build and runtime
ENV TRANSFORMERS_CACHE=/opt/hf-cache \
    HF_HOME=/opt/hf-cache
RUN mkdir -p /opt/hf-cache

# Pre-download Gemma 3N model using a build arg token (stable layer - only rebuild if model/token changes)
ARG HUGGING_FACE_HUB_TOKEN
RUN HUGGING_FACE_HUB_TOKEN=$HUGGING_FACE_HUB_TOKEN /opt/venv/bin/python -c "import os, pathlib; from huggingface_hub import snapshot_download; cache_dir=os.environ.get('TRANSFORMERS_CACHE','/opt/hf-cache'); pathlib.Path(cache_dir).mkdir(parents=True, exist_ok=True); tok=os.environ.get('HUGGING_FACE_HUB_TOKEN'); assert tok, 'HUGGING_FACE_HUB_TOKEN build-arg is required to pre-download google/gemma-3n-e4b-it'; snapshot_download(repo_id='google/gemma-3n-e4b-it', token=tok, local_dir=os.path.join(cache_dir, 'models--google--gemma-3n-e4b-it'), local_dir_use_symlinks=False)"

# Install liblouis from release (stable layer - only rebuild if liblouis version changes)
RUN curl -fsSL https://github.com/liblouis/liblouis/releases/download/v3.34.0/liblouis-3.34.0.zip -o liblouis.zip \
    && unzip liblouis.zip \
    && cd liblouis-3.34.0 \
    && ./configure --enable-ucs4 \
    && make \
    && make install \
    && ldconfig \
    && cd python \
    && python setup.py install \
    && cd /app/backend \
    && rm -rf liblouis-3.34.0 liblouis.zip

# Copy application code (changes frequently - put last)
WORKDIR /app
COPY . .

# Create necessary directories
RUN mkdir -p /app/backend/uploads

# Set up environment file
RUN if [ ! -f /app/backend/.env ]; then \
        cp /app/backend/.env.example /app/backend/.env 2>/dev/null || echo "# Environment file" > /app/backend/.env; \
    fi

# Create startup script
COPY <<'EOF' /app/start.sh
#!/bin/bash

set -e

echo "🚀 Starting Braille Bridge Services..."

# Start Ollama service
echo "🤖 Starting Ollama service..."
ollama serve &
OLLAMA_PID=$!

# Wait for Ollama to be ready
echo "Waiting for Ollama to be ready..."
sleep 10

# Start backend
echo "🔧 Starting Backend..."
cd /app/backend
PYTHONPATH=/app/backend HUGGING_FACE_HUB_TOKEN=$HUGGING_FACE_HUB_TOKEN /opt/venv/bin/python app/run.py &
BACKEND_PID=$!

# Wait for backend to be ready
echo "Waiting for backend to be ready..."
sleep 5

# Start frontend
echo "🎨 Starting Frontend..."
cd /app/frontend
npm run dev -- --host 0.0.0.0 --port 5173 &
FRONTEND_PID=$!

echo "✅ All services started!"
echo "Frontend: http://localhost:5173"
echo "Backend: http://localhost:8000"
echo "Ollama: http://localhost:11434"

# Wait for any process to exit
wait -n

# Exit with status of process that exited first
exit $?
EOF

RUN chmod +x /app/start.sh

# Expose ports
EXPOSE 5173 8000 11434

# Set the default command
CMD ["/app/start.sh"]
