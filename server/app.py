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
    <title>Maritime Distance & ETS Calculator</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: #f8fafc;
            color: #1e293b;
            line-height: 1.6;
            min-height: 100vh;
        }}
        
        .header {{
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
            color: white;
            padding: 2rem 1.5rem;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }}
        
        .header-content {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        
        .header h1 {{
            font-size: 1.875rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
            letter-spacing: -0.025em;
        }}
        
        .header p {{
            font-size: 0.95rem;
            color: #94a3b8;
            font-weight: 400;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 2rem 1.5rem;
        }}
        
        .tabs {{
            display: flex;
            gap: 0.5rem;
            margin-bottom: 2rem;
            border-bottom: 2px solid #e2e8f0;
            overflow-x: auto;
        }}
        
        .tab-btn {{
            background: transparent;
            border: none;
            padding: 0.875rem 1.5rem;
            font-size: 0.95rem;
            font-weight: 500;
            cursor: pointer;
            border-bottom: 3px solid transparent;
            transition: all 0.2s;
            color: #64748b;
            white-space: nowrap;
        }}
        
        .tab-btn:hover {{
            color: #0f172a;
            background: #f1f5f9;
        }}
        
        .tab-btn.active {{
            border-bottom-color: #0ea5e9;
            color: #0ea5e9;
        }}
        
        .tab-content {{
            display: none;
        }}
        
        .tab-content.active {{
            display: block;
        }}
        
        .card {{
            background: white;
            border-radius: 12px;
            padding: 2rem;
            box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
            margin-bottom: 1.5rem;
        }}
        
        .card-title {{
            font-size: 1.25rem;
            font-weight: 600;
            margin-bottom: 1.5rem;
            color: #0f172a;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}
        
        .form-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 1.5rem;
            margin-bottom: 1.5rem;
        }}
        
        .form-group {{
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
        }}
        
        .form-label {{
            font-weight: 500;
            font-size: 0.875rem;
            color: #475569;
            text-transform: uppercase;
            letter-spacing: 0.025em;
        }}
        
        .form-input {{
            padding: 0.75rem 1rem;
            border: 2px solid #e2e8f0;
            border-radius: 8px;
            font-size: 1rem;
            transition: all 0.2s;
            font-family: inherit;
            background: white;
        }}
        
        .form-input:focus {{
            outline: none;
            border-color: #0ea5e9;
            box-shadow: 0 0 0 3px rgba(14, 165, 233, 0.1);
        }}
        
        .search-results {{
            max-height: 240px;
            overflow-y: auto;
            border: 2px solid #e2e8f0;
            border-radius: 8px;
            margin-top: 0.5rem;
            display: none;
            background: white;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }}
        
        .search-result {{
            padding: 0.875rem 1rem;
            cursor: pointer;
            border-bottom: 1px solid #f1f5f9;
            transition: background 0.15s;
            font-size: 0.9rem;
        }}
        
        .search-result:hover {{
            background: #f8fafc;
        }}
        
        .search-result:last-child {{
            border-bottom: none;
        }}
        
        .coordinates-display {{
            font-family: 'Courier New', monospace;
            background: #f1f5f9;
            padding: 0.75rem 1rem;
            border-radius: 8px;
            font-size: 0.875rem;
            color: #475569;
            border: 2px solid #e2e8f0;
        }}
        
        .btn-primary {{
            background: linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%);
            color: white;
            border: none;
            padding: 1rem 2rem;
            border-radius: 8px;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
            width: 100%;
            margin-top: 1rem;
            box-shadow: 0 4px 6px -1px rgba(14, 165, 233, 0.3);
        }}
        
        .btn-primary:hover:not(:disabled) {{
            transform: translateY(-2px);
            box-shadow: 0 10px 15px -3px rgba(14, 165, 233, 0.4);
        }}
        
        .btn-primary:disabled {{
            background: #cbd5e1;
            cursor: not-allowed;
            box-shadow: none;
        }}
        
        .status-badge {{
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            background: #dbeafe;
            color: #1e40af;
            padding: 0.5rem 1rem;
            border-radius: 6px;
            font-size: 0.875rem;
            font-weight: 500;
            margin-bottom: 1.5rem;
        }}
        
        .status-badge.success {{
            background: #dcfce7;
            color: #166534;
        }}
        
        .results {{
            display: none;
        }}
        
        .results.show {{
            display: block;
        }}
        
        .result-card {{
            background: white;
            border-radius: 12px;
            padding: 1.5rem;
            margin-bottom: 1rem;
            border: 2px solid #e2e8f0;
            transition: all 0.2s;
        }}
        
        .result-card:hover {{
            border-color: #cbd5e1;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }}
        
        .result-card.primary {{
            border-color: #0ea5e9;
            background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
        }}
        
        .result-header {{
            font-weight: 600;
            font-size: 1rem;
            margin-bottom: 1rem;
            color: #0f172a;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}
        
        .result-value {{
            font-size: 2.5rem;
            font-weight: 700;
            color: #0ea5e9;
            margin: 0.5rem 0;
            line-height: 1;
        }}
        
        .result-subtitle {{
            font-size: 1.125rem;
            color: #64748b;
            margin-bottom: 0.5rem;
        }}
        
        .result-meta {{
            color: #64748b;
            font-size: 0.875rem;
            margin-top: 0.5rem;
        }}
        
        .loading {{
            text-align: center;
            padding: 3rem;
            color: #64748b;
        }}
        
        .loading::after {{
            content: '...';
            animation: dots 1.5s steps(4, end) infinite;
        }}
        
        @keyframes dots {{
            0%, 20% {{ content: '.'; }}
            40% {{ content: '..'; }}
            60%, 100% {{ content: '...'; }}
        }}
        
        .error {{
            background: #fee2e2;
            color: #991b1b;
            padding: 1rem 1.25rem;
            border-radius: 8px;
            margin: 1rem 0;
            border-left: 4px solid #dc2626;
            font-size: 0.9rem;
        }}
        
        .cost-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
            gap: 1rem;
            margin-top: 1rem;
        }}
        
        .cost-item {{
            background: white;
            padding: 1rem;
            border-radius: 8px;
            border: 2px solid #e2e8f0;
        }}
        
        .cost-year {{
            font-weight: 600;
            font-size: 1.125rem;
            color: #0f172a;
            margin-bottom: 0.5rem;
        }}
        
        .cost-amount {{
            font-size: 1.5rem;
            font-weight: 700;
            color: #0ea5e9;
            margin-bottom: 0.25rem;
        }}
        
        .cost-details {{
            font-size: 0.8rem;
            color: #64748b;
        }}
        
        .metric-row {{
            display: flex;
            justify-content: space-between;
            padding: 0.75rem 0;
            border-bottom: 1px solid #f1f5f9;
        }}
        
        .metric-row:last-child {{
            border-bottom: none;
        }}
        
        .metric-label {{
            color: #64748b;
            font-size: 0.9rem;
        }}
        
        .metric-value {{
            font-weight: 600;
            color: #0f172a;
        }}
        
        @media (max-width: 768px) {{
            .header h1 {{
                font-size: 1.5rem;
            }}
            
            .form-grid {{
                grid-template-columns: 1fr;
            }}
            
            .result-value {{
                font-size: 2rem;
            }}
            
            .cost-grid {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <div class="header-content">
            <h1>⚓ Maritime Distance & ETS Calculator</h1>
            <p>Calculate shipping distances and EU Emissions Trading System costs</p>
        </div>
    </div>
    
    <div class="container">
        <div class="tabs">
            <button class="tab-btn active" onclick="switchTab('mrv')">💰 ETS Cost Calculation</button>
            <button class="tab-btn" onclick="switchTab('distance')">🌊 Distance Calculation</button>
        </div>
        
        <!-- MRV Tab -->
        <div id="mrv-tab" class="tab-content active">
            <div class="card">
                <h2 class="card-title">🚢 Ship Information</h2>
                
                <div class="form-group">
                    <label class="form-label" for="imo-number">IMO Number</label>
                    <input type="text" id="imo-number" class="form-input" placeholder="Enter ship IMO number (e.g., 1013664)">
                </div>
            </div>
            
            <div class="card">
                <h2 class="card-title">📍 Route Information</h2>
                
                <div class="form-grid">
                    <div class="form-group">
                        <label class="form-label" for="mrv-origin-search">Origin Port</label>
                        <input type="text" id="mrv-origin-search" class="form-input" placeholder="Search for origin port..." autocomplete="off">
                        <div id="mrv-origin-results" class="search-results"></div>
                        <div class="coordinates-display" id="mrv-origin-coords">Not selected</div>
                    </div>
                    
                    <div class="form-group">
                        <label class="form-label" for="mrv-dest-search">Destination Port</label>
                        <input type="text" id="mrv-dest-search" class="form-input" placeholder="Search for destination port..." autocomplete="off">
                        <div id="mrv-dest-results" class="search-results"></div>
                        <div class="coordinates-display" id="mrv-dest-coords">Not selected</div>
                    </div>
                </div>
                
                <button class="btn-primary" id="mrv-calculate-btn" onclick="calculateMRV()" disabled>
                    💰 Calculate ETS Costs
                </button>
            </div>
            
            <div class="status-badge {'success' if JAVA_AVAILABLE else ''}">
                <span>{'✓' if JAVA_AVAILABLE else '⚠'}</span>
                Java SeaRoute: {'Available' if JAVA_AVAILABLE else 'Not Available'}
            </div>
            
            <div id="mrv-results" class="results">
                <div id="mrv-results-content"></div>
            </div>
        </div>
        
        <!-- Distance Tab -->
        <div id="distance-tab" class="tab-content">
            <div class="card">
                <h2 class="card-title">📍 Route Information</h2>
                
                <div class="form-grid">
                    <div class="form-group">
                        <label class="form-label" for="origin-search">Origin Port</label>
                        <input type="text" id="origin-search" class="form-input" placeholder="Search for origin port..." autocomplete="off">
                        <div id="origin-results" class="search-results"></div>
                        <div class="coordinates-display" id="origin-coords">Not selected</div>
                    </div>
                    
                    <div class="form-group">
                        <label class="form-label" for="dest-search">Destination Port</label>
                        <input type="text" id="dest-search" class="form-input" placeholder="Search for destination port..." autocomplete="off">
                        <div id="dest-results" class="search-results"></div>
                        <div class="coordinates-display" id="dest-coords">Not selected</div>
                    </div>
                </div>
                
                <button class="btn-primary" id="calculate-btn" onclick="calculateDistance()" disabled>
                    🌊 Calculate Distance
                </button>
            </div>
            
            <div class="status-badge {'success' if JAVA_AVAILABLE else ''}">
                <span>{'✓' if JAVA_AVAILABLE else '⚠'}</span>
                Java SeaRoute: {'Available' if JAVA_AVAILABLE else 'Not Available'}
            </div>
            
            <div id="results" class="results">
                <div id="results-content"></div>
            </div>
        </div>
    </div>
    
    <script>
        let selectedOrigin = null;
        let selectedDestination = null;
        let selectedMRVOrigin = null;
        let selectedMRVDestination = null;
        
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
        
        document.getElementById('imo-number').addEventListener('input', function() {{
            updateMRVCalculateButton();
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
        
        function updateMRVCalculateButton() {{
            const imo = document.getElementById('imo-number').value;
            const btn = document.getElementById('mrv-calculate-btn');
            btn.disabled = !selectedMRVOrigin || !selectedMRVDestination || !imo;
        }}
        
        function switchTab(tab) {{
            document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            
            document.getElementById(tab + '-tab').classList.add('active');
            event.target.classList.add('active');
        }}
        
        function calculateDistance() {{
            if (!selectedOrigin || !selectedDestination) return;
            
            const resultsDiv = document.getElementById('results');
            const contentDiv = document.getElementById('results-content');
            
            resultsDiv.classList.add('show');
            contentDiv.innerHTML = '<div class="loading">Calculating distances</div>';
            
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
            
            if (data.distance.success) {{
                html += `
                    <div class="result-card primary">
                        <div class="result-header">🚢 Maritime Distance</div>
                        <div class="result-value">${{data.distance.distance_nm.toFixed(1)}} <span style="font-size: 1.5rem; color: #64748b;">nm</span></div>
                        <div class="result-subtitle">${{data.distance.distance_km.toFixed(1)}} kilometers</div>
                        <div class="result-meta">Route complexity: ${{data.distance.route_complexity}} waypoints</div>
                        <div class="result-meta">Method: Java SeaRoute (Actual Shipping Routes)</div>
                    </div>
                `;
            }} else {{
                html += `<div class="error">${{data.distance.error}}</div>`;
            }}
            
            const originEea = selectedOrigin.is_eea;
            const destEea = selectedDestination.is_eea;
            let coverageText = '';
            
            if (originEea && destEea) {{
                coverageText = '100% (EEA to EEA)';
            }} else if (originEea || destEea) {{
                coverageText = '50% (Mixed route)';
            }} else {{
                coverageText = '0% (Non-EEA route)';
            }}
            
            html += `
                <div class="result-card">
                    <div class="result-header">🇪🇺 ETS Coverage</div>
                    <div class="result-value" style="font-size: 2rem;">${{coverageText}}</div>
                    <div class="metric-row">
                        <span class="metric-label">Origin EEA Status</span>
                        <span class="metric-value">${{originEea ? 'Yes' : 'No'}}</span>
                    </div>
                    <div class="metric-row">
                        <span class="metric-label">Destination EEA Status</span>
                        <span class="metric-value">${{destEea ? 'Yes' : 'No'}}</span>
                    </div>
                </div>
            `;
            
            contentDiv.innerHTML = html;
        }}
        
        function calculateMRV() {{
            if (!selectedMRVOrigin || !selectedMRVDestination) return;
            
            const imoNumber = document.getElementById('imo-number').value;
            if (!imoNumber) return;
            
            const resultsDiv = document.getElementById('mrv-results');
            const contentDiv = document.getElementById('mrv-results-content');
            
            resultsDiv.classList.add('show');
            contentDiv.innerHTML = '<div class="loading">Calculating ETS costs</div>';
            
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
                html += `
                    <div class="result-card">
                        <div class="result-header">🚢 Ship Information</div>
                        <div class="metric-row">
                            <span class="metric-label">IMO Number</span>
                            <span class="metric-value">${{data.imo_number}}</span>
                        </div>
                        <div class="metric-row">
                            <span class="metric-label">CO₂ per Nautical Mile</span>
                            <span class="metric-value">${{data.ship_data.co2_per_nm.toFixed(2)}} kg/nm</span>
                        </div>
                        <div class="metric-row">
                            <span class="metric-label">CO₂eq per Nautical Mile</span>
                            <span class="metric-value">${{data.ship_data.co2eq_per_nm.toFixed(2)}} kg/nm</span>
                        </div>
                    </div>
                `;
                
                if (data.distance.success) {{
                    html += `
                        <div class="result-card primary">
                            <div class="result-header">📏 Distance</div>
                            <div class="result-value">${{data.distance.distance_nm.toFixed(1)}} <span style="font-size: 1.5rem; color: #64748b;">nm</span></div>
                            <div class="result-subtitle">${{data.distance.distance_km.toFixed(1)}} kilometers</div>
                        </div>
                    `;
                }}
                
                html += `
                    <div class="result-card">
                        <div class="result-header">☁️ Total Emissions</div>
                        <div class="metric-row">
                            <span class="metric-label">CO₂ Emissions</span>
                            <span class="metric-value">${{data.emissions.co2_tonnes}} tonnes</span>
                        </div>
                        <div class="metric-row">
                            <span class="metric-label">CO₂eq Emissions</span>
                            <span class="metric-value">${{data.emissions.co2eq_tonnes}} tonnes</span>
                        </div>
                    </div>
                    
                    <div class="result-card">
                        <div class="result-header">🇪🇺 ETS Coverage</div>
                        <div class="result-value" style="font-size: 2rem;">${{data.ets_coverage.description}}</div>
                        <div class="metric-row">
                            <span class="metric-label">Origin EEA Status</span>
                            <span class="metric-value">${{data.ets_coverage.origin_eea ? 'Yes 🇪🇺' : 'No'}}</span>
                        </div>
                        <div class="metric-row">
                            <span class="metric-label">Destination EEA Status</span>
                            <span class="metric-value">${{data.ets_coverage.dest_eea ? 'Yes 🇪🇺' : 'No'}}</span>
                        </div>
                    </div>
                    
                    <div class="result-card">
                        <div class="result-header">💰 ETS Costs by Year</div>
                        <div class="cost-grid">
                `;
                
                for (const [year, costs] of Object.entries(data.ets_costs)) {{
                    html += `
                        <div class="cost-item">
                            <div class="cost-year">${{year}}</div>
                            <div class="cost-amount">€${{costs.cost_eur.toLocaleString()}}</div>
                            <div class="cost-details">${{costs.phase_in_pct}}% phase-in</div>
                            <div class="cost-details">€${{costs.eua_price_eur.toFixed(2)}}/tonne</div>
                        </div>
                    `;
                }}
                
                html += `
                        </div>
                    </div>
                `;
            }}
            
            contentDiv.innerHTML = html;
        }}
    </script>
</body>
</html>
        """

def main():
    # Use Railway's PORT environment variable, fallback to 8080 for local
    PORT = int(os.environ.get('PORT', 8080))
    
    print("=" * 60)
    print("EU ETS COST CALCULATOR - WEB SERVER")
    print("=" * 60)
    print(f"Java SeaRoute Available: {'Yes' if JAVA_AVAILABLE else 'No'}")
    print(f"Starting server on port {{PORT}}...")
    print(f"Open your browser and go to: http://localhost:{{PORT}}")
    print("Press Ctrl+C to stop the server")
    print("=" * 60)
    
    try:
        with socketserver.TCPServer(("", PORT), CalculatorHandler) as httpd:
            print(f"Server running at http://0.0.0.0:{{PORT}}")
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\\nServer stopped.")
    except Exception as e:
        print(f"Error starting server: {{e}}")

if __name__ == "__main__":
    main()
