FROM python:3.11-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements-docker.txt pyproject.toml ./
RUN pip install --no-cache-dir -r requirements-docker.txt

COPY . .

RUN mkdir -p data data/models

ENV MPLBACKEND=Agg \
    PYTHONUNBUFFERED=1 \
    IVSURF_DB_PATH=data/ivsurf.db \
    IVSURF_DATA_DIR=data

EXPOSE 8501 8000

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || curl -f http://localhost:8501/_stcore/health

# Default: Streamlit UI (override in docker compose for API)
CMD ["streamlit", "run", "scripts/ivsurf_retro_terminal.py", "--server.port=8501", "--server.address=0.0.0.0"]
