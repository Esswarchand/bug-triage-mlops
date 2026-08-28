#!/bin/bash
set -e

echo "🚀 [CONTAINER STARTUP] Fetching ONNX model artifacts from AWS S3..."
python -m src.fetch_artifacts

echo "⚡ [CONTAINER STARTUP] Starting FastAPI Application..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000