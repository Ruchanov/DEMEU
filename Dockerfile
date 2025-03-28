# Use official Python image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
     libgl1-mesa-glx \
    && rm -rf /var/lib/apt/lists/*

# Copy only requirements and install first (for caching)
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy the project (excluding venv)
COPY . .

# Expose Django default port
EXPOSE 8000

# Start Django dev server
CMD ["python", "manage.py", "runserver"]
