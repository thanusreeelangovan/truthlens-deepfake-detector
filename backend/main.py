"""
TruthLens AI — Backend Entry Point
Path: backend/main.py

Day 1 scope: health check + CORS only.
Pipeline endpoints (upload, analyze) land in Day 2.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="TruthLens AI",
    description="Real-time media authenticity analysis engine",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health_check():
    return {
        "status": "online",
        "engine": "TruthLens AI",
        "version": "0.1.0",
    }