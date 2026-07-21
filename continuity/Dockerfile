FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY *.py *.html ./

ENV CONTINUITY_STORAGE_DIR=/app/storage
ENV CONTINUITY_TRANSPORT=streamable-http

EXPOSE 8000

CMD ["python", "server_lite.py"]
