#!/usr/bin/env python3
"""
Run script for SeaRoute Maritime Distance Calculator
Simple script to start the Streamlit application
"""

import subprocess
import sys
import os

def main():
    """Main function to run the Streamlit app"""
    
    # Check if we're in the right directory
    if not os.path.exists('src/app.py'):
        print("❌ Error: src/app.py not found!")
        print("Please run this script from the project root directory.")
        sys.exit(1)
    
    # Check if requirements are installed
    try:
        import streamlit
        import searoute
        print("✅ Dependencies found")
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Please run: pip install -r requirements.txt")
        sys.exit(1)
    
    # Start the Streamlit app
    print("🚀 Starting SeaRoute Maritime Distance Calculator...")
    print("📱 Open your browser to: http://localhost:8501")
    print("🛑 Press Ctrl+C to stop the application")
    
    try:
        subprocess.run([
            sys.executable, '-m', 'streamlit', 'run', 'src/app.py',
            '--server.port=8501',
            '--server.address=localhost'
        ])
    except KeyboardInterrupt:
        print("\n👋 Application stopped by user")
    except Exception as e:
        print(f"❌ Error starting application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
