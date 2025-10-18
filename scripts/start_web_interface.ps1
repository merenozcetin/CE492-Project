# SeaRoute Web Interface Launcher
Write-Host "🌊 Starting SeaRoute Web Interface..." -ForegroundColor Cyan
Write-Host ""

# Add Java to PATH for this session
$env:PATH += ";C:\Program Files\Java\jdk-25\bin"

# Check if Python is installed
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Python 3.6 or higher" -ForegroundColor Yellow
    Write-Host "Download from: https://www.python.org/downloads/" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Check if Java is installed
try {
    $javaVersion = java --version 2>&1 | Select-Object -First 1
    Write-Host "✅ Java found: $javaVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Java is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Java JDK 9 or higher" -ForegroundColor Yellow
    Write-Host "See docs\SETUP_GUIDE.md for installation instructions" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host "🚀 Starting web server..." -ForegroundColor Green
Write-Host "📱 The interface will open at: http://localhost:8080" -ForegroundColor Cyan
Write-Host "⏹️  Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

# Start the web server
try {
    Set-Location "..\web-interface"
    python searoute_server.py
} catch {
    Write-Host "❌ Failed to start server: $_" -ForegroundColor Red
    Read-Host "Press Enter to exit"
}
