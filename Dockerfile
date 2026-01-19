# Use the official Python image from Docker Hub
FROM python:3.9-slim

# Set a working directory inside the container
WORKDIR /app

# Copy the requirements.txt to the container
COPY requirements.txt .

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project into the container
COPY . .

# Expose the port your app will run on (example: Flask runs on 5000)
EXPOSE 5000

# Set the entrypoint (this runs your app when the container starts)
CMD ["python", "app.py"]
