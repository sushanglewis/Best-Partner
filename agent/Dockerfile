# Best Partners Agent - LangGraph Dev Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (needed for psycopg2/redis connectors)
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python deps (use requirements.txt to ensure version consistency)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY app/ ./app/
COPY langgraph.json ./
COPY pyproject.toml ./

# Expose port 2024 as per project standards
EXPOSE 2024

# Start FastAPI via uvicorn to avoid requiring langgraph-cli in container
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "2024"]