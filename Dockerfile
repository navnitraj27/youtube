FROM python:3.10-slim

# Install ffmpeg
RUN apt-get update && apt-get install -y ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy rest of the app
COPY . .

# Expose port (Railway provides PORT)
EXPOSE 8080

# Start app with gunicorn
CMD ["gunicorn", "main:app", "--bind", "0.0.0.0:8080"]

RUN pip install -U yt-dlp

