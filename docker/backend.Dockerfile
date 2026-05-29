FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Set PYTHONPATH to include the current directory
ENV PYTHONPATH=/app

# Default command: start the FastAPI server
CMD ["uvicorn", "personaforge.backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
