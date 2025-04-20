FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source files
COPY enrich.py run.sh ./
RUN chmod +x run.sh

CMD ["./run.sh"]
