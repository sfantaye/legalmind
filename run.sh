#!/bin/bash
# run.sh
echo "Starting LegalMind FastAPI server..."
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
