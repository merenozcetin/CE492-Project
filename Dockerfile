# Use Python 3.13 base image
FROM python:3.13-slim

# Install Java (required for SeaRoute)
RUN apt-get update && apt-get install -y \
    openjdk-17-jdk \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project
COPY . .

# Set Java environment
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
ENV PATH=$JAVA_HOME/bin:$PATH

# Expose port (will be set by platform)
EXPOSE 8080

# Run the web server
CMD ["python", "web-interface/searoute_server.py"]
