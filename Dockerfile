# Use official Python 3.10 slim image as a base
FROM python:3.10-slim

# Set the working directory inside the container
WORKDIR /app

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

# Set the default command to run the app using Flask (for debugging)
CMD ["flask", "run", "--host=0.0.0.0", "--port=5000"]

