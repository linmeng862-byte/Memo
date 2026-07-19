FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY *.py .

ENV CONTINUITY_STORAGE_DIR=/app/storage
ENV CONTINUITY_TRANSPORT=streamable-http

CMD ["sh", "-c", "exec python -c \"import os; from server import mcp; port=int(os.environ.get('PORT',8000)); mcp.run(transport='streamable-http',host='0.0.0.0',port=port)\""]
