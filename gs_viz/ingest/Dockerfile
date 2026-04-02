FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY ingest_server.py .

# Expose socket port
EXPOSE 5555

# Run the ingest server
CMD ["python", "-u", "ingest_server.py"]
