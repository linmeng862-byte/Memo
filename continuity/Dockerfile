FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY *.py .

ENV CONTINUITY_STORAGE_DIR=/app/storage
ENV CONTINUITY_TRANSPORT=streamable-http
ENV CONTINUITY_PORT=8000

EXPOSE 8000

CMD ["sh", "-c", "python -c \"from server import mcp; mcp.run(transport='streamable-http', host='0.0.0.0', port=8000)\""]
