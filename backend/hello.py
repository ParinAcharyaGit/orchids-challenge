from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List
import uvicorn

# Create FastAPI instance
app = FastAPI(
    title="Orchids Challenge API",
    description="A starter FastAPI template for the Orchids Challenge backend",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # In production, replace with specific domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def main():
    """Run the application"""
    uvicorn.run(
        "hello:app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )


if __name__ == "__main__":
    main()
