#!/usr/bin/env python3
"""
EU ETS Maritime Distance Calculator - Local Web Server

A simple web application for calculating maritime distances between ports worldwide.
Uses Java SeaRoute for accurate shipping routes with Great Circle fallback.

Usage:
    python app.py

Then open http://localhost:8080 in your browser
"""

import http.server
import socketserver
import json
import os
import sys
import urllib.parse
import math
from datetime import datetime

# Add tools directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'tools'))
# Set current directory to server directory
os.chdir(os.path.dirname(__file__))

try:
    from java_searoute_wrapper import JavaSeaRouteWrapper
    JAVA_AVAILABLE = True
except ImportError:
    JAVA_AVAILABLE = False

class CalculatorHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.serve_main_page()
        elif self.path.startswith('/api/calculate'):
            self.handle_calculation()
        elif self.path.startswith('/api/mrv'):
            self.handle_mrv_calculation()
        elif self.path.startswith('/api/ports'):
            self.handle_port_search()
        else:
            super().do_GET()
    
    def serve_main_page(self):
        html_content = self.get_main_page_html()
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(html_content.encode())
    
    def handle_calculation(self):
        try:
            # Parse query parameters
            query_params = urllib.parse.parse_qs(self.path.split('?')[1])
            
            origin_lat = float(query_params['origin_lat'][0])
            origin_lon = float(query_params['origin_lon'][0])
            dest_lat = float(query_params['dest_lat'][0])
            dest_lon = float(query_params['dest_lon'][0])
            
            # Calculate distances
            result = self.calculate_distances(origin_lat, origin_lon, dest_lat, dest_lon)
            
            # Send JSON response
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())
            
        except Exception as e:
            error_response = {'error': str(e)}
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(error_response).encode())
    
    def handle_port_search(self):
        try:
            query_params = urllib.parse.parse_qs(self.path.split('?')[1])
            search_term = query_params.get('q', [''])[0]
            
            # Load ports and search
            ports = self.load_ports()
            matches = self.search_ports(ports, search_term)
            
            # Send JSON response
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(matches[:10]).encode())  # Limit to 10 results
            
        except Exception as e:
            print(f"Port search error: {e}")
            error_response = {'error': str(e)}
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(error_response).encode())
    
    def calculate_distances(self, origin_lat, origin_lon, dest_lat, dest_lon):
        """Calculate distances using Java SeaRoute"""
        result = {
            'timestamp': datetime.now().isoformat(),
            'origin': {'lat': origin_lat, 'lon': origin_lon},
            'destination': {'lat': dest_lat, 'lon': dest_lon}
        }
        
        # Try Java SeaRoute if available
        if JAVA_AVAILABLE:
            try:
                java_wrapper = JavaSeaRouteWrapper()
                java_result = java_wrapper.calculate_distance(origin_lon, origin_lat, dest_lon, dest_lat)
                
                if java_result['success']:
                    result['distance'] = {
                        'distance_km': java_result['distance_km'],
                        'distance_nm': java_result['distance_nm'],
                        'method': 'Java SeaRoute (Actual Shipping Routes)',
                        'route_complexity': java_result.get('route_complexity', 0),
                        'success': True
                    }
                else:
                    result['distance'] = {
                        'error': java_result['error'],
                        'success': False
                    }
                    
            except Exception as e:
                result['distance'] = {
                    'error': str(e),
                    'success': False
                }
        else:
            result['distance'] = {
                'error': 'Java not available - please install Java to use this application',
                'success': False
            }
        
        return result
    
    def load_ports(self):
        """Load port data"""
        try:
            ports_file = 'data/ports.json'
            with open(ports_file, 'r', encoding='utf-8') as f:
                ports = json.load(f)
                print(f"Loaded {len(ports)} ports from {ports_file}")
                return ports
        except Exception as e:
            print(f"Error loading ports: {e}")
            return []
    
    def load_mrv_data(self):
        """Load MRV ship emissions data"""
        try:
            mrv_data = {}
            with open('data/mrv_data.csv', 'r', encoding='utf-8') as f:
                next(f)  # Skip header
                for line in f:
                    parts = line.strip().split(',')
                    if len(parts) >= 3:
                        imo = parts[0]
                        co2_per_nm = float(parts[1])
                        co2eq_per_nm = float(parts[2])
                        mrv_data[imo] = {
                            'co2_per_nm': co2_per_nm,
                            'co2eq_per_nm': co2eq_per_nm
                        }
            print(f"Loaded {len(mrv_data)} MRV ship records")
            return mrv_data
        except Exception as e:
            print(f"Error loading MRV data: {e}")
            return {}
    
    def load_ets_prices(self):
        """Load ETS price data"""
        try:
            prices = {}
            with open('data/ets_price.csv', 'r', encoding='utf-8') as f:
                next(f)  # Skip header
                for line in f:
                    parts = line.strip().split(',')
                    if len(parts) >= 2:
                        year = int(parts[0])
                        price = float(parts[1])
                        prices[year] = price
            print(f"Loaded ETS prices for {len(prices)} years")
            return prices
        except Exception as e:
            print(f"Error loading ETS prices: {e}")
            return {}
    
    def handle_mrv_calculation(self):
        """Handle MRV emissions and ETS cost calculation"""
        try:
            # Parse query parameters
            query_params = urllib.parse.parse_qs(self.path.split('?')[1])
            
            imo_number = query_params.get('imo', [''])[0]
            origin_lat = float(query_params.get('origin_lat', ['0'])[0])
            origin_lon = float(query_params.get('origin_lon', ['0'])[0])
            dest_lat = float(query_params.get('dest_lat', ['0'])[0])
            dest_lon = float(query_params.get('dest_lon', ['0'])[0])
            
            # Load MRV data
            mrv_data = self.load_mrv_data()
            ets_prices = self.load_ets_prices()
            
            # Get ship data
            if imo_number not in mrv_data:
                error_response = {'error': f'Ship IMO {imo_number} not found in MRV database'}
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(error_response).encode())
                return
            
            ship_data = mrv_data[imo_number]
            
            # Calculate distance
            distance_result = self.calculate_distances(origin_lat, origin_lon, dest_lat, dest_lon)
            
            if not distance_result['distance']['success']:
                error_response = {'error': f"Distance calculation failed: {distance_result['distance'].get('error', 'Unknown error')}"}
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(error_response).encode())
                return
            
            distance_nm = distance_result['distance']['distance_nm']
            
            # Calculate emissions
            co2_emissions_t = (ship_data['co2_per_nm'] * distance_nm) / 1000  # Convert kg to tonnes
            co2eq_emissions_t = (ship_data['co2eq_per_nm'] * distance_nm) / 1000
            
            # Load ports to determine ETS coverage
            ports = self.load_ports()
            origin_port = None
            dest_port = None
            
            # Find closest ports (simplified - in production would use distance calculation)
            for port in ports:
                if abs(port['lat'] - origin_lat) < 0.01 and abs(port['lon'] - origin_lon) < 0.01:
                    origin_port = port
                    break
            
            for port in ports:
                if abs(port['lat'] - dest_lat) < 0.01 and abs(port['lon'] - dest_lon) < 0.01:
                    dest_port = port
                    break
            
            # Determine ETS coverage
            origin_eea = origin_port.get('is_eea', False) if origin_port else False
            dest_eea = dest_port.get('is_eea', False) if dest_port else False
            
            if origin_eea and dest_eea:
                coverage = 1.0  # 100% intra-EEA
                coverage_text = '100% (EEA to EEA)'
            elif origin_eea or dest_eea:
                coverage = 0.5  # 50% extra-EEA
                coverage_text = '50% (Mixed route)'
            else:
                coverage = 0.0  # 0% out-of-scope
                coverage_text = '0% (Non-EEA route)'
            
            # Calculate ETS costs by year
            ets_costs = {}
            covered_co2_t = co2_emissions_t * coverage
            covered_co2eq_t = co2eq_emissions_t * coverage
            
            for year in sorted(ets_prices.keys()):
                price_eur = ets_prices[year]
                
                # Phase-in schedule
                if year == 2024:
                    phase_in = 0.40
                elif year == 2025:
                    phase_in = 0.70
                else:
                    phase_in = 1.00
                
                # Calculate cost (use CO2 for 2024-2025, CO2eq for 2026+)
                if year <= 2025:
                    cost = covered_co2_t * phase_in * price_eur
                else:
                    cost = covered_co2eq_t * phase_in * price_eur
                
                ets_costs[year] = {
                    'cost_eur': round(cost, 2),
                    'covered_emissions_t': round((covered_co2_t if year <= 2025 else covered_co2eq_t) * phase_in, 2),
                    'phase_in_pct': int(phase_in * 100),
                    'eua_price_eur': price_eur
                }
            
            # Build response
            result = {
                'timestamp': datetime.now().isoformat(),
                'imo_number': imo_number,
                'ship_data': ship_data,
                'distance': distance_result['distance'],
                'emissions': {
                    'co2_tonnes': round(co2_emissions_t, 2),
                    'co2eq_tonnes': round(co2eq_emissions_t, 2)
                },
                'ets_coverage': {
                    'percentage': int(coverage * 100),
                    'description': coverage_text,
                    'origin_eea': origin_eea,
                    'dest_eea': dest_eea
                },
                'ets_costs': ets_costs
            }
            
            # Send JSON response
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())
            
        except Exception as e:
            error_response = {'error': str(e)}
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(error_response).encode())
    
    def search_ports(self, ports, search_term):
        """Search ports by name or country"""
        if not search_term or len(search_term) < 2:
            return []
        
        search_term = search_term.lower()
        matches = []
        
        for port in ports:
            try:
                port_name = port.get('name', '').lower()
                port_country = str(port.get('country', '')).lower()
                
                if (search_term in port_name or search_term in port_country):
                    matches.append({
                        'name': port.get('name', ''),
                        'country': port.get('country', ''),
                        'lat': float(port.get('lat', 0)),
                        'lon': float(port.get('lon', 0)),
                        'is_eea': port.get('is_eea', False)
                    })
            except (ValueError, TypeError) as e:
                # Skip ports with invalid data
                continue
        
        # Sort by relevance (exact matches first)
        def sort_key(port):
            name_match = search_term in port['name'].lower()
            country_match = search_term in str(port['country']).lower()
            if name_match and country_match:
                return (0, port['name'])
            elif name_match:
                return (1, port['name'])
            else:
                return (2, port['name'])
        
        matches.sort(key=sort_key)
        return matches[:20]  # Limit results
    
    def get_main_page_html(self):
        return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>EU ETS Cost Calculator - Local</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }}
        
        .container {{
            max-width: 1000px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        
        .header h1 {{
            margin: 0;
            font-size: 2.5em;
            font-weight: 300;
        }}
        
        .content {{
            padding: 30px;
        }}
        
        .form-section {{
            background: #f8f9fa;
            padding: 25px;
            border-radius: 10px;
            margin-bottom: 30px;
        }}
        
        .form-row {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 20px;
        }}
        
        .form-group {{
            display: flex;
            flex-direction: column;
        }}
        
        .form-group label {{
            font-weight: bold;
            margin-bottom: 5px;
            color: #2c3e50;
        }}
        
        .form-group input, .form-group select {{
            padding: 12px;
            border: 2px solid #e9ecef;
            border-radius: 8px;
            font-size: 1em;
            transition: border-color 0.3s ease;
        }}
        
        .form-group input:focus, .form-group select:focus {{
            outline: none;
            border-color: #3498db;
        }}
        
        .search-results {{
            max-height: 200px;
            overflow-y: auto;
            border: 1px solid #e9ecef;
            border-radius: 8px;
            margin-top: 5px;
            display: none;
        }}
        
        .search-result {{
            padding: 10px;
            cursor: pointer;
            border-bottom: 1px solid #f8f9fa;
        }}
        
        .search-result:hover {{
            background: #e9ecef;
        }}
        
        .search-result:last-child {{
            border-bottom: none;
        }}
        
        .calculate-btn {{
            background: linear-gradient(135deg, #3498db 0%, #2980b9 100%);
            color: white;
            border: none;
            padding: 15px 30px;
            border-radius: 25px;
            font-size: 1.1em;
            cursor: pointer;
            transition: transform 0.3s ease;
            width: 100%;
            margin-top: 20px;
        }}
        
        .calculate-btn:hover {{
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(52, 152, 219, 0.4);
        }}
        
        .calculate-btn:disabled {{
            background: #bdc3c7;
            cursor: not-allowed;
            transform: none;
        }}
        
        .results {{
            display: none;
            background: white;
            border-radius: 10px;
            padding: 25px;
            margin-top: 30px;
            border: 2px solid #e9ecef;
        }}
        
        .results.show {{
            display: block;
        }}
        
        .result-method {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            margin: 15px 0;
            border-left: 5px solid #3498db;
        }}
        
        .result-method.java {{
            border-left-color: #27ae60;
            background: #e8f5e8;
        }}
        
        .method-title {{
            font-weight: bold;
            font-size: 1.2em;
            margin-bottom: 10px;
            color: #2c3e50;
        }}
        
        .distance-value {{
            font-size: 2em;
            font-weight: bold;
            color: #3498db;
            margin: 10px 0;
        }}
        
        .distance-value.java {{
            color: #27ae60;
        }}
        
        .improvement {{
            color: #27ae60;
            font-weight: bold;
            font-size: 1.1em;
        }}
        
        .loading {{
            text-align: center;
            padding: 20px;
            color: #7f8c8d;
        }}
        
        .error {{
            background: #f8d7da;
            color: #721c24;
            padding: 15px;
            border-radius: 8px;
            margin: 15px 0;
        }}
        
        .status {{
            background: #d4edda;
            color: #155724;
            padding: 15px;
            border-radius: 8px;
            margin: 15px 0;
        }}
        
        .coordinates {{
            font-family: monospace;
            background: #f8f9fa;
            padding: 10px;
            border-radius: 5px;
            margin: 10px 0;
        }}
        
        .tabs {{
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
            border-bottom: 2px solid #e9ecef;
        }}
        
        .tab-btn {{
            background: white;
            border: none;
            padding: 15px 30px;
            font-size: 1.1em;
            cursor: pointer;
            border-bottom: 3px solid transparent;
            transition: all 0.3s;
        }}
        
        .tab-btn:hover {{
            background: #f8f9fa;
        }}
        
        .tab-btn.active {{
            border-bottom-color: #3498db;
            color: #3498db;
            font-weight: bold;
        }}
        
        .tab-content {{
            display: none;
        }}
        
        .tab-content.active {{
            display: block;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🇪🇺 EU ETS Cost Calculator</h1>
            <p>Local Distance Calculation Interface</p>
        </div>
        
        <div class="content">
            <!-- Tabs -->
            <div class="tabs">
                <button class="tab-btn active" onclick="switchTab('distance')">🌊 Distance Calculation</button>
                <button class="tab-btn" onclick="switchTab('mrv')">💰 ETS Cost Calculation</button>
            </div>
            
            <!-- Distance Tab -->
            <div id="distance-tab" class="tab-content active">
            <div class="form-section">
                <h2>📍 Route Information</h2>
                
                <div class="form-row">
                    <div class="form-group">
                        <label for="origin-search">Origin Port</label>
                        <input type="text" id="origin-search" placeholder="Search for origin port..." autocomplete="off">
                        <div id="origin-results" class="search-results"></div>
                    </div>
                    
                    <div class="form-group">
                        <label for="dest-search">Destination Port</label>
                        <input type="text" id="dest-search" placeholder="Search for destination port..." autocomplete="off">
                        <div id="dest-results" class="search-results"></div>
                    </div>
                </div>
                
                <div class="form-row">
                    <div class="form-group">
                        <label>Origin Coordinates</label>
                        <div class="coordinates" id="origin-coords">Not selected</div>
                    </div>
                    
                    <div class="form-group">
                        <label>Destination Coordinates</label>
                        <div class="coordinates" id="dest-coords">Not selected</div>
                    </div>
                </div>
                
                <button class="calculate-btn" id="calculate-btn" onclick="calculateDistance()" disabled>
                    🌊 Calculate Distance
                </button>
            </div>
            
            <div id="status" class="status" style="display: none;">
                Java SeaRoute: {'Available' if JAVA_AVAILABLE else 'Not Available (using fallback)'}
            </div>
            
            <div id="results" class="results">
                <h2>📊 Distance Results</h2>
                <div id="results-content"></div>
            </div>
            </div>
            
            <!-- MRV Tab -->
            <div id="mrv-tab" class="tab-content">
                <div class="form-section">
                    <h2>🚢 Ship Information</h2>
                    
                    <div class="form-group">
                        <label for="imo-number">IMO Number</label>
                        <input type="text" id="imo-number" placeholder="Enter ship IMO number (e.g., 1013664)">
                    </div>
                    
                    <h2>📍 Route Information</h2>
                    
                    <div class="form-row">
                        <div class="form-group">
                            <label for="mrv-origin-search">Origin Port</label>
                            <input type="text" id="mrv-origin-search" placeholder="Search for origin port..." autocomplete="off">
                            <div id="mrv-origin-results" class="search-results"></div>
                        </div>
                        
                        <div class="form-group">
                            <label for="mrv-dest-search">Destination Port</label>
                            <input type="text" id="mrv-dest-search" placeholder="Search for destination port..." autocomplete="off">
                            <div id="mrv-dest-results" class="search-results"></div>
                        </div>
                    </div>
                    
                    <div class="form-row">
                        <div class="form-group">
                            <label>Origin Coordinates</label>
                            <div class="coordinates" id="mrv-origin-coords">Not selected</div>
                        </div>
                        
                        <div class="form-group">
                            <label>Destination Coordinates</label>
                            <div class="coordinates" id="mrv-dest-coords">Not selected</div>
                        </div>
                    </div>
                    
                    <button class="calculate-btn" id="mrv-calculate-btn" onclick="calculateMRV()" disabled>
                        💰 Calculate ETS Costs
                    </button>
                </div>
                
                <div id="mrv-status" class="status" style="display: none;">
                    Java SeaRoute: {'Available' if JAVA_AVAILABLE else 'Not Available'}
                </div>
                
                <div id="mrv-results" class="results">
                    <h2>📊 ETS Cost Results</h2>
                    <div id="mrv-results-content"></div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        let selectedOrigin = null;
        let selectedDestination = null;
        
        // Port search functionality
        document.getElementById('origin-search').addEventListener('input', function(e) {{
            searchPorts(e.target.value, 'origin-results', function(port) {{
                selectedOrigin = port;
                document.getElementById('origin-coords').textContent = `${{port.lat.toFixed(4)}}, ${{port.lon.toFixed(4)}}`;
                document.getElementById('origin-search').value = port.name;
                document.getElementById('origin-results').style.display = 'none';
                updateCalculateButton();
            }});
        }});
        
        document.getElementById('dest-search').addEventListener('input', function(e) {{
            searchPorts(e.target.value, 'dest-results', function(port) {{
                selectedDestination = port;
                document.getElementById('dest-coords').textContent = `${{port.lat.toFixed(4)}}, ${{port.lon.toFixed(4)}}`;
                document.getElementById('dest-search').value = port.name;
                document.getElementById('dest-results').style.display = 'none';
                updateCalculateButton();
            }});
        }});
        
        function searchPorts(query, resultsId, onSelect) {{
            if (query.length < 2) {{
                document.getElementById(resultsId).style.display = 'none';
                return;
            }}
            
            fetch(`/api/ports?q=${{encodeURIComponent(query)}}`)
                .then(response => response.json())
                .then(ports => {{
                    const resultsDiv = document.getElementById(resultsId);
                    resultsDiv.innerHTML = '';
                    
                    ports.forEach(port => {{
                        const div = document.createElement('div');
                        div.className = 'search-result';
                        div.innerHTML = `${{port.name}} (${{port.country}}) ${{port.is_eea ? '🇪🇺' : ''}}`;
                        div.onclick = () => onSelect(port);
                        resultsDiv.appendChild(div);
                    }});
                    
                    resultsDiv.style.display = ports.length > 0 ? 'block' : 'none';
                }})
                .catch(error => {{
                    console.error('Search error:', error);
                }});
        }}
        
        function updateCalculateButton() {{
            const btn = document.getElementById('calculate-btn');
            btn.disabled = !selectedOrigin || !selectedDestination;
        }}
        
        function calculateDistance() {{
            if (!selectedOrigin || !selectedDestination) return;
            
            const resultsDiv = document.getElementById('results');
            const contentDiv = document.getElementById('results-content');
            
            resultsDiv.classList.add('show');
            contentDiv.innerHTML = '<div class="loading">Calculating distances...</div>';
            
            const url = `/api/calculate?origin_lat=${{selectedOrigin.lat}}&origin_lon=${{selectedOrigin.lon}}&dest_lat=${{selectedDestination.lat}}&dest_lon=${{selectedDestination.lon}}`;
            
            fetch(url)
                .then(response => response.json())
                .then(data => {{
                    displayResults(data);
                }})
                .catch(error => {{
                    contentDiv.innerHTML = `<div class="error">Error: ${{error.message}}</div>`;
                }});
        }}
        
        function displayResults(data) {{
            const contentDiv = document.getElementById('results-content');
            let html = '';
            
            // Java SeaRoute results
            if (data.distance.success) {{
                html += `
                    <div class="result-method java">
                        <div class="method-title">🚢 Distance (Java SeaRoute - Actual Shipping Routes)</div>
                        <div class="distance-value java">${{data.distance.distance_nm}} nm</div>
                        <div>(${{data.distance.distance_km}} km)</div>
                        <div style="color: #7f8c8d; font-size: 0.9em;">Route complexity: ${{data.distance.route_complexity}} waypoints</div>
                        <div style="color: #7f8c8d; font-size: 0.9em; margin-top: 10px;">Based on actual maritime shipping routes</div>
                    </div>
                `;
            }} else {{
                html += `
                    <div class="result-method">
                        <div class="method-title">Java SeaRoute</div>
                        <div class="error">${{data.distance.error}}</div>
                    </div>
                `;
            }}
            
            // ETS Coverage
            const originEea = selectedOrigin.is_eea;
            const destEea = selectedDestination.is_eea;
            let coverage = 0;
            let coverageText = '';
            
            if (originEea && destEea) {{
                coverage = 1.0;
                coverageText = '100% (EEA to EEA)';
            }} else if (originEea || destEea) {{
                coverage = 0.5;
                coverageText = '50% (Mixed route)';
            }} else {{
                coverage = 0.0;
                coverageText = '0% (Non-EEA route)';
            }}
            
            html += `
                <div class="result-method">
                    <div class="method-title">ETS Coverage</div>
                    <div style="font-size: 1.2em; font-weight: bold; color: #e74c3c;">${{coverageText}}</div>
                    <div style="color: #7f8c8d; font-size: 0.9em;">
                        Origin EEA: ${{originEea ? 'Yes' : 'No'}}, Destination EEA: ${{destEea ? 'Yes' : 'No'}}
                    </div>
                </div>
            `;
            
            contentDiv.innerHTML = html;
        }}
        
        // Show status
        document.getElementById('status').style.display = 'block';
        
        // Tab switching
        function switchTab(tab) {{
            // Hide all tabs
            document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            
            // Show selected tab
            document.getElementById(tab + '-tab').classList.add('active');
            event.target.classList.add('active');
        }}
        
        // MRV tab variables
        let selectedMRVOrigin = null;
        let selectedMRVDestination = null;
        
        // MRV port search
        document.getElementById('mrv-origin-search').addEventListener('input', function(e) {{
            searchPorts(e.target.value, 'mrv-origin-results', function(port) {{
                selectedMRVOrigin = port;
                document.getElementById('mrv-origin-coords').textContent = `${{port.lat.toFixed(4)}}, ${{port.lon.toFixed(4)}}`;
                document.getElementById('mrv-origin-search').value = port.name;
                document.getElementById('mrv-origin-results').style.display = 'none';
                updateMRVCalculateButton();
            }});
        }});
        
        document.getElementById('mrv-dest-search').addEventListener('input', function(e) {{
            searchPorts(e.target.value, 'mrv-dest-results', function(port) {{
                selectedMRVDestination = port;
                document.getElementById('mrv-dest-coords').textContent = `${{port.lat.toFixed(4)}}, ${{port.lon.toFixed(4)}}`;
                document.getElementById('mrv-dest-search').value = port.name;
                document.getElementById('mrv-dest-results').style.display = 'none';
                updateMRVCalculateButton();
            }});
        }});
        
        function updateMRVCalculateButton() {{
            const imo = document.getElementById('imo-number').value;
            const btn = document.getElementById('mrv-calculate-btn');
            btn.disabled = !selectedMRVOrigin || !selectedMRVDestination || !imo;
        }}
        
        // Listen for IMO number input
        document.getElementById('imo-number').addEventListener('input', function() {{
            updateMRVCalculateButton();
        }});
        
        function calculateMRV() {{
            if (!selectedMRVOrigin || !selectedMRVDestination) return;
            
            const imoNumber = document.getElementById('imo-number').value;
            if (!imoNumber) return;
            
            const resultsDiv = document.getElementById('mrv-results');
            const contentDiv = document.getElementById('mrv-results-content');
            
            resultsDiv.classList.add('show');
            contentDiv.innerHTML = '<div class="loading">Calculating ETS costs...</div>';
            
            const url = `/api/mrv?imo=${{imoNumber}}&origin_lat=${{selectedMRVOrigin.lat}}&origin_lon=${{selectedMRVOrigin.lon}}&dest_lat=${{selectedMRVDestination.lat}}&dest_lon=${{selectedMRVDestination.lon}}`;
            
            fetch(url)
                .then(response => response.json())
                .then(data => {{
                    displayMRVResults(data);
                }})
                .catch(error => {{
                    contentDiv.innerHTML = `<div class="error">Error: ${{error.message}}</div>`;
                }});
        }}
        
        function displayMRVResults(data) {{
            const contentDiv = document.getElementById('mrv-results-content');
            let html = '';
            
            if (data.error) {{
                html = `<div class="error">${{data.error}}</div>`;
            }} else {{
                // Ship information
                html += `
                    <div class="result-method">
                        <div class="method-title">🚢 Ship Information</div>
                        <div>IMO: <strong>${{data.imo_number}}</strong></div>
                        <div>CO₂ per NM: <strong>${{data.ship_data.co2_per_nm.toFixed(2)}} kg/nm</strong></div>
                        <div>CO₂eq per NM: <strong>${{data.ship_data.co2eq_per_nm.toFixed(2)}} kg/nm</strong></div>
                    </div>
                `;
                
                // Distance
                if (data.distance.success) {{
                    html += `
                        <div class="result-method">
                            <div class="method-title">📏 Distance</div>
                            <div class="distance-value">${{data.distance.distance_nm.toFixed(1)}} nm</div>
                            <div>(${{data.distance.distance_km.toFixed(1)}} km)</div>
                        </div>
                    `;
                }}
                
                // Emissions
                html += `
                    <div class="result-method">
                        <div class="method-title">☁️ Total Emissions</div>
                        <div>CO₂: <strong>${{data.emissions.co2_tonnes}} tonnes</strong></div>
                        <div>CO₂eq: <strong>${{data.emissions.co2eq_tonnes}} tonnes</strong></div>
                    </div>
                `;
                
                // ETS Coverage
                html += `
                    <div class="result-method">
                        <div class="method-title">🇪🇺 ETS Coverage</div>
                        <div style="font-size: 1.2em; font-weight: bold; color: #e74c3c;">${{data.ets_coverage.description}}</div>
                    </div>
                `;
                
                // ETS Costs by Year
                html += '<div class="result-method"><div class="method-title">💰 ETS Costs by Year</div>';
                
                for (const [year, costs] of Object.entries(data.ets_costs)) {{
                    html += `
                        <div style="padding: 10px; margin: 5px 0; background: white; border-radius: 5px; border-left: 4px solid #3498db;">
                            <strong>${{year}}:</strong> €${{costs.cost_eur.toFixed(2)}}
                            <div style="font-size: 0.9em; color: #7f8c8d;">
                                ${{costs.phase_in_pct}}% phase-in, €${{costs.eua_price_eur.toFixed(2)}}/tonne
                            </div>
                        </div>
                    `;
                }}
                
                html += '</div>';
            }}
            
            contentDiv.innerHTML = html;
        }}
    </script>
</body>
</html>
        """

def main():
    PORT = 8080
    
    print("=" * 60)
    print("EU ETS COST CALCULATOR - LOCAL WEB SERVER")
    print("=" * 60)
    print(f"Java SeaRoute Available: {'Yes' if JAVA_AVAILABLE else 'No'}")
    print(f"Starting server on port {PORT}...")
    print(f"Open your browser and go to: http://localhost:{PORT}")
    print("Press Ctrl+C to stop the server")
    print("=" * 60)
    
    try:
        with socketserver.TCPServer(("", PORT), CalculatorHandler) as httpd:
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
    except Exception as e:
        print(f"Error starting server: {e}")

if __name__ == "__main__":
    main()
