# Dockerfile for ECOMMERCE Python microservices
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1

# Ensure PYTHONPATH includes /app for module resolution
ENV PYTHONPATH=/app

CMD ["tail", "-f", "/dev/null"]
