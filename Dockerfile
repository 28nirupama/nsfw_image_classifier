FROM python:3.9-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements files to the container
COPY requirements-base.txt .
COPY requirements.txt .

# Upgrade pip and setuptools to avoid version issues
RUN pip install --upgrade pip setuptools

# Install system dependencies for image processing
RUN DEBIAN_FRONTEND=noninteractive apt-get update && apt-get install -y --no-install-recommends \
    libopenblas-dev \
    libomp-dev \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    && rm -rf /var/lib/apt/lists/*

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
