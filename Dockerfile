# Use official Python 3.10 slim image as a base
FROM python:3.10-slim

# Set the working directory inside the container
WORKDIR /app

# Install system dependencies needed for torch
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container
COPY requirements.txt .

# Install Python dependencies (increase timeout in case of large files)
RUN pip install --no-cache-dir -r requirements.txt --timeout=600

# Copy the rest of the project files into the container
COPY . .

# Expose the port Flask will run on
EXPOSE 5000

# Set the default command to run your app
CMD ["python", "app.py"]
