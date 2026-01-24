# Use official Python 3.10 slim image as a base
FROM python:3.10-slim

# Set the working directory inside the container
WORKDIR /app

# Set production environment by default
# Override with docker run -e FLASK_ENV=development for local testing
ENV FLASK_ENV=production

# Copy the requirements file into the container
COPY requirements.txt .

# Install Python dependencies (including Gunicorn)
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install gunicorn

# Copy the rest of the project files into the container
COPY . .

# Expose the port Flask will run on
EXPOSE 5000

# Set the default command to run the app using Gunicorn in production mode
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--access-logfile", "-", "app:app"]
