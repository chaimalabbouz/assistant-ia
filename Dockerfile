FROM python:3.10-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY Backend ./Backend
COPY data ./data
COPY eval ./eval

WORKDIR /app/Backend

# Pour l'instant : on lance juste le test du checkpointer
CMD ["sh", "-c", "python -m app.mcp.server & sleep 5 && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]