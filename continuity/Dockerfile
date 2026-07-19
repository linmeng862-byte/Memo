FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY *.py .

# Zeabur 会把 Volume 挂载到 /app/storage
ENV CONTINUITY_STORAGE_DIR=/app/storage
ENV CONTINUITY_TRANSPORT=streamable-http
ENV HF_ENDPOINT=https://hf-mirror.com

EXPOSE 8001

CMD ["python", "start.py"]
