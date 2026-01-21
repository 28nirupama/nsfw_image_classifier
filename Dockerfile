# Use the official Python image from Docker Hub
FROM python:3.9-slim

# Set a working directory inside the container
WORKDIR /app

# Copy the requirements files into the container
COPY requirements-base.txt .
COPY requirements.txt .

# Upgrade pip and setuptools to avoid version issues
RUN pip install --upgrade pip setuptools

# Install system dependencies in batches to avoid memory issues
RUN apt-get update && apt-get install -y --no-install-recommends \
    libopenblas-dev \
    libomp-dev \
    libglib2.0-0 \
    libsm6 && rm -rf /var/lib/apt/lists/*

RUN apt-get install -y --no-install-recommends \
    libxext6 \
    libxrender-dev && rm -rf /var/lib/apt/lists/*

# Install the base dependencies first
RUN pip install --no-cache-dir -r requirements-base.txt

# Install the remaining dependencies (heavier ones) from requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project into the container
COPY . .

# Expose the port your app will run on
EXPOSE 5000

# Set the entrypoint (this runs your app when the container starts)
CMD ["python", "app.py"]
