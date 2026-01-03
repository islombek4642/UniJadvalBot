# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Set environment variables
# PYTHONDONTWRITEBYTECODE 1 meant to prevent Python from writing .pyc files
# PYTHONUNBUFFERED 1 meant to ensure that output is piped to logs immediately
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies (if any)
# sqlite3 is usually included in python images, but good to ensure
RUN apt-get update && apt-get install -y --no-install-recommends \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Create volume for database persistence
VOLUME ["/app/data"]

# Define the command to run the app
# Use main.py as the entry point
CMD ["python", "main.py"]
