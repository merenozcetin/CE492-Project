#!/usr/bin/env python3
"""
SeaRoute Maritime Distance Calculator
Clean Flask web application for calculating maritime distances between ports worldwide.
Uses the lightweight Python SeaRoute wrapper.

Usage:
    python app.py
"""

from flask import Flask, render_template, request, jsonify
import searoute as sr
import json
import os
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

class SeaRouteCalculator:
    """Main SeaRoute distance calculator using Python wrapper"""
    
    def __init__(self):
        self.ports = []
        self._load_ports()
    
    def _load_ports(self):
        """Load port database from ports.json"""
        ports_file = 'data/ports.json'
        
        if not os.path.exists(ports_file):
            print(f"❌ Port data not found: {ports_file}")
            return
        
        try:
            with open(ports_file, 'r', encoding='utf-8') as f:
                ports_data = json.load(f)
            
            for port_data in ports_data:
                port = Port(
                    name=port_data['name'],
                    country=port_data['country'],
                    region=port_data['region'],
                    lon=port_data['lon'],
                    lat=port_data['lat'],
                    alternate=port_data.get('alternate')
                )
                self.ports.append(port)
            
            print(f"✅ Loaded {len(self.ports)} ports")
            
        except Exception as e:
            print(f"❌ Error loading ports: {e}")
    
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
                          dest_lon: float, dest_lat: float) -> Dict:
        """Calculate maritime distance using Python SeaRoute wrapper"""
        
        try:
            # Round coordinates to 2 decimal places
            origin_lon = round(origin_lon, 2)
            origin_lat = round(origin_lat, 2)
            dest_lon = round(dest_lon, 2)
            dest_lat = round(dest_lat, 2)
            
            # Define origin and destination coordinates [longitude, latitude]
            origin = [origin_lon, origin_lat]
            destination = [dest_lon, dest_lat]
            
            # Calculate the sea route using Python wrapper
            route = sr.searoute(origin, destination)
            
            # Extract distance and convert to nautical miles
            distance_km = route['properties']['length']
            distance_nm = distance_km / 1.852  # Convert km to nautical miles
            
            return {
                'success': True,
                'distance_nm': round(distance_nm, 1),
                'distance_km': round(distance_km, 1),
                'route_name': 'SeaRoute Calculation'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"SeaRoute calculation failed: {str(e)}"
            }

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
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f"Invalid input: {str(e)}"
        }), 400

@app.route('/api/status')
def status():
    """API endpoint for system status"""
    return jsonify({
        'ports_loaded': len(calculator.ports),
        'searoute_available': True,
        'status': 'ready'
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
