FROM python:3.10-slim

WORKDIR /app

ENV FLASK_ENV=production
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# REQUIRED system dependencies for torch + torchvision
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libstdc++6 \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first
COPY requirements.txt .

# Upgrade pip & install deps
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy the .env file into the container
# Copy the .env file into the container (use full path if necessary)
COPY ./.env ./.env


# Copy app code
COPY . .

EXPOSE 5000

CMD ["gunicorn", "-b", "0.0.0.0:5000", "-w", "4", "app:app"]
