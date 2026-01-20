# Stage 1: Build dependencies
FROM python:3.9-slim AS build_stage  
# Correct capitalization

WORKDIR /app

# Copy requirements.txt to the container
COPY requirements.txt .

# Upgrade pip and install dependencies
RUN python -m pip install --upgrade pip setuptools
RUN python -m pip install --no-cache-dir -r requirements.txt

# Stage 2: Final image
FROM python:3.9-slim

WORKDIR /app

# Copy the installed dependencies from the build_stage
COPY --from=build_stage /app /app

# Expose port 5000
EXPOSE 5000

# Run the app
CMD ["python", "app.py"]
