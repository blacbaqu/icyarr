# ---------------------------------------------------------
# icyarr Dockerfile
# Backend metadata service powering:
# - Now Playing metadata
# - Tickarr text overlays
# - M3U export
# - Future Local Game Mode (XMLTV + ESPN + icy metadata)
#
# This version assumes your backend code lives in:
#     backend/src/main.py
# ---------------------------------------------------------

# 1) Base image: lightweight Python runtime
FROM python:3.11-slim AS base

# 2) Environment settings
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    APP_HOME=/app

# 3) Create app directory
WORKDIR ${APP_HOME}

# 4) Install minimal system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# 5) Copy dependency file first (layer caching)
COPY requirements.txt ${APP_HOME}/requirements.txt

# 6) Install Python dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# 7) Copy backend source code
#    This copies the entire backend folder including src/
COPY . ${APP_HOME}

# 8) Expose FastAPI port
EXPOSE 8000

# 9) Start icyarr using uvicorn
#    Assumes:
#      - main.py contains: app = FastAPI()
#      - main.py is inside src/
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
