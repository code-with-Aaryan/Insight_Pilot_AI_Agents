# Dockerfile for InsightPilot BI Platform
FROM python:3.11-slim

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python requirements
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY . .

# Expose ports: FastAPI (8000), Streamlit (8501)
EXPOSE 8000
EXPOSE 8501

# Run the seeding script, model training, and start services
CMD ["sh", "-c", "python scripts/generate_data.py && python scripts/train_models.py && streamlit run frontend/app.py --server.port=8501 --server.address=0.0.0.0"]
