# Use the official Python image from Docker Hub
FROM python:3.9-slim

# Set a working directory inside the container
WORKDIR /app

# Copy the requirements.txt to the container
COPY requirements.txt .

# Upgrade pip and setuptools to avoid version issues (only once)
RUN pip install --upgrade pip setuptools

# Install system dependencies needed for image processing (e.g., Pillow, OpenCV)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libopenblas-dev \
    libomp-dev \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    && rm -rf /var/lib/apt/lists/*

# Install the dependencies from requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project into the container
COPY . .

# Expose the port your app will run on (Flask runs on 5000)
EXPOSE 5000

# Set the entrypoint (this runs your app when the container starts)
CMD ["python", "app.py"]