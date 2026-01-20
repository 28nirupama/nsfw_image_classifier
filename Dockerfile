# Stage 1: Build dependencies
FROM python:3.9-slim as build_stage

WORKDIR /app

# Copy requirements.txt
COPY requirements.txt .

# Upgrade pip and install dependencies
RUN python -m pip install --upgrade pip setuptools
RUN python -m pip install --no-cache-dir -r requirements.txt

# Stage 2: Create the final image
FROM python:3.9-slim

WORKDIR /app

# Copy the dependencies from the build stage
COPY --from=build_stage /app /app

# Install system dependencies (optional)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libopenblas-dev \
    libomp-dev \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy the project into the final image
COPY . .

# Expose the port the app will run on (Flask on 5000)
EXPOSE 5000

# Set the entrypoint to run your Flask app
CMD ["python", "app.py"]
