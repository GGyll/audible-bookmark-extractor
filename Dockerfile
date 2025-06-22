FROM python:3.13-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    qt6-base-dev \
    libgl1-mesa-glx \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Expose port if needed (e.g., for future web interface)
EXPOSE 8080

# Set environment variable for QT to run in container
ENV QT_QPA_PLATFORM=offscreen

# Run the application
CMD ["python", "gui.py"] 