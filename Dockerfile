FROM python:3.11-slim

WORKDIR /app

# S2.6: install serving requirements first (Docker caches this slow step)
COPY requirements-serving.txt .
RUN pip install --no-cache-dir -r requirements-serving.txt

# S2.7: copy only the API code and the trained model
COPY api/ ./api/
COPY models/ ./models/

ENV PORT=7860
EXPOSE 7860

CMD ["sh", "-c", "uvicorn api.main:app --host 0.0.0.0 --port ${PORT}"]