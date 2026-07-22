# ============================================================
# ICYARR BACKEND — Dockerfile
# ============================================================
# Builds the FastAPI backend with SQLite persistence.
# ============================================================

# Use official Python image
FROM python:3.11-slim

# Set working directory inside container
WORKDIR /app

# Copy requirements first (better caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source code
COPY src/ ./src/

# Copy SQLite database file (will be mounted as a volume)
COPY channel.db ./channel.db

# Expose backend port (internal only — NPM will NOT use this)
EXPOSE 8000

# Run FastAPI using uvicorn
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
