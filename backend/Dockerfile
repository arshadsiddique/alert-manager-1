FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy startup script and make it executable
COPY startup.sh .
RUN chmod +x startup.sh

# Copy alembic configuration (alembic.ini should be in backend root)
COPY alembic.ini .
COPY alembic/ ./alembic/

# Copy application code
COPY app/ ./app/

# Create empty __init__.py files if they don't exist
RUN touch app/__init__.py \
    && touch app/models/__init__.py \
    && touch app/schemas/__init__.py \
    && touch app/services/__init__.py \
    && touch app/api/__init__.py \
    && touch app/api/routes/__init__.py \
    && touch app/core/__init__.py \
    && touch app/utils/__init__.py

EXPOSE 8000

CMD ["./startup.sh"]