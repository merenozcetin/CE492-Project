#!/bin/bash
set -e

echo "========================================="
echo "Building EU ETS Maritime Calculator"
echo "========================================="

# Install system dependencies
echo "Installing Java..."
apt-get update
apt-get install -y openjdk-17-jdk

# Verify Java installation
echo "Verifying Java installation..."
java -version

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

echo "========================================="
echo "Build complete!"
echo "========================================="
