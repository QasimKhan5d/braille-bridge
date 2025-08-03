#!/usr/bin/env python3
"""
Run the BrailleBridge Teacher API server
"""
import uvicorn
import os

if __name__ == "__main__":
    # Configuration from environment variables
    host = os.getenv("BACKEND_HOST", "0.0.0.0")
    port = int(os.getenv("BACKEND_PORT", "8000"))
    reload = os.getenv("BACKEND_RELOAD", "true").lower() == "true"
    
    # Log startup message
    print("🧠 BrailleBridge Teacher API Starting...")
    print("📚 Loading models and initializing services...")
    print(f"API will be available at: http://{host}:{port}")
    print(f"Health check: http://{host}:{port}/api/health")
    print(f"API Documentation: http://{host}:{port}/docs")
    print(f"Environment: {'Development' if reload else 'Production'}")
    
    uvicorn.run("main:app", host=host, port=port, reload=reload) 