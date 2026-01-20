# Use the official Python image from Docker Hub
FROM python:3.9-slim

# Set a working directory inside the container
WORKDIR /app

# Copy the requirements.txt to the container
COPY requirements.txt .

# Upgrade pip and setuptools to avoid version issues
RUN python -m pip install --upgrade pip setuptools

# Install the dependencies from requirements.txt
RUN python -m pip install --upgrade pip setuptools
RUN python -m pip install --no-cache-dir Flask==2.0.1
RUN python -m pip install --no-cache-dir torch==1.12.0
RUN python -m pip install --no-cache-dir torchvision==0.10.0
RUN python -m pip install --no-cache-dir Pillow==9.0.0
RUN python -m pip install --no-cache-dir requests==2.26.0


# Install system dependencies needed for image processing (e.g., Pillow, OpenCV)
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev

# Copy the entire project into the container
COPY . .

# Expose the port your app will run on (example: Flask runs on 5000)
EXPOSE 5000

# Set the entrypoint (this runs your app when the container starts)
CMD ["python", "app.py"]
