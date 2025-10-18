#!/usr/bin/env python3
"""
SeaRoute Web Interface Backend
Simple HTTP server to handle port distance calculations
"""

import json
import subprocess
import tempfile
import os
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading
import time

class SeaRouteHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Serve the HTML interface"""
        if self.path == '/' or self.path == '/index.html':
            self.serve_html()
        else:
            self.send_error(404, "Not Found")
    
    def do_POST(self):
        """Handle distance calculation requests"""
        if self.path == '/calculate':
            self.handle_calculation()
        else:
            self.send_error(404, "Not Found")
    
    def serve_html(self):
        """Serve the HTML interface"""
        try:
            with open('port_calculator.html', 'r', encoding='utf-8') as f:
                content = f.read()
            
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(content.encode('utf-8'))
        except FileNotFoundError:
            self.send_error(404, "HTML file not found")
    
    def handle_calculation(self):
        """Handle distance calculation requests"""
        try:
            # Read request body
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            # Extract coordinates
            origin_lon = data['originLon']
            origin_lat = data['originLat']
            dest_lon = data['destLon']
            dest_lat = data['destLat']
            
            # Calculate distance
            result = self.calculate_distance(origin_lon, origin_lat, dest_lon, dest_lat)
            
            # Send response
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(result).encode('utf-8'))
            
        except Exception as e:
            self.send_error(500, f"Calculation error: {str(e)}")
    
    def calculate_distance(self, origin_lon, origin_lat, dest_lon, dest_lat):
        """Calculate distance using SeaRoute"""
        try:
            # Validate and round coordinates to 2 decimal places
            origin_lon = round(float(origin_lon), 2)
            origin_lat = round(float(origin_lat), 2)
            dest_lon = round(float(dest_lon), 2)
            dest_lat = round(float(dest_lat), 2)
            
            # Validate coordinate ranges
            if not (-180 <= origin_lon <= 180) or not (-90 <= origin_lat <= 90):
                raise ValueError("Invalid origin coordinates")
            if not (-180 <= dest_lon <= 180) or not (-90 <= dest_lat <= 90):
                raise ValueError("Invalid destination coordinates")
            
            # Create temporary CSV file in searoute directory
            searoute_dir = os.path.join('..', 'searoute-engine')
            temp_csv = os.path.join(searoute_dir, 'temp_input.csv')
            temp_output = os.path.join(searoute_dir, 'out.geojson')
            
            with open(temp_csv, 'w') as f:
                f.write('route name,olon,olat,dlon,dlat\n')
                f.write(f'Custom Route,{origin_lon},{origin_lat},{dest_lon},{dest_lat}\n')
            
            # Run SeaRoute
            searoute_path = os.path.join('..', 'searoute-engine', 'searoute.jar')
            
            if not os.path.exists(searoute_path):
                raise Exception("SeaRoute JAR file not found. Please ensure you're running from the project root.")
            
            # Get Java path
            java_path = check_java()
            if not java_path:
                raise Exception("Java not found. Please install Java JDK 9 or higher.")
            
            # Change to the searoute directory to find marnet files
            original_cwd = os.getcwd()
            
            try:
                os.chdir(searoute_dir)
                
                cmd = [
                    java_path, '-jar', 'searoute.jar',
                    '-i', 'temp_input.csv',
                    '-res', '20',  # Use 20km resolution for speed
                    '-panama', '0'
                ]
                
                # Run the command
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
                
            finally:
                # Always change back to original directory
                os.chdir(original_cwd)
            
            if result.returncode != 0:
                raise Exception(f"SeaRoute failed: {result.stderr}")
            
            # Read the output GeoJSON
            with open(temp_output, 'r', encoding='utf-8') as f:
                geojson_data = json.load(f)
            
            # Extract results
            if not geojson_data.get('features'):
                raise Exception("No route found")
            
            feature = geojson_data['features'][0]
            properties = feature['properties']
            
            # Clean up temporary files
            try:
                os.unlink(temp_csv)
                os.unlink(temp_output)
            except:
                pass
            
            return {
                'distance': round(float(properties['distKM']), 1),
                'originApprox': round(float(properties['dFromKM']), 2),
                'destApprox': round(float(properties['dToKM']), 2),
                'routeName': properties.get('route name', 'Custom Route')
            }
            
        except subprocess.TimeoutExpired:
            raise Exception("Calculation timed out. Please try again.")
        except Exception as e:
            # Clean up temporary files on error
            try:
                if 'temp_csv' in locals():
                    os.unlink(temp_csv)
                if 'temp_output' in locals():
                    os.unlink(temp_output)
            except:
                pass
            raise e
    
    def log_message(self, format, *args):
        """Override to reduce log noise"""
        pass

def check_java():
    """Check if Java is available"""
    try:
        # Try the full path first
        java_paths = [
            r"C:\Program Files\Java\jdk-25\bin\java.exe",
            "java"
        ]
        
        for java_path in java_paths:
            try:
                result = subprocess.run([java_path, '--version'], capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    return java_path
            except:
                continue
        
        return None
    except:
        return None

def check_searoute():
    """Check if SeaRoute JAR exists"""
    searoute_path = os.path.join('..', 'searoute-engine', 'searoute.jar')
    return os.path.exists(searoute_path)

def main():
    """Main function"""
    print("🌊 SeaRoute Web Interface")
    print("=" * 40)
    
    # Check prerequisites
    java_path = check_java()
    if not java_path:
        print("❌ Java not found. Please install Java JDK 9 or higher.")
        print("   See SETUP_GUIDE.md for installation instructions.")
        sys.exit(1)
    
    if not check_searoute():
        print("❌ SeaRoute JAR not found.")
        print("   Please ensure you're running from the project root directory.")
        sys.exit(1)
    
    print("✅ Java found")
    print("✅ SeaRoute JAR found")
    print()
    
    # Start server
    # Get port from environment variable (for deployment platforms)
    port = int(os.environ.get('PORT', 8080))
    server_address = ('', port)
    httpd = HTTPServer(server_address, SeaRouteHandler)
    
    print(f"🚀 Starting web server on port {port}")
    print("📱 Your SeaRoute website is now accessible!")
    print("⏹️  Press Ctrl+C to stop the server")
    print()
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped")
        httpd.shutdown()

if __name__ == '__main__':
    main()
