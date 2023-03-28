# Base image
FROM python:3.11.2-slim-buster

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY ./src/main.py .
COPY ./src/words_to_review.txt .

# Start the application
CMD ["python", "main.py"]
