FROM python:3.10-slim

WORKDIR /app

ENV FLASK_ENV=production
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies for torch + torchvision
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libstdc++6 \
    libgl1 \
    libglib2.0-0 \
    libjpeg-dev \  # Added for image processing && rm -rf /var/lib/apt/lists/*

# Copy requirements file and install dependencies
COPY requirements.txt ./

RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Copy the application code and model file into the app directory
COPY . /app

# Expose the port that Flask uses
EXPOSE 5000

# Run Gunicorn to serve the Flask app
CMD ["gunicorn", "-b", "0.0.0.0:5000", "-w", "4", "--access-logfile", "-", "--error-logfile", "-", "app:app"]
