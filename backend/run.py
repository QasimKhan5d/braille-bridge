#!/usr/bin/env python3
"""
Run the BrailleBridge Teacher API server
"""
import uvicorn

if __name__ == "__main__":
    print("Starting BrailleBridge Teacher API server...")
    print("API will be available at: http://localhost:8000")
    print("Health check: http://localhost:8000/api/health")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 