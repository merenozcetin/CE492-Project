#!/usr/bin/env python3
"""
SeaRoute Maritime Distance Calculator - Flask Web App
Web application for calculating maritime distances between ports worldwide.

Usage:
    python searoute_flask_app.py
"""

from flask import Flask, render_template, request, jsonify
import json
import subprocess
import os
import re
from typing import Dict, List, Optional
from dataclasses import dataclass

@dataclass
class Port:
    """Port information"""
    name: str
    country: str
    region: str
    lon: float
    lat: float
    alternate: Optional[str] = None

@dataclass
class RouteResult:
    """Maritime route calculation result"""
    origin: Port
    destination: Port
    distance_nm: float
    origin_approx_km: float
    dest_approx_km: float
    route_name: str

class SeaRouteCalculator:
    """Main SeaRoute distance calculator"""
    
    def __init__(self):
        self.ports = []
        self.searoute_jar_path = self._find_searoute_jar()
        self.java_path = None
        self._load_ports()
        self._setup_searoute()
    
    def _find_searoute_jar(self) -> str:
        """Find SeaRoute JAR file in multiple possible locations"""
        possible_paths = [
            'searoute-engine/searoute.jar',
            'searoute.jar',
            '../searoute-engine/searoute.jar',
            './searoute-engine/searoute.jar',
            'modules/jar/release/searoute/searoute.jar'
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
        
        return 'searoute-engine/searoute.jar'  # Default fallback
    
    def _find_port_data(self) -> str:
        """Find port data HTML file in multiple possible locations"""
        possible_paths = [
            'web-interface/port_calculator.html',
            'port_calculator.html',
            '../web-interface/port_calculator.html',
            './web-interface/port_calculator.html'
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
        
        return 'web-interface/port_calculator.html'  # Default fallback
    
    def _load_ports(self):
        """Load port database from the web interface HTML file"""
        # Find port data file
        html_file = self._find_port_data()
        if not os.path.exists(html_file):
            print(f"❌ Port data source not found: {html_file}")
            return
        
        with open(html_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract ports array from JavaScript
        start_marker = 'const ports = ['
        end_marker = '];'
        
        start_pos = content.find(start_marker)
        end_pos = content.find(end_marker, start_pos)
        
        if start_pos == -1 or end_pos == -1:
            print("❌ Could not find ports array in HTML file")
            return
        
        ports_js = content[start_pos + len(start_marker):end_pos]
        
        # Parse JavaScript port objects
        port_lines = ports_js.strip().split('\n')
        for line in port_lines:
            line = line.strip()
            if line.startswith('{') and line.endswith(','):
                line = line[:-1]  # Remove trailing comma
            elif line.startswith('{') and line.endswith('}'):
                pass  # Keep as is
            
            try:
                # Simple parsing of JavaScript object
                if 'name:' in line and 'country:' in line:
                    # Extract values using string manipulation
                    name_start = line.find('"', line.find('name:')) + 1
                    name_end = line.find('"', name_start)
                    name = line[name_start:name_end]
                    
                    country_start = line.find('"', line.find('country:')) + 1
                    country_end = line.find('"', country_start)
                    country = line[country_start:country_end]
                    
                    region_start = line.find('"', line.find('region:')) + 1
                    region_end = line.find('"', region_start)
                    region = line[region_start:region_end]
                    
                    lon_start = line.find('lon:') + 4
                    lon_end = line.find(',', lon_start)
                    lon = float(line[lon_start:lon_end])
                    
                    lat_start = line.find('lat:') + 4
                    lat_end = line.find('}', lat_start)
                    lat = float(line[lat_start:lat_end])
                    
                    # Check for alternate name
                    alternate = None
                    if 'alternate:' in line:
                        alt_start = line.find('"', line.find('alternate:')) + 1
                        alt_end = line.find('"', alt_start)
                        alternate = line[alt_start:alt_end]
                    
                    port = Port(
                        name=name,
                        country=country,
                        region=region,
                        lon=lon,
                        lat=lat,
                        alternate=alternate
                    )
                    self.ports.append(port)
                    
            except (ValueError, IndexError) as e:
                continue  # Skip malformed lines
    
    def _setup_searoute(self):
        """Setup SeaRoute Java engine"""
        # Find Java
        java_paths = [
            'java',  # Try PATH first
            '/usr/bin/java',
            '/usr/local/bin/java',
            'C:\\Program Files\\Java\\jdk-25\\bin\\java.exe',
            'C:\\Program Files\\Java\\jdk-17\\bin\\java.exe',
            'C:\\Program Files\\Java\\jdk-11\\bin\\java.exe',
            'C:\\Program Files\\Java\\jdk-9\\bin\\java.exe'
        ]
        
        for java_path in java_paths:
            try:
                if java_path == 'java':
                    result = subprocess.run([java_path, '-version'], capture_output=True, text=True)
                    if result.returncode == 0:
                        self.java_path = java_path
                        break
                else:
                    if os.path.exists(java_path):
                        result = subprocess.run([java_path, '-version'], capture_output=True, text=True)
                        if result.returncode == 0:
                            self.java_path = java_path
                            break
            except (FileNotFoundError, subprocess.SubprocessError):
                continue
        
        if not self.java_path:
            print("❌ Java not found. Please install Java JDK 9 or higher.")
            return
    
    def search_ports(self, query: str, limit: int = 10) -> List[Port]:
        """Search ports by name, country, or region"""
        query = query.lower()
        matches = []
        
        for port in self.ports:
            if (query in port.name.lower() or 
                query in port.country.lower() or 
                query in port.region.lower() or
                (port.alternate and query in port.alternate.lower())):
                matches.append(port)
        
        return matches[:limit]
    
    def calculate_distance(self, origin_lon: float, origin_lat: float, 
                          dest_lon: float, dest_lat: float) -> RouteResult:
        """Calculate maritime distance using SeaRoute"""
        
        if not self.searoute_jar_path or not self.java_path:
            raise Exception("SeaRoute engine not properly configured")
        
        # Round coordinates to 2 decimal places
        origin_lon = round(origin_lon, 2)
        origin_lat = round(origin_lat, 2)
        dest_lon = round(dest_lon, 2)
        dest_lat = round(dest_lat, 2)
        
        # Create temporary CSV file
        temp_csv = 'temp_input.csv'
        temp_output = 'out.geojson'
        
        try:
            # Create input CSV
            with open(temp_csv, 'w', newline='') as f:
                f.write('route name,olon,olat,dlon,dlat\n')
                f.write(f'Custom Route,{origin_lon},{origin_lat},{dest_lon},{dest_lat}\n')
            
            # Change to searoute directory
            original_cwd = os.getcwd()
            searoute_dir = os.path.dirname(self.searoute_jar_path)
            
            if not os.path.exists(searoute_dir):
                raise Exception(f"SeaRoute directory not found: {searoute_dir}")
            
            os.chdir(searoute_dir)
            
            try:
                # Run SeaRoute
                jar_name = os.path.basename(self.searoute_jar_path)
                cmd = [self.java_path, '-jar', jar_name, temp_csv]
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
                
                if result.returncode != 0:
                    raise Exception(f"SeaRoute failed: {result.stderr}")
                
                # Read output
                if not os.path.exists(temp_output):
                    raise Exception("SeaRoute did not produce output file")
                
                with open(temp_output, 'r', encoding='utf-8') as f:
                    geojson_data = json.load(f)
                
                # Extract results
                if 'features' in geojson_data and len(geojson_data['features']) > 0:
                    feature = geojson_data['features'][0]
                    properties = feature['properties']
                    
                    # Convert km to nautical miles
                    distance_km = float(properties['distKM'])
                    distance_nm = distance_km / 1.852
                    
                    origin_approx_km = float(properties['dFromKM'])
                    dest_approx_km = float(properties['dToKM'])
                    
                    # Create dummy ports for result
                    origin_port = Port("Custom Origin", "Unknown", "Unknown", origin_lon, origin_lat)
                    dest_port = Port("Custom Destination", "Unknown", "Unknown", dest_lon, dest_lat)
                    
                    return RouteResult(
                        origin=origin_port,
                        destination=dest_port,
                        distance_nm=round(distance_nm, 1),
                        origin_approx_km=round(origin_approx_km, 2),
                        dest_approx_km=round(dest_approx_km, 2),
                        route_name=properties.get('route name', 'Custom Route')
                    )
                else:
                    raise Exception("No route found in SeaRoute output")
                    
            finally:
                os.chdir(original_cwd)
                
        finally:
            # Clean up temporary files
            for temp_file in [temp_csv, temp_output]:
                if os.path.exists(temp_file):
                    try:
                        os.remove(temp_file)
                    except:
                        pass
                # Also clean up in searoute directory
                searoute_dir = os.path.dirname(self.searoute_jar_path)
                searoute_temp = os.path.join(searoute_dir, temp_file)
                if os.path.exists(searoute_temp):
                    try:
                        os.remove(searoute_temp)
                    except:
                        pass

# Initialize Flask app
app = Flask(__name__)

# Initialize calculator
calculator = SeaRouteCalculator()

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html', port_count=len(calculator.ports))

@app.route('/api/search')
def search_ports():
    """API endpoint for port search"""
    query = request.args.get('q', '')
    limit = int(request.args.get('limit', 10))
    
    if not query:
        return jsonify([])
    
    ports = calculator.search_ports(query, limit)
    
    # Convert to JSON-serializable format
    port_data = []
    for port in ports:
        port_data.append({
            'name': port.name,
            'country': port.country,
            'region': port.region,
            'lon': port.lon,
            'lat': port.lat,
            'alternate': port.alternate
        })
    
    return jsonify(port_data)

@app.route('/api/calculate', methods=['POST'])
def calculate_distance():
    """API endpoint for distance calculation"""
    try:
        data = request.get_json()
        
        origin_lon = float(data['origin_lon'])
        origin_lat = float(data['origin_lat'])
        dest_lon = float(data['dest_lon'])
        dest_lat = float(data['dest_lat'])
        
        result = calculator.calculate_distance(origin_lon, origin_lat, dest_lon, dest_lat)
        
        return jsonify({
            'success': True,
            'distance_nm': result.distance_nm,
            'distance_km': result.distance_nm * 1.852,
            'origin_approx_km': result.origin_approx_km,
            'dest_approx_km': result.dest_approx_km,
            'route_name': result.route_name
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
