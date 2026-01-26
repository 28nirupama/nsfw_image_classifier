# Stage 1: Build dependencies
FROM python:3.10-slim AS build  

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install Python dependencies (including Gunicorn) with no cache
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Stage 2: Final image with minimal footprint
FROM python:3.10-slim AS base  

# Set the working directory inside the container
WORKDIR /app

# Copy only the necessary files (installed dependencies)
COPY --from=build /app /app

# Copy the rest of the project files into the container
COPY . .

# Expose the port Flask will run on
EXPOSE 5000

# Set environment variable for production
ENV FLASK_ENV=production

# Install Gunicorn (if it's not part of requirements.txt)
RUN pip install gunicorn

# Set the default command to run the app using Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--access-logfile", "-", "app:app"]
