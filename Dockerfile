FROM python:3.11-slim

# Install Java and system dependencies
RUN apt-get update && \
    apt-get install -y -q --no-install-recommends \
    default-jdk \
    ca-certificates \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Verify Java installation
RUN java -version

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all files
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

# Expose port
EXPOSE 8080

# Run the application
WORKDIR /app/server
CMD ["python", "app.py"]
