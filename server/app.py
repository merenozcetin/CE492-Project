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
import urllib.request
import urllib.error
import csv
from datetime import datetime

try:
    import openrouteservice as ors
    ORS_AVAILABLE = True
except ImportError:
    ORS_AVAILABLE = False

try:
    import geopandas as gpd
    from shapely.geometry import Point
    GEOPANDAS_AVAILABLE = True
except ImportError:
    GEOPANDAS_AVAILABLE = False

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
        elif self.path.startswith('/api/transport-options'):
            self.handle_transport_options()
        elif self.path.startswith('/api/road-distance'):
            self.handle_road_distance()
        elif self.path.startswith('/api/geocode'):
            self.handle_geocode()
        elif self.path.startswith('/api/route-geometry'):
            self.handle_route_geometry()
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
    
    def handle_transport_options(self):
        """Handle request for transport options (sea vessel types/sizes/fuels, road modes/fuels)"""
        try:
            query_params = urllib.parse.parse_qs(self.path.split('?')[1]) if '?' in self.path else {}
            vessel_type_filter = query_params.get('vessel_type', [''])[0]
            size_filter = query_params.get('size', [''])[0]
            road_mode_filter = query_params.get('road_mode', [''])[0]
            
            sea_factors = self.load_sea_emission_factors()
            road_factors = self.load_road_emission_factors()
            
            # For sea transport with conditional filtering
            sea_vessel_types = set()
            sea_sizes = set()
            sea_fuels = set()
            
            for key, data in sea_factors.items():
                vessel_type = data.get('vessel_type', '').strip()
                size = data.get('size', '').strip()
                fuel = data.get('fuel', '').strip()
                
                # Apply filters
                if vessel_type_filter and vessel_type != vessel_type_filter:
                    continue
                if size_filter and size != size_filter:
                    continue
                
                if vessel_type:
                    sea_vessel_types.add(vessel_type)
                if size:
                    sea_sizes.add(size)
                if fuel:
                    sea_fuels.add(fuel)
            
            # For road transport with conditional filtering
            road_modes = set()
            road_load_types = set()
            road_fuels = set()
            
            for key, data in road_factors.items():
                mode = data.get('mode', '').strip()
                load_type = data.get('load_type', '').strip()
                fuel = data.get('fuel', '').strip()
                
                # Apply filter
                if road_mode_filter and mode != road_mode_filter:
                    continue
                
                if mode:
                    road_modes.add(mode)
                if load_type:
                    road_load_types.add(load_type)
                if fuel:
                    road_fuels.add(fuel)
            
            # Return all emission factors for client-side filtering
            sea_factors_list = []
            for key, data in sea_factors.items():
                sea_factors_list.append(data)
            
            road_factors_list = []
            for key, data in road_factors.items():
                road_factors_list.append(data)
            
            result = {
                'sea': {
                    'vessel_types': sorted(list(sea_vessel_types)),
                    'sizes': sorted(list(sea_sizes)),
                    'fuels': sorted(list(sea_fuels)),
                    'all_factors': sea_factors_list
                },
                'road': {
                    'modes': sorted(list(road_modes)),
                    'load_types': sorted(list(road_load_types)),
                    'fuels': sorted(list(road_fuels)),
                    'all_factors': road_factors_list
                }
            }
            
            print(f"Transport options: {len(sea_vessel_types)} vessel types, {len(road_modes)} road modes", flush=True)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())
            
        except Exception as e:
            print(f"Error in handle_transport_options: {e}")
            import traceback
            traceback.print_exc()
            error_response = {'error': str(e)}
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
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

    def handle_geocode(self):
        """Handle geocoding requests using Mapbox API"""
        try:
            print(f"[GEOCODE] Request received: {self.path}")
            query_params = urllib.parse.parse_qs(self.path.split('?')[1]) if '?' in self.path else {}
            query = query_params.get('q', [''])[0]
            mode = query_params.get('mode', ['search'])[0]
            print(f"[GEOCODE] Query: '{query}', Mode: {mode}")

            if not query or len(query) < 2:
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({'success': False, 'error': 'Query must be at least 2 characters'}).encode())
                return

            # Get Mapbox token from environment
            mapbox_token = os.environ.get('MAPBOX_ACCESS_TOKEN', '')
            if not mapbox_token:
                # Try loading from .env.local file
                env_file = os.path.join(os.path.dirname(__file__), '.env.local')
                print(f"[GEOCODE] Looking for .env.local at: {env_file}")
                if os.path.exists(env_file):
                    print(f"[GEOCODE] Found .env.local file")
                    with open(env_file, 'r') as f:
                        for line in f:
                            if line.startswith('MAPBOX_ACCESS_TOKEN='):
                                mapbox_token = line.split('=', 1)[1].strip().strip('"\'')
                                print(f"[GEOCODE] Token loaded: {mapbox_token[:20]}...")
                                break
                else:
                    print(f"[GEOCODE] .env.local file not found")

            if not mapbox_token:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({'success': False, 'error': 'Mapbox token not configured'}).encode())
                return

            # Call Mapbox Geocoding API
            limit = 1 if mode == 'geocode' else 5
            encoded_query = urllib.parse.quote(query)
            mapbox_url = f"https://api.mapbox.com/geocoding/v5/mapbox.places/{encoded_query}.json?access_token={mapbox_token}&limit={limit}&types=address,place,poi,locality"
            print(f"[GEOCODE] Calling Mapbox API...")

            req = urllib.request.Request(mapbox_url, headers={'Accept': 'application/json'})
            with urllib.request.urlopen(req, timeout=10) as response:
                mapbox_data = json.loads(response.read().decode())

            print(f"[GEOCODE] Mapbox returned {len(mapbox_data.get('features', []))} features")

            # Transform response
            if mode == 'search':
                # Return suggestions for autocomplete
                suggestions = []
                for feature in mapbox_data.get('features', []):
                    # Mapbox returns [lng, lat] order!
                    lng, lat = feature['center']
                    context_parts = [c['text'] for c in feature.get('context', [])]
                    suggestions.append({
                        'id': feature['id'],
                        'placeName': feature['place_name'],
                        'text': feature['text'],
                        'coordinates': {'lat': lat, 'lng': lng},
                        'context': ', '.join(context_parts) if context_parts else None
                    })
                result = {'success': True, 'data': suggestions}
            else:
                # Return single geocode result
                if mapbox_data.get('features'):
                    feature = mapbox_data['features'][0]
                    lng, lat = feature['center']
                    result = {
                        'success': True,
                        'data': {
                            'coordinates': {'lat': lat, 'lng': lng},
                            'placeName': feature['text'],
                            'formattedAddress': feature['place_name']
                        }
                    }
                else:
                    result = {'success': False, 'error': 'No results found'}

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())

        except urllib.error.URLError as e:
            print(f"Geocoding URL error: {e}")
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({'success': False, 'error': f'Mapbox API error: {str(e)}'}).encode())
        except Exception as e:
            print(f"Geocoding error: {e}")
            import traceback
            traceback.print_exc()
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({'success': False, 'error': str(e)}).encode())

    def handle_route_geometry(self):
        """Handle route geometry requests for map display"""
        try:
            query_params = urllib.parse.parse_qs(self.path.split('?')[1]) if '?' in self.path else {}
            origin_lat = float(query_params.get('origin_lat', [0])[0])
            origin_lon = float(query_params.get('origin_lon', [0])[0])
            dest_lat = float(query_params.get('dest_lat', [0])[0])
            dest_lon = float(query_params.get('dest_lon', [0])[0])
            mode = query_params.get('mode', ['sea'])[0]

            print(f"[ROUTE] Getting {mode} route geometry: ({origin_lat}, {origin_lon}) -> ({dest_lat}, {dest_lon})")

            result = {'success': False, 'coordinates': []}

            if mode == 'sea':
                # Use Java SeaRoute for maritime routes
                if JAVA_AVAILABLE:
                    try:
                        java_wrapper = JavaSeaRouteWrapper()
                        java_result = java_wrapper.calculate_distance(origin_lon, origin_lat, dest_lon, dest_lat)

                        if java_result['success'] and java_result.get('coordinates'):
                            # SeaRoute returns MultiLineString coordinates
                            coords = java_result['coordinates']
                            # Flatten to single array of [lng, lat] pairs
                            flat_coords = []
                            for line_string in coords:
                                flat_coords.extend(line_string)
                            result = {
                                'success': True,
                                'coordinates': flat_coords,
                                'distance_km': java_result.get('distance_km', 0),
                                'distance_nm': java_result.get('distance_nm', 0),
                                'mode': 'sea'
                            }
                            print(f"[ROUTE] Sea route found with {len(flat_coords)} waypoints")
                        else:
                            # Fallback to straight line
                            result = {
                                'success': True,
                                'coordinates': [[origin_lon, origin_lat], [dest_lon, dest_lat]],
                                'mode': 'sea',
                                'fallback': True
                            }
                    except Exception as e:
                        print(f"[ROUTE] Sea route error: {e}")
                        result = {
                            'success': True,
                            'coordinates': [[origin_lon, origin_lat], [dest_lon, dest_lat]],
                            'mode': 'sea',
                            'fallback': True,
                            'error': str(e)
                        }
                else:
                    # No Java available, use straight line
                    result = {
                        'success': True,
                        'coordinates': [[origin_lon, origin_lat], [dest_lon, dest_lat]],
                        'mode': 'sea',
                        'fallback': True
                    }

            elif mode == 'road':
                # Use OpenRouteService for road routes
                if ORS_AVAILABLE:
                    try:
                        api_key = "eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6IjljYzg0MGUwOGMzODQ0ODQ4OWI0ZTJkMWMzODcwOGM4IiwiaCI6Im11cm11cjY0In0="
                        client = ors.Client(key=api_key)

                        routes = client.directions(
                            coordinates=[[origin_lon, origin_lat], [dest_lon, dest_lat]],
                            profile='driving-car',
                            format='geojson'
                        )

                        if routes and routes.get('features'):
                            geometry = routes['features'][0]['geometry']
                            coords = geometry.get('coordinates', [])
                            props = routes['features'][0].get('properties', {})
                            summary = props.get('summary', {})

                            result = {
                                'success': True,
                                'coordinates': coords,
                                'distance_km': round(summary.get('distance', 0) / 1000, 1),
                                'duration_hours': round(summary.get('duration', 0) / 3600, 2),
                                'mode': 'road'
                            }
                            print(f"[ROUTE] Road route found with {len(coords)} waypoints")
                        else:
                            result = {
                                'success': True,
                                'coordinates': [[origin_lon, origin_lat], [dest_lon, dest_lat]],
                                'mode': 'road',
                                'fallback': True
                            }
                    except Exception as e:
                        error_msg = str(e)
                        print(f"[ROUTE] Road route error: {e}")
                        # Check for common ORS errors
                        if "Unable to find a route" in error_msg or "Could not find routable point" in error_msg:
                            result = {
                                'success': True,
                                'coordinates': [[origin_lon, origin_lat], [dest_lon, dest_lat]],
                                'mode': 'road',
                                'fallback': True,
                                'error': 'No road route available between these points'
                            }
                        else:
                            result = {
                                'success': True,
                                'coordinates': [[origin_lon, origin_lat], [dest_lon, dest_lat]],
                                'mode': 'road',
                                'fallback': True,
                                'error': error_msg
                            }
                else:
                    result = {
                        'success': True,
                        'coordinates': [[origin_lon, origin_lat], [dest_lon, dest_lat]],
                        'mode': 'road',
                        'fallback': True,
                        'error': 'OpenRouteService not available'
                    }

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())

        except Exception as e:
            print(f"[ROUTE] Error: {e}")
            import traceback
            traceback.print_exc()
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({'success': False, 'error': str(e)}).encode())

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
    
    def load_sea_emission_factors(self):
        """Load sea transport emission factors from sea.csv"""
        try:
            sea_factors = {}
            with open('data/sea.csv', 'r', encoding='utf-8-sig') as f:  # utf-8-sig automatically strips BOM
                reader = csv.DictReader(f)
                print(f"CSV columns: {reader.fieldnames}", flush=True)
                for row_num, row in enumerate(reader, start=2):
                    # Get values - utf-8-sig should have stripped BOM, but handle both cases
                    vessel_type = (row.get('Vessel Characteristics', '') or 
                                  row.get('\ufeffVessel Characteristics', '')).strip()
                    size = row.get('Size', '').strip()
                    fuel = row.get('Fuel', '').strip()
                    emission_str = row.get('Emission intensity (g CO2e/t-km)', '').strip()
                    
                    # Debug first row
                    if row_num == 2:
                        print(f"First row data: vessel_type='{vessel_type}', size='{size}', fuel='{fuel}', emission='{emission_str}'", flush=True)
                    
                    # Skip empty rows
                    if not vessel_type or not size or not fuel or not emission_str:
                        if row_num <= 5:
                            print(f"Row {row_num} skipped - empty values", flush=True)
                        continue
                    
                    try:
                        emission_factor = float(emission_str)
                    except ValueError:
                        if row_num <= 5:
                            print(f"Row {row_num} skipped - invalid emission value: '{emission_str}'", flush=True)
                        continue
                    
                    key = f"{vessel_type}|{size}|{fuel}"
                    sea_factors[key] = {
                        'vessel_type': vessel_type,
                        'size': size,
                        'fuel': fuel,
                        'emission_factor': emission_factor  # g CO2e/t-km
                    }
            print(f"Loaded {len(sea_factors)} sea emission factor records", flush=True)
            if len(sea_factors) > 0:
                first_key = list(sea_factors.keys())[0]
                print(f"Sample sea factor: {sea_factors[first_key]}", flush=True)
            return sea_factors
        except Exception as e:
            print(f"Error loading sea emission factors: {e}", flush=True)
            import traceback
            traceback.print_exc()
            return {}
    
    def load_road_emission_factors(self):
        """Load road transport emission factors from road.csv"""
        try:
            road_factors = {}
            with open('data/road.csv', 'r', encoding='utf-8-sig') as f:  # utf-8-sig automatically strips BOM
                reader = csv.DictReader(f)
                print(f"Road CSV columns: {reader.fieldnames}", flush=True)
                for row_num, row in enumerate(reader, start=2):
                    # Get values including load type
                    mode = (row.get('Mode', '') or row.get('\ufeffMode', '')).strip()
                    load_type = row.get('Load type', '').strip()
                    fuel = row.get('Fuel', '').strip()
                    emission_str = row.get('Emission intensity (g CO2e/t-km)', '').strip()
                    
                    # Debug first row
                    if row_num == 2:
                        print(f"First road row: mode='{mode}', load_type='{load_type}', fuel='{fuel}', emission='{emission_str}'", flush=True)
                    
                    # Skip empty rows
                    if not mode or not fuel or not emission_str:
                        if row_num <= 5:
                            print(f"Road row {row_num} skipped - empty values", flush=True)
                        continue
                    
                    try:
                        emission_factor = float(emission_str)
                    except ValueError:
                        if row_num <= 5:
                            print(f"Road row {row_num} skipped - invalid emission: '{emission_str}'", flush=True)
                        continue
                    
                    # Include load type in the key if available
                    if load_type:
                        key = f"{mode}|{load_type}|{fuel}"
                        road_factors[key] = {
                            'mode': mode,
                            'load_type': load_type,
                            'fuel': fuel,
                            'emission_factor': emission_factor
                        }
                    else:
                        key = f"{mode}|{fuel}"
                        road_factors[key] = {
                            'mode': mode,
                            'load_type': '',
                            'fuel': fuel,
                            'emission_factor': emission_factor
                        }
            print(f"Loaded {len(road_factors)} road emission factor records", flush=True)
            if len(road_factors) > 0:
                first_key = list(road_factors.keys())[0]
                print(f"Sample road factor: {road_factors[first_key]}", flush=True)
            return road_factors
        except Exception as e:
            print(f"Error loading road emission factors: {e}", flush=True)
            import traceback
            traceback.print_exc()
            return {}
    
    def handle_mrv_calculation(self):
        """Handle MRV emissions and ETS cost calculation"""
        try:
            # Parse query parameters
            query_params = urllib.parse.parse_qs(self.path.split('?')[1])
            
            transport_mode = query_params.get('transport_mode', [''])[0]  # 'sea' or 'road'
            origin_lat = float(query_params.get('origin_lat', ['0'])[0])
            origin_lon = float(query_params.get('origin_lon', ['0'])[0])
            dest_lat = float(query_params.get('dest_lat', ['0'])[0])
            dest_lon = float(query_params.get('dest_lon', ['0'])[0])
            cargo_weight = float(query_params.get('cargo_weight', ['0'])[0])  # in tonnes
            
            # Load emission factors and ETS prices
            sea_factors = self.load_sea_emission_factors()
            road_factors = self.load_road_emission_factors()
            ets_prices = self.load_ets_prices()
            
            emission_factor = None
            distance_km = None
            transport_info = {}
            
            if transport_mode == 'sea':
                # Sea transport: get ship type, size, fuel
                vessel_type = query_params.get('vessel_type', [''])[0]
                size = query_params.get('size', [''])[0]
                fuel = query_params.get('fuel', [''])[0]
                
                # Find emission factor
                key = f"{vessel_type}|{size}|{fuel}"
                if key not in sea_factors:
                    error_response = {'error': f'Sea emission factor not found for: {vessel_type}, {size}, {fuel}'}
                    self.send_response(400)
                    self.send_header('Content-type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(json.dumps(error_response).encode())
                    return
                
                emission_factor = sea_factors[key]['emission_factor']
                transport_info = {
                    'mode': 'Sea Transport',
                    'vessel_type': vessel_type,
                    'size': size,
                    'fuel': fuel,
                    'emission_factor': emission_factor
                }
                
                # Calculate sea distance
                distance_result = self.calculate_distances(origin_lat, origin_lon, dest_lat, dest_lon)
                if not distance_result['distance']['success']:
                    error_response = {'error': f"Distance calculation failed: {distance_result['distance'].get('error', 'Unknown error')}"}
                    self.send_response(400)
                    self.send_header('Content-type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(json.dumps(error_response).encode())
                    return
                
                distance_km = distance_result['distance']['distance_km']
                distance_nm = distance_result['distance']['distance_nm']
                
                # Calculate emissions: 1000 * cargo_weight * distance_km * emission_factor (g CO2e/t-km) / 1000000 = tonnes CO2e
                # Formula: weight (t) * distance (km) * emission_factor (g CO2e/t-km) / 1000000 = tonnes CO2e
                co2eq_emissions_t = (cargo_weight * distance_km * emission_factor) / 1000000
                co2_emissions_t = co2eq_emissions_t  # Assuming CO2eq = CO2 for now
                
            elif transport_mode == 'road':
                # Road transport: get mode, load type, and fuel
                road_mode = query_params.get('road_mode', [''])[0]
                load_type = query_params.get('load_type', [''])[0]
                fuel = query_params.get('fuel', [''])[0]
                
                # Find emission factor (try with and without load type)
                key_with_load = f"{road_mode}|{load_type}|{fuel}"
                key_without_load = f"{road_mode}|{fuel}"
                
                if key_with_load in road_factors:
                    emission_factor = road_factors[key_with_load]['emission_factor']
                    transport_info = {
                        'mode': 'Road Transport',
                        'vehicle_mode': road_mode,
                        'load_type': load_type,
                        'fuel': fuel,
                        'emission_factor': emission_factor
                    }
                elif key_without_load in road_factors:
                    emission_factor = road_factors[key_without_load]['emission_factor']
                    transport_info = {
                        'mode': 'Road Transport',
                        'vehicle_mode': road_mode,
                        'load_type': load_type or 'N/A',
                        'fuel': fuel,
                        'emission_factor': emission_factor
                    }
                else:
                    error_response = {'error': f'Road emission factor not found for: {road_mode}, {load_type}, {fuel}'}
                    self.send_response(400)
                    self.send_header('Content-type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(json.dumps(error_response).encode())
                    return
                
                # Calculate road distance using OpenRouteService
                if not ORS_AVAILABLE:
                    error_response = {'error': 'OpenRouteService library not available for road distance calculation'}
                    self.send_response(400)
                    self.send_header('Content-type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(json.dumps(error_response).encode())
                    return
                
                api_key = "eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6IjljYzg0MGUwOGMzODQ0ODQ4OWI0ZTJkMWMzODcwOGM4IiwiaCI6Im11cm11cjY0In0="
                
                try:
                    client = ors.Client(key=api_key)
                    start_coords = [origin_lon, origin_lat]
                    end_coords = [dest_lon, dest_lat]
                    
                    routes = client.directions(
                        coordinates=[start_coords, end_coords],
                        profile='driving-car',
                        format='json'
                    )
                    
                    if 'routes' not in routes or len(routes['routes']) == 0:
                        error_response = {'error': '⚠️ No route found for these coordinates. Please check they are near roads.'}
                        self.send_response(400)
                        self.send_header('Content-type', 'application/json')
                        self.send_header('Access-Control-Allow-Origin', '*')
                        self.end_headers()
                        self.wfile.write(json.dumps(error_response).encode())
                        return
                    
                    distance_m = routes['routes'][0]['summary']['distance']
                    distance_km = distance_m / 1000
                    distance_nm = distance_km / 1.852  # Convert to nautical miles
                    
                    # Calculate emissions
                    co2eq_emissions_t = (emission_factor * cargo_weight * distance_km) / 1000000
                    co2_emissions_t = co2eq_emissions_t
                    
                except ors.exceptions.ApiError as api_error:
                    # Handle OpenRouteService API errors with user-friendly messages
                    error_str = str(api_error)
                    print(f"OpenRouteService API error in MRV: {error_str}", flush=True)
                    
                    if "Could not find routable point" in error_str or "2010" in error_str:
                        user_message = "⚠️ The coordinates are not near a road. Please ensure your coordinates are within 350 meters of a drivable road. Try using major city coordinates or addresses near highways."
                    elif "2009" in error_str or "point is out of bounds" in error_str:
                        user_message = "⚠️ The coordinates are outside the available map area. Please check your latitude and longitude values."
                    elif "401" in error_str or "Unauthorized" in error_str:
                        user_message = "⚠️ API authentication error. Please contact support."
                    elif "403" in error_str or "rate limit" in error_str.lower():
                        user_message = "⚠️ API rate limit exceeded. Please try again in a few moments."
                    else:
                        user_message = f"⚠️ Road routing error. Please verify your coordinates and try again."
                    
                    error_response = {'error': user_message}
                    self.send_response(400)
                    self.send_header('Content-type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(json.dumps(error_response).encode())
                    return
                
            else:
                error_response = {'error': f'Invalid transport mode: {transport_mode}. Must be "sea" or "road".'}
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(error_response).encode())
                return
            
            # Determine ETS coverage based on transport mode
            if transport_mode == 'sea':
                # For sea transport, use port matching
                ports = self.load_ports()
                origin_port = None
                dest_port = None
                
                # Find closest ports
                for port in ports:
                    if abs(port['lat'] - origin_lat) < 0.01 and abs(port['lon'] - origin_lon) < 0.01:
                        origin_port = port
                        break
                
                for port in ports:
                    if abs(port['lat'] - dest_lat) < 0.01 and abs(port['lon'] - dest_lon) < 0.01:
                        dest_port = port
                        break
                
                # Use GeoPackage-based detection for accurate EEA check
                origin_eea = self.is_coordinate_in_eea(origin_lat, origin_lon)
                dest_eea = self.is_coordinate_in_eea(dest_lat, dest_lon)
            else:
                # For road transport, use same GeoPackage-based detection
                origin_eea = self.is_coordinate_in_eea(origin_lat, origin_lon)
                dest_eea = self.is_coordinate_in_eea(dest_lat, dest_lon)
            
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
                'transport_mode': transport_mode,
                'transport_info': transport_info,
                'cargo_weight': cargo_weight,
                'distance': {
                    'distance_km': round(distance_km, 2),
                    'distance_nm': round(distance_nm, 2) if transport_mode == 'sea' else round(distance_nm, 2),
                    'success': True
                },
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
    
    def handle_road_distance(self):
        """Handle road distance calculation using OpenRouteService API"""
        try:
            if not ORS_AVAILABLE:
                raise Exception("OpenRouteService library not available. Please install: pip install openrouteservice")
            
            # Parse query parameters
            query_params = urllib.parse.parse_qs(self.path.split('?')[1])
            
            origin_lat = float(query_params['origin_lat'][0])
            origin_lon = float(query_params['origin_lon'][0])
            dest_lat = float(query_params['dest_lat'][0])
            dest_lon = float(query_params['dest_lon'][0])
            
            # OpenRouteService API key
            api_key = "eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6IjljYzg0MGUwOGMzODQ0ODQ4OWI0ZTJkMWMzODcwOGM4IiwiaCI6Im11cm11cjY0In0="
            
            # Initialize OpenRouteService client
            client = ors.Client(key=api_key)
            
            # Coordinates format: [longitude, latitude]
            start_coords = [origin_lon, origin_lat]
            end_coords = [dest_lon, dest_lat]
            
            # Calculate route
            routes = client.directions(
                coordinates=[start_coords, end_coords],
                profile='driving-car',
                format='json'
            )
            
            # Parse response
            if 'routes' in routes and len(routes['routes']) > 0:
                route = routes['routes'][0]
                distance_m = route['summary']['distance']  # Distance in meters
                duration_s = route['summary']['duration']  # Duration in seconds
                distance_km = distance_m / 1000
                distance_miles = distance_km * 0.621371
                
                # Convert duration to hours and minutes
                hours = int(duration_s // 3600)
                minutes = int((duration_s % 3600) // 60)
                
                result = {
                    'success': True,
                    'distance_km': round(distance_km, 2),
                    'distance_miles': round(distance_miles, 2),
                    'distance_meters': round(distance_m, 0),
                    'duration_seconds': round(duration_s, 0),
                    'duration_hours': hours,
                    'duration_minutes': minutes,
                    'geometry': route.get('geometry', '')  # Encoded polyline for route visualization
                }
            else:
                raise Exception("No route found in API response")
            
            # Send JSON response
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())
            
        except ors.exceptions.ApiError as e:
            # Log error for debugging
            print(f"OpenRouteService API error: {str(e)}")
            
            # Parse error message for user-friendly response
            error_str = str(e)
            user_message = "Road routing error"
            
            if "Could not find routable point" in error_str or "2010" in error_str:
                user_message = "⚠️ The coordinates are not near a road. Please ensure your coordinates are within 350 meters of a drivable road."
            elif "2009" in error_str or "point is out of bounds" in error_str:
                user_message = "⚠️ The coordinates are outside the available map area. Please check your latitude and longitude values."
            elif "401" in error_str or "Unauthorized" in error_str:
                user_message = "⚠️ API authentication error. Please contact support."
            elif "403" in error_str or "rate limit" in error_str.lower():
                user_message = "⚠️ API rate limit exceeded. Please try again in a few moments."
            else:
                user_message = f"⚠️ Road routing error: {error_str}"
            
            error_response = {'success': False, 'error': user_message}
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(error_response).encode())
        except Exception as e:
            # Log error for debugging
            print(f"Road distance calculation error: {str(e)}")
            error_response = {'success': False, 'error': f"⚠️ Error: {str(e)}"}
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(error_response).encode())
    
    _eea_geometry = None  # Cache for GeoDataFrame
    
    def is_coordinate_in_eea(self, lat, lon):
        """
        Determine if coordinates are in EEA territory
        Uses GeoPackage file with actual country boundaries for accurate detection
        Falls back to bounding box if GeoPackage is unavailable
        
        EEA includes: EU-27 + Iceland, Liechtenstein, Norway
        """
        # Try using GeoPackage for accurate detection
        if GEOPANDAS_AVAILABLE:
            try:
                # Load and cache the GeoDataFrame
                if CalculatorHandler._eea_geometry is None:
                    # EEA country codes (ISO 2-letter codes)
                    eea_countries = [
                        'AT', 'BE', 'BG', 'HR', 'CY', 'CZ', 'DK', 'EE', 'FI', 'FR',
                        'DE', 'GR', 'HU', 'IE', 'IT', 'LV', 'LT', 'LU', 'MT', 'NL',
                        'PL', 'PT', 'RO', 'SK', 'SI', 'ES', 'SE',  # EU-27
                        'IS', 'LI', 'NO'  # EFTA in EEA
                    ]
                    
                    # Load country boundaries from GeoPackage
                    gdf = gpd.read_file('data/CNTR_RG_20M_2024_3035.gpkg')

                    # Filter to EEA countries only
                    eea_gdf = gdf[gdf['CNTR_ID'].isin(eea_countries)]

                    # Reproject from EPSG:3035 to EPSG:4326 (WGS84 lat/lon)
                    # The GeoPackage uses ETRS89-LAEA (meters), but we need WGS84 for lat/lon coordinates
                    eea_gdf = eea_gdf.to_crs(epsg=4326)

                    # Combine all geometries into one
                    CalculatorHandler._eea_geometry = eea_gdf.unary_union
                    print(f"Loaded EEA boundaries for {len(eea_countries)} countries (reprojected to WGS84)", flush=True)
                
                # Create point and check if it's within EEA
                point = Point(lon, lat)
                is_in_eea = CalculatorHandler._eea_geometry.contains(point)
                
                return is_in_eea
                
            except Exception as e:
                print(f"GeoPackage error, using fallback: {e}", flush=True)
                # Fall through to bounding box method
        
        # Fallback: Conservative bounding box (less accurate)
        # Main Europe box - more restrictive to exclude Turkey
        if 42.0 <= lat <= 71.0 and -10.0 <= lon <= 28.0:
            # Exclude areas clearly outside EEA
            # Turkey is roughly: 36-42°N, 26-45°E
            # This conservative box keeps most of EU but may exclude some edge cases
            return True
        
        # Cyprus (EEA member, special case)
        if 34.5 <= lat <= 35.7 and 32.3 <= lon <= 34.6:
            return True
        
        # Canary Islands, Azores, Madeira (EEA territories)
        if 27.6 <= lat <= 29.4 and -18.2 <= lon <= -13.4:  # Canary Islands
            return True
        if 36.9 <= lat <= 39.7 and -31.3 <= lon <= -25.0:  # Azores
            return True
        if 32.4 <= lat <= 33.1 and -17.3 <= lon <= -16.3:  # Madeira
            return True
        
        return False
    
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
                    lat = float(port.get('lat', 0))
                    lon = float(port.get('lon', 0))
                    matches.append({
                        'name': port.get('name', ''),
                        'country': port.get('country', ''),
                        'lat': lat,
                        'lon': lon,
                        'is_eea': self.is_coordinate_in_eea(lat, lon)
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
    <title>routets - Maritime Distance & ETS Calculator</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <!-- Mapbox GL JS -->
    <script src="https://api.mapbox.com/mapbox-gl-js/v3.3.0/mapbox-gl.js"></script>
    <link href="https://api.mapbox.com/mapbox-gl-js/v3.3.0/mapbox-gl.css" rel="stylesheet" />
    <!-- Chart.js for ETS cost comparison charts -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
    <style>
        /* ========================================
           ERGUVAN-INSPIRED DESIGN SYSTEM
           Black & White Minimal Theme
           ======================================== */

        :root {{
            --background: #ffffff;
            --foreground: #0a0a0a;
            --primary: #0a0a0a;
            --primary-dark: #1a1a1a;
            --primary-foreground: #ffffff;
            --secondary: #f5f5f5;
            --muted: #64748b;
            --muted-foreground: #94a3b8;
            --success: #16a34a;
            --success-bg: #dcfce7;
            --success-border: #86efac;
            --success-text: #166534;
            --info: #2563eb;
            --info-bg: #f5f5f5;
            --warning-bg: #f5f5f5;
            --border: #e5e5e5;
            --border-dark: #333333;
            --card: #ffffff;
            --radius: 0px;
            --error: #dc2626;
            --error-muted: #fee2e2;
        }}

        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: var(--background);
            color: var(--foreground);
            line-height: 1.6;
            min-height: 100vh;
        }}

        /* ========================================
           HEADER - Minimal Erguvan Style
           ======================================== */

        .header {{
            background: var(--primary);
            color: var(--primary-foreground);
            padding: 1rem 1.5rem;
            position: sticky;
            top: 0;
            z-index: 100;
            border-bottom: 1px solid var(--border-dark);
        }}

        .header-content {{
            max-width: 1200px;
            margin: 0 auto;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}

        .logo {{
            font-size: 1.25rem;
            font-weight: 400;
            letter-spacing: -0.02em;
            color: var(--primary-foreground);
            text-decoration: none;
        }}

        .header-right {{
            display: flex;
            align-items: center;
            gap: 1.5rem;
        }}

        .menu-btn {{
            background: transparent;
            border: none;
            cursor: pointer;
            padding: 0.5rem;
            display: flex;
            flex-direction: column;
            gap: 5px;
        }}

        .menu-btn span {{
            display: block;
            width: 24px;
            height: 2px;
            background: var(--primary-foreground);
            transition: all 0.3s ease;
        }}

        .menu-btn.active span:nth-child(1) {{ transform: rotate(45deg) translate(5px, 5px); }}
        .menu-btn.active span:nth-child(2) {{ opacity: 0; }}
        .menu-btn.active span:nth-child(3) {{ transform: rotate(-45deg) translate(5px, -5px); }}

        /* ========================================
           NAVIGATION OVERLAY
           ======================================== */

        .nav-overlay {{
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: var(--primary);
            z-index: 99;
            display: none;
            padding: 6rem 2rem 2rem;
        }}

        .nav-overlay.active {{ display: block; }}

        .nav-menu {{
            max-width: 600px;
            margin: 0 auto;
        }}

        .nav-link {{
            display: block;
            font-size: 1.5rem;
            font-weight: 400;
            color: var(--primary-foreground);
            text-decoration: none;
            padding: 1rem 0;
            border-bottom: 1px solid var(--border-dark);
            transition: opacity 0.2s;
        }}

        .nav-link:hover {{ opacity: 0.7; }}

        .nav-section-label {{
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            color: var(--muted);
            margin-top: 2rem;
            margin-bottom: 1rem;
        }}

        .nav-sub-link {{
            display: block;
            font-size: 1rem;
            color: var(--muted-foreground);
            text-decoration: none;
            padding: 0.75rem 0;
            transition: color 0.2s;
        }}

        .nav-sub-link:hover {{ color: var(--primary-foreground); }}

        /* ========================================
           HERO SECTION
           ======================================== */

        .hero {{
            background: var(--primary);
            color: var(--primary-foreground);
            padding: 4rem 1.5rem;
            text-align: left;
        }}

        .hero-content {{
            max-width: 1200px;
            margin: 0 auto;
        }}

        .hero h1 {{
            font-size: 3rem;
            font-weight: 700;
            line-height: 1.1;
            margin-bottom: 1rem;
            letter-spacing: -0.03em;
        }}

        .hero p {{
            font-size: 1rem;
            color: var(--muted);
            margin-bottom: 2rem;
            max-width: 500px;
        }}

        .hero-buttons {{
            display: flex;
            gap: 1rem;
            flex-wrap: wrap;
        }}

        .btn-hero-outline {{
            background: transparent;
            color: var(--primary-foreground);
            border: 2px solid var(--primary-foreground);
            padding: 1rem 2rem;
            font-size: 0.875rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            cursor: pointer;
            transition: all 0.2s;
        }}

        .btn-hero-outline:hover {{
            background: var(--primary-foreground);
            color: var(--primary);
        }}

        .btn-hero-filled {{
            background: var(--primary-foreground);
            color: var(--primary);
            border: 2px solid var(--primary-foreground);
            padding: 1rem 2rem;
            font-size: 0.875rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            cursor: pointer;
            transition: all 0.2s;
        }}

        .btn-hero-filled:hover {{ background: var(--secondary); }}

        /* ========================================
           MAIN CONTAINER
           ======================================== */

        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 3rem 1.5rem;
        }}

        /* ========================================
           TABS - Erguvan Style
           ======================================== */

        .tabs {{
            display: flex;
            gap: 0;
            margin-bottom: 3rem;
            border-bottom: 1px solid var(--border);
            overflow-x: auto;
            scrollbar-width: none;
            -ms-overflow-style: none;
        }}

        .tabs::-webkit-scrollbar {{
            display: none;
        }}

        .tab-btn {{
            background: transparent;
            border: none;
            padding: 1rem 1.5rem;
            font-size: 0.875rem;
            font-weight: 500;
            cursor: pointer;
            border-bottom: 2px solid transparent;
            transition: all 0.2s;
            color: var(--muted);
            white-space: nowrap;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: -1px;
        }}

        .tab-btn:hover {{ color: var(--foreground); }}

        .tab-btn.active {{
            border-bottom-color: var(--primary);
            color: var(--primary);
        }}

        .tab-content {{ display: none; }}
        .tab-content.active {{ display: block; }}

        /* ========================================
           CARDS - Sharp Corners
           ======================================== */

        .card {{
            background: var(--card);
            border: 1px solid var(--border);
            padding: 2rem;
            margin-bottom: 1.5rem;
            transition: border-color 0.2s;
        }}

        .card:hover {{ border-color: var(--muted); }}

        .card-header {{
            display: flex;
            align-items: center;
            gap: 0.75rem;
            margin-bottom: 1.5rem;
        }}

        .card-icon {{
            width: 40px;
            height: 40px;
            border-radius: var(--radius);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.25rem;
            flex-shrink: 0;
            background: var(--secondary);
            border: 1px solid var(--border);
        }}

        .card-icon.transport {{ background: var(--secondary); }}
        .card-icon.sea {{ background: var(--secondary); }}
        .card-icon.road {{ background: var(--secondary); }}
        .card-icon.cargo {{ background: var(--secondary); }}
        .card-icon.route {{ background: var(--secondary); }}
        .card-icon.success {{ background: var(--secondary); }}

        .card-title {{
            font-size: 1rem;
            font-weight: 600;
            margin: 0;
            color: var(--foreground);
            letter-spacing: 0.05em;
        }}

        .card-subtitle {{
            font-size: 0.875rem;
            color: var(--muted-foreground);
            margin-top: 0.25rem;
        }}

        .card-title-standalone {{
            font-size: 1.25rem;
            font-weight: 600;
            margin-bottom: 1.5rem;
            color: var(--foreground);
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
            font-weight: 600;
            font-size: 0.7rem;
            color: var(--muted-foreground);
            text-transform: uppercase;
            letter-spacing: 0.1em;
            margin-bottom: 0.5rem;
        }}
        
        .form-input {{
            padding: 0.875rem 1rem;
            border: 1px solid var(--border);
            font-size: 1rem;
            transition: all 0.2s;
            font-family: inherit;
            background: var(--background);
            color: var(--foreground);
        }}

        .form-input:focus {{
            outline: none;
            border-color: var(--primary);
        }}

        .form-input::placeholder {{
            color: var(--muted-foreground);
        }}
        
        .search-results {{
            max-height: 240px;
            overflow-y: auto;
            border: 1px solid var(--border);
            margin-top: 0.5rem;
            display: none;
            background: var(--background);
        }}

        .search-result {{
            padding: 0.875rem 1rem;
            cursor: pointer;
            border-bottom: 1px solid var(--border);
            transition: background 0.15s;
            font-size: 0.9rem;
        }}

        .search-result:hover {{
            background: var(--secondary);
        }}

        .search-result:last-child {{
            border-bottom: none;
        }}
        
        .coordinates-display {{
            font-family: 'Inter', sans-serif;
            background: var(--background);
            padding: 0.75rem 1rem;
            border-radius: var(--radius);
            font-size: 0.75rem;
            color: var(--muted-foreground);
            border: 1px solid var(--border);
            margin-top: 0.5rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}

        .location-selected {{
            background: var(--background);
            border: 1px solid var(--primary);
            color: var(--foreground);
            padding: 0.75rem 1rem;
            border-radius: var(--radius);
            margin-top: 0.5rem;
            display: flex;
            align-items: flex-start;
            gap: 0.75rem;
        }}

        .location-selected-icon {{
            color: var(--primary);
            flex-shrink: 0;
            margin-top: 2px;
        }}

        .location-selected-content {{
            flex: 1;
        }}

        .location-selected-title {{
            font-weight: 600;
            font-size: 0.7rem;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            color: var(--muted-foreground);
        }}

        .location-selected-coords {{
            font-size: 0.875rem;
            font-family: 'Inter', sans-serif;
            margin-top: 4px;
            color: var(--foreground);
            font-weight: 500;
        }}
        
        .btn-primary {{
            background: var(--primary);
            color: var(--primary-foreground);
            border: 1px solid var(--primary);
            padding: 0.875rem 1.5rem;
            font-size: 0.75rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
            width: 100%;
            margin-top: 1rem;
            text-transform: uppercase;
            letter-spacing: 0.1em;
        }}

        .btn-primary:hover:not(:disabled) {{
            background: var(--primary-dark);
            border-color: var(--primary-dark);
        }}

        .btn-primary:disabled {{
            background: var(--border);
            border-color: var(--border);
            color: var(--muted);
            cursor: not-allowed;
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

        /* Address Search Styles */
        .address-search-container {{
            position: relative;
            width: 100%;
        }}

        .address-search-input {{
            padding: 0.75rem 1rem 0.75rem 2.5rem;
            border: 2px solid #e2e8f0;
            border-radius: 8px;
            font-size: 1rem;
            transition: all 0.2s;
            font-family: inherit;
            background: white;
            width: 100%;
        }}

        .address-search-input:focus {{
            outline: none;
            border-color: #0ea5e9;
            box-shadow: 0 0 0 3px rgba(14, 165, 233, 0.1);
        }}

        .address-search-icon {{
            position: absolute;
            left: 0.75rem;
            top: 50%;
            transform: translateY(-50%);
            color: #64748b;
            pointer-events: none;
        }}

        .address-search-spinner {{
            position: absolute;
            right: 0.75rem;
            top: 50%;
            transform: translateY(-50%);
            width: 16px;
            height: 16px;
            border: 2px solid #e2e8f0;
            border-top-color: #0ea5e9;
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
            display: none;
        }}

        .address-search-spinner.show {{
            display: block;
        }}

        .address-search-clear {{
            position: absolute;
            right: 0.75rem;
            top: 50%;
            transform: translateY(-50%);
            background: none;
            border: none;
            color: #64748b;
            cursor: pointer;
            padding: 4px;
            display: none;
        }}

        .address-search-clear.show {{
            display: block;
        }}

        .address-search-clear:hover {{
            color: #0f172a;
        }}

        .address-suggestions {{
            position: absolute;
            top: 100%;
            left: 0;
            right: 0;
            z-index: 1000;
            max-height: 240px;
            overflow-y: auto;
            border: 2px solid #e2e8f0;
            border-radius: 8px;
            margin-top: 0.25rem;
            background: white;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            display: none;
        }}

        .address-suggestions.show {{
            display: block;
        }}

        .address-suggestion {{
            padding: 0.875rem 1rem;
            cursor: pointer;
            border-bottom: 1px solid #f1f5f9;
            transition: background 0.15s;
            display: flex;
            align-items: flex-start;
            gap: 0.5rem;
        }}

        .address-suggestion:hover,
        .address-suggestion.highlighted {{
            background: #f8fafc;
        }}

        .address-suggestion:last-child {{
            border-bottom: none;
        }}

        .address-suggestion-icon {{
            color: #64748b;
            flex-shrink: 0;
            margin-top: 2px;
        }}

        .address-suggestion-content {{
            flex: 1;
            min-width: 0;
        }}

        .address-suggestion-text {{
            font-weight: 500;
            font-size: 0.9rem;
            color: #0f172a;
        }}

        .address-suggestion-context {{
            font-size: 0.8rem;
            color: #64748b;
            margin-top: 2px;
        }}

        @keyframes spin {{
            to {{ transform: translateY(-50%) rotate(360deg); }}
        }}

        /* Map Styles */
        .map-container {{
            height: 400px;
            border-radius: var(--radius);
            overflow: hidden;
            border: 1px solid var(--border);
            margin-top: 1rem;
            position: relative;
            background: var(--secondary);
        }}

        .map-placeholder {{
            height: 100%;
            display: flex;
            align-items: center;
            justify-content: center;
            background: var(--secondary);
            color: var(--muted-foreground);
            font-size: 0.875rem;
            letter-spacing: 0.05em;
        }}

        .mapboxgl-popup-content {{
            padding: 12px 16px;
            border-radius: var(--radius);
            font-family: 'Inter', sans-serif;
            font-size: 0.9rem;
        }}

        .marker-label {{
            font-weight: 600;
            color: var(--foreground);
        }}

        .marker-coords {{
            font-size: 0.8rem;
            color: var(--muted-foreground);
            margin-top: 4px;
        }}

        /* Map Legend */
        .map-legend {{
            position: absolute;
            bottom: 1rem;
            left: 1rem;
            background: rgba(255, 255, 255, 0.95);
            padding: 0.75rem 1rem;
            border-radius: var(--radius);
            font-size: 0.8rem;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
            z-index: 10;
            border: 1px solid var(--border);
        }}

        .legend-title {{
            font-weight: 600;
            margin-bottom: 0.5rem;
            color: var(--foreground);
        }}

        .legend-item {{
            display: flex;
            align-items: center;
            gap: 0.5rem;
            margin-bottom: 0.375rem;
        }}

        .legend-item:last-child {{
            margin-bottom: 0;
        }}

        .legend-dot {{
            width: 12px;
            height: 12px;
            border-radius: 50%;
            flex-shrink: 0;
        }}

        .legend-dot.origin {{
            background: var(--success);
        }}

        .legend-dot.destination {{
            background: #ef4444;
        }}

        .legend-line {{
            width: 20px;
            height: 4px;
            border-radius: 2px;
            background: var(--info);
            flex-shrink: 0;
        }}

        .legend-text {{
            color: var(--muted-foreground);
        }}

        /* Result card improvements */
        .result-card-highlight {{
            background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
            border-left: 4px solid var(--primary);
        }}

        .result-icon {{
            width: 36px;
            height: 36px;
            border-radius: var(--radius);
            display: flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
        }}

        .result-icon.distance {{
            background: var(--info-bg);
            color: var(--info);
        }}

        .result-icon.duration {{
            background: var(--warning-bg);
            color: #d97706;
        }}

        .result-icon.emissions {{
            background: var(--success-bg);
            color: var(--success-text);
        }}

        /* ===== COMPARISON WIZARD STYLES ===== */
        .wizard-container {{
            background: var(--background);
            border: 1px solid var(--border);
            padding: 0;
        }}

        .wizard-header {{
            background: var(--primary);
            color: var(--primary-foreground);
            padding: 2rem;
            text-align: center;
        }}

        .wizard-header .card-title {{
            color: var(--primary-foreground);
            font-size: 1.25rem;
            margin-bottom: 0.5rem;
        }}

        .wizard-header .card-subtitle {{
            color: rgba(255, 255, 255, 0.7);
            margin-top: 0;
        }}

        .wizard-body {{
            padding: 2rem;
        }}

        .wizard-steps {{
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 0 0 2rem 0;
            margin-bottom: 2rem;
            border-bottom: 1px solid var(--border);
        }}

        .wizard-step {{
            display: flex;
            align-items: center;
            gap: 0.75rem;
            opacity: 0.4;
            transition: all 0.3s ease;
        }}

        .wizard-step.active {{
            opacity: 1;
        }}

        .wizard-step.completed {{
            opacity: 1;
        }}

        .wizard-step.completed .wizard-step-number {{
            background: var(--primary);
            color: var(--primary-foreground);
        }}

        .wizard-step-number {{
            width: 32px;
            height: 32px;
            border-radius: 50%;
            background: var(--border);
            color: var(--muted-foreground);
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 600;
            font-size: 0.875rem;
            transition: all 0.3s ease;
        }}

        .wizard-step.active .wizard-step-number {{
            background: var(--primary);
            color: var(--primary-foreground);
        }}

        .wizard-step-label {{
            font-size: 0.75rem;
            font-weight: 600;
            color: var(--muted-foreground);
            letter-spacing: 0.1em;
        }}

        .wizard-step.active .wizard-step-label {{
            color: var(--foreground);
        }}

        .wizard-step-connector {{
            width: 80px;
            height: 1px;
            background: var(--border);
            margin: 0 1.5rem;
            transition: background 0.3s ease;
        }}

        .wizard-step-connector.completed {{
            background: var(--primary);
        }}

        .wizard-content {{
            min-height: 280px;
            padding: 0;
        }}

        .wizard-dual-panel {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 1.5rem;
        }}

        @media (max-width: 768px) {{
            .wizard-dual-panel {{
                grid-template-columns: 1fr;
            }}
        }}

        .wizard-panel {{
            background: var(--secondary);
            border-radius: var(--radius);
            padding: 1.5rem;
            border: 1px solid var(--border);
            position: relative;
        }}

        .wizard-panel::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 3px;
            background: var(--primary);
        }}

        .wizard-panel.sea-panel::before {{
            background: var(--primary);
        }}

        .wizard-panel.road-panel::before {{
            background: var(--primary);
        }}

        .wizard-panel-title {{
            font-size: 0.75rem;
            font-weight: 700;
            margin-bottom: 1.25rem;
            display: flex;
            align-items: center;
            gap: 0.75rem;
            letter-spacing: 0.1em;
            padding-bottom: 1rem;
            border-bottom: 1px solid var(--border);
        }}

        .panel-icon {{
            font-size: 1.5rem;
        }}

        .wizard-cargo-section {{
            margin-top: 2rem;
            padding-top: 2rem;
            border-top: 1px solid var(--border);
            display: flex;
            justify-content: center;
        }}

        .cargo-input-row {{
            display: flex;
            align-items: center;
            justify-content: center;
            background: var(--secondary);
            padding: 1.5rem 2rem;
            border-radius: var(--radius);
            border: 1px solid var(--border);
            min-width: 350px;
        }}

        .wizard-navigation {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 1.5rem 2rem;
            border-top: 1px solid var(--border);
            margin-top: 2rem;
            background: var(--secondary);
        }}

        .wizard-navigation .btn-secondary,
        .wizard-navigation .btn-primary {{
            min-width: 140px;
            width: auto !important;
            flex: 0 0 auto;
            margin-top: 0;
            font-size: 0.75rem;
            letter-spacing: 0.1em;
        }}

        .wizard-navigation .wizard-compare-btn {{
            min-width: 180px;
            width: auto !important;
        }}

        .btn-secondary {{
            background: transparent;
            color: var(--foreground);
            border: 1px solid var(--border);
            padding: 0.875rem 1.5rem;
            border-radius: var(--radius);
            font-size: 0.75rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
            letter-spacing: 0.1em;
        }}

        .btn-secondary:hover {{
            background: var(--foreground);
            color: var(--background);
            border-color: var(--foreground);
        }}

        .btn-small {{
            padding: 0.625rem 1rem;
            font-size: 0.7rem;
        }}

        .wizard-compare-btn {{
            background: var(--primary);
            color: var(--primary-foreground);
        }}

        .wizard-compare-btn:hover:not(:disabled) {{
            background: var(--primary-dark);
        }}

        .wizard-cargo-input {{
            display: flex;
            justify-content: center;
            padding: 2rem 0;
        }}

        .form-hint {{
            font-size: 0.8rem;
            color: var(--muted-foreground);
            margin-top: 0.5rem;
        }}

        .wizard-divider {{
            text-align: center;
            margin: 2rem 0;
            position: relative;
        }}

        .wizard-divider::before {{
            content: '';
            position: absolute;
            top: 50%;
            left: 0;
            right: 0;
            height: 2px;
            background: var(--border);
        }}

        .wizard-divider-text {{
            background: var(--background);
            padding: 0 1rem;
            color: var(--muted-foreground);
            font-size: 0.875rem;
            position: relative;
            z-index: 1;
        }}

        /* ===== COMPARISON RESULTS STYLES ===== */
        .comparison-results-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1.5rem;
        }}

        .card-title-standalone {{
            font-size: 1.25rem;
            font-weight: 700;
            color: var(--foreground);
            margin: 0;
            letter-spacing: 0.05em;
        }}

        .comparison-map-container {{
            height: 650px;
        }}

        .comparison-metrics-grid {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 1.5rem;
            margin-bottom: 1.5rem;
        }}

        @media (max-width: 768px) {{
            .comparison-metrics-grid {{
                grid-template-columns: 1fr;
            }}
        }}

        .comparison-metric-card {{
            background: var(--background);
            border-radius: var(--radius);
            padding: 1.5rem;
            border: 2px solid var(--border);
            text-align: center;
        }}

        .comparison-metric-card.sea {{
            border-top: 4px solid var(--primary);
        }}

        .comparison-metric-card.road {{
            border-top: 4px solid var(--primary);
        }}

        .comparison-metric-card.summary {{
            border-top: 4px solid var(--primary);
            background: var(--secondary);
        }}

        .comparison-metric-header {{
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 0.5rem;
            margin-bottom: 1rem;
        }}

        .comparison-metric-icon {{
            font-size: 1.5rem;
        }}

        .comparison-metric-title {{
            font-weight: 600;
            color: var(--foreground);
            font-size: 0.875rem;
            letter-spacing: 0.05em;
            text-transform: uppercase;
        }}

        .comparison-metric-value {{
            font-size: 2.5rem;
            font-weight: 700;
            color: var(--foreground);
            line-height: 1;
        }}

        .comparison-metric-card.sea .comparison-metric-value {{
            color: var(--foreground);
        }}

        .comparison-metric-card.road .comparison-metric-value {{
            color: var(--foreground);
        }}

        .comparison-metric-card.summary .comparison-metric-value {{
            color: var(--foreground);
        }}

        .comparison-metric-label {{
            font-size: 0.875rem;
            color: var(--muted-foreground);
            margin-top: 0.5rem;
        }}

        .comparison-metric-detail {{
            font-size: 0.8rem;
            color: var(--muted-foreground);
            margin-top: 0.5rem;
        }}

        /* Chart Container */
        .chart-container {{
            position: relative;
            height: 420px;
            padding: 1.5rem;
            background: var(--background);
            border-radius: var(--radius);
        }}

        /* Insights Styles */
        .insights-content {{
            padding: 0.5rem 0;
        }}

        .insight-item {{
            display: flex;
            align-items: flex-start;
            gap: 1rem;
            padding: 1.25rem;
            background: var(--background);
            border-radius: var(--radius);
            margin-bottom: 0.75rem;
            border: 1px solid var(--border);
        }}

        .insight-item:last-child {{
            margin-bottom: 0;
        }}

        .insight-label {{
            font-size: 0.65rem;
            font-weight: 700;
            letter-spacing: 0.1em;
            padding: 0.5rem 0.75rem;
            background: var(--primary);
            color: var(--primary-foreground);
            border-radius: var(--radius);
            flex-shrink: 0;
            min-width: 50px;
            text-align: center;
        }}

        .insight-text {{
            flex: 1;
        }}

        .insight-title {{
            font-weight: 600;
            font-size: 0.875rem;
            color: var(--foreground);
            margin-bottom: 0.5rem;
        }}

        .insight-description {{
            font-size: 0.8rem;
            color: var(--muted-foreground);
            line-height: 1.5;
        }}

        .insight-item.positive {{
            border-left: 3px solid var(--primary);
        }}

        .insight-item.negative {{
            border-left: 3px solid var(--primary);
        }}

        .insight-item.neutral {{
            border-left: 3px solid var(--muted);
        }}

        /* Combined Map Legend */
        .comparison-map-legend {{
            position: absolute;
            bottom: 1rem;
            left: 1rem;
            background: rgba(255, 255, 255, 0.95);
            padding: 0.75rem 1rem;
            border-radius: var(--radius);
            font-size: 0.8rem;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
            z-index: 10;
            border: 1px solid var(--border);
        }}
    </style>
</head>
<body>
    <!-- Navigation Overlay -->
    <div class="nav-overlay" id="navOverlay">
        <div class="nav-menu">
            <a href="#" class="nav-link" onclick="navigateToTab('compare'); toggleMenu(); return false;">Compare Routes</a>
            <a href="#" class="nav-link" onclick="navigateToTab('mrv'); toggleMenu(); return false;">ETS Calculator</a>
            <a href="#" class="nav-link" onclick="navigateToTab('distance'); toggleMenu(); return false;">Sea Distance</a>
            <a href="#" class="nav-link" onclick="navigateToTab('road'); toggleMenu(); return false;">Road Distance</a>

            <div class="nav-section-label">CALCULATORS:</div>
            <a href="#" class="nav-sub-link" onclick="navigateToTab('compare'); toggleMenu(); return false;">Sea vs Road Comparison</a>
            <a href="#" class="nav-sub-link" onclick="navigateToTab('mrv'); toggleMenu(); return false;">ETS Cost Calculation</a>
            <a href="#" class="nav-sub-link" onclick="navigateToTab('distance'); toggleMenu(); return false;">Sea Distance</a>
            <a href="#" class="nav-sub-link" onclick="navigateToTab('road'); toggleMenu(); return false;">Road Distance</a>
        </div>
    </div>

    <!-- Header -->
    <div class="header">
        <div class="header-content">
            <a href="#" class="logo">ets-routes</a>
            <div class="header-right">
                <button class="menu-btn" id="menuBtn" onclick="toggleMenu()">
                    <span></span>
                    <span></span>
                    <span></span>
                </button>
            </div>
        </div>
    </div>

    <!-- Hero Section -->
    <div class="hero">
        <div class="hero-content">
            <h1>Route &<br>ETS Calculator.</h1>
            <p>Calculate shipping distances and EU Emissions Trading System costs with precision. Compare sea and road transport options.</p>
            <div class="hero-buttons">
                <button class="btn-hero-outline" onclick="navigateToTab('compare')">COMPARE ROUTES</button>
                <button class="btn-hero-filled" onclick="navigateToTab('mrv')">ETS CALCULATOR</button>
            </div>
        </div>
    </div>

    <div class="container">
        <div class="tabs">
            <button class="tab-btn active" onclick="switchTab('compare')">COMPARE ROUTES</button>
            <button class="tab-btn" onclick="switchTab('mrv')">ETS COST</button>
            <button class="tab-btn" onclick="switchTab('distance')">SEA DISTANCE</button>
            <button class="tab-btn" onclick="switchTab('road')">ROAD DISTANCE</button>
        </div>
        
        <!-- Compare Routes Tab -->
        <div id="compare-tab" class="tab-content active">
            <!-- ETS Cost Comparison Wizard -->
            <div class="card wizard-container" id="comparison-wizard">
                <div class="wizard-header">
                    <h2 class="card-title">SEA VS ROAD COMPARISON</h2>
                    <p class="card-subtitle">Compare ETS costs between maritime and road transport</p>
                </div>

                <div class="wizard-body">
                    <!-- Step Indicator -->
                    <div class="wizard-steps">
                        <div class="wizard-step active" data-step="1">
                            <div class="wizard-step-number">1</div>
                            <div class="wizard-step-label">VEHICLES & CARGO</div>
                        </div>
                        <div class="wizard-step-connector"></div>
                        <div class="wizard-step" data-step="2">
                            <div class="wizard-step-number">2</div>
                            <div class="wizard-step-label">ROUTE</div>
                        </div>
                    </div>

                    <!-- Step 1: Vehicle Selection -->
                    <div class="wizard-content" id="wizard-step-1">
                        <div class="wizard-dual-panel">
                            <!-- Sea Vehicle Panel -->
                            <div class="wizard-panel sea-panel">
                                <h3 class="wizard-panel-title">SEA TRANSPORT</h3>
                            <div class="form-group">
                                <label class="form-label">Vessel Type</label>
                                <select id="wizard-vessel-type" class="form-input" onchange="updateWizardSeaDropdowns(); updateWizardState();">
                                    <option value="">-- Select Vessel Type --</option>
                                </select>
                            </div>
                            <div class="form-group">
                                <label class="form-label">Size (dwt)</label>
                                <select id="wizard-vessel-size" class="form-input" onchange="updateWizardSeaDropdowns(); updateWizardState();" disabled>
                                    <option value="">-- Select Size --</option>
                                </select>
                            </div>
                            <div class="form-group">
                                <label class="form-label">Fuel Type</label>
                                <select id="wizard-sea-fuel" class="form-input" onchange="updateWizardState();" disabled>
                                    <option value="">-- Select Fuel --</option>
                                </select>
                            </div>
                        </div>

                        <!-- Road Vehicle Panel -->
                        <div class="wizard-panel road-panel">
                            <h3 class="wizard-panel-title">ROAD TRANSPORT</h3>
                            <div class="form-group">
                                <label class="form-label">Vehicle Mode</label>
                                <select id="wizard-road-mode" class="form-input" onchange="updateWizardRoadDropdowns(); updateWizardState();">
                                    <option value="">-- Select Mode --</option>
                                </select>
                            </div>
                            <div class="form-group">
                                <label class="form-label">Load Type</label>
                                <select id="wizard-road-load-type" class="form-input" onchange="updateWizardRoadDropdowns(); updateWizardState();" disabled>
                                    <option value="">-- Select Load Type --</option>
                                </select>
                            </div>
                            <div class="form-group">
                                <label class="form-label">Fuel Type</label>
                                <select id="wizard-road-fuel" class="form-input" onchange="updateWizardState();" disabled>
                                    <option value="">-- Select Fuel --</option>
                                </select>
                            </div>
                        </div>
                    </div>

                    <!-- Cargo Weight Input -->
                    <div class="wizard-cargo-section">
                        <div class="cargo-input-row">
                            <div class="form-group" style="flex: 1; max-width: 300px; margin: 0;">
                                <label class="form-label">CARGO WEIGHT (TONNES)</label>
                                <input type="number" id="wizard-cargo-weight" class="form-input" placeholder="Enter cargo weight" step="0.01" min="0" oninput="updateWizardState()">
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Step 2: Route Selection -->
                <div class="wizard-content" id="wizard-step-2" style="display: none;">
                    <div class="form-grid">
                        <div class="form-group">
                            <label class="form-label">Origin Location</label>
                            <div class="address-search-container">
                                <svg class="address-search-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path><circle cx="12" cy="10" r="3"></circle></svg>
                                <input type="text" id="wizard-origin-address" class="address-search-input" placeholder="Search for origin location..." autocomplete="off">
                                <div class="address-search-spinner" id="wizard-origin-spinner"></div>
                                <button class="address-search-clear" id="wizard-origin-clear" onclick="clearWizardAddress('wizard-origin')">&#10005;</button>
                                <div class="address-suggestions" id="wizard-origin-suggestions"></div>
                            </div>
                            <input type="hidden" id="wizard-origin-lat">
                            <input type="hidden" id="wizard-origin-lon">
                            <div class="coordinates-display" id="wizard-origin-coords">Not selected</div>
                        </div>

                        <div class="form-group">
                            <label class="form-label">Destination Location</label>
                            <div class="address-search-container">
                                <svg class="address-search-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path><circle cx="12" cy="10" r="3"></circle></svg>
                                <input type="text" id="wizard-dest-address" class="address-search-input" placeholder="Search for destination location..." autocomplete="off">
                                <div class="address-search-spinner" id="wizard-dest-spinner"></div>
                                <button class="address-search-clear" id="wizard-dest-clear" onclick="clearWizardAddress('wizard-dest')">&#10005;</button>
                                <div class="address-suggestions" id="wizard-dest-suggestions"></div>
                            </div>
                            <input type="hidden" id="wizard-dest-lat">
                            <input type="hidden" id="wizard-dest-lon">
                            <div class="coordinates-display" id="wizard-dest-coords">Not selected</div>
                        </div>
                    </div>

                    <!-- Route preview map -->
                    <div class="map-container" id="wizard-preview-map-container" style="height: 450px; margin-top: 1rem;">
                        <div class="map-placeholder" id="wizard-preview-map-placeholder">
                            Select origin and destination to preview routes
                        </div>
                        <div id="wizard-preview-map" style="width: 100%; height: 100%; display: none;"></div>
                    </div>
                </div>

                    <!-- Navigation Buttons -->
                    <div class="wizard-navigation">
                        <button class="btn-secondary" id="wizard-back-btn" onclick="wizardPrevStep()" style="display: none;">
                            BACK
                        </button>
                        <button class="btn-primary" id="wizard-next-btn" onclick="wizardNextStep()" disabled>
                            NEXT
                        </button>
                        <button class="btn-primary wizard-compare-btn" id="wizard-compare-btn" onclick="runComparison()" style="display: none;" disabled>
                            RUN COMPARISON
                        </button>
                    </div>
                </div>
            </div>

            <!-- Comparison Results Section -->
            <div id="comparison-results" class="results" style="display: none;">
                <div class="comparison-results-header">
                    <h2 class="card-title-standalone">COMPARISON RESULTS</h2>
                    <button class="btn-secondary btn-small" onclick="resetWizard()">NEW COMPARISON</button>
                </div>

                <!-- Combined Routes Map -->
                <div class="card">
                    <div class="card-header">
                        <div>
                            <h2 class="card-title">ROUTE COMPARISON MAP</h2>
                            <p class="card-subtitle">Visual comparison of sea and road transport routes</p>
                        </div>
                    </div>
                    <div class="map-container comparison-map-container" id="comparison-map-container">
                        <div class="map-placeholder" id="comparison-map-placeholder">Loading routes...</div>
                        <div id="comparison-map" style="width: 100%; height: 100%; display: none;"></div>
                    </div>
                </div>

                <!-- CO2 Comparison Cards -->
                <div class="comparison-metrics-grid">
                    <div class="comparison-metric-card sea">
                        <div class="comparison-metric-header">
                            <span class="comparison-metric-title">SEA TRANSPORT</span>
                        </div>
                        <div class="comparison-metric-value" id="sea-co2-value">--</div>
                        <div class="comparison-metric-label">TONNES CO2</div>
                        <div class="comparison-metric-detail" id="sea-distance-detail">-- km</div>
                    </div>

                    <div class="comparison-metric-card road">
                        <div class="comparison-metric-header">
                            <span class="comparison-metric-title">ROAD TRANSPORT</span>
                        </div>
                        <div class="comparison-metric-value" id="road-co2-value">--</div>
                        <div class="comparison-metric-label">TONNES CO2</div>
                        <div class="comparison-metric-detail" id="road-distance-detail">-- km</div>
                    </div>

                    <div class="comparison-metric-card summary">
                        <div class="comparison-metric-header">
                            <span class="comparison-metric-title">CO2 DIFFERENCE</span>
                        </div>
                        <div class="comparison-metric-value" id="co2-savings-value">--</div>
                        <div class="comparison-metric-label" id="co2-savings-label">TONNES CO2</div>
                        <div class="comparison-metric-detail" id="co2-savings-percent">--</div>
                    </div>
                </div>

                <!-- ETS Cost Chart -->
                <div class="card">
                    <div class="card-header">
                        <div>
                            <h2 class="card-title">ETS COST PROJECTION (2024-2030)</h2>
                            <p class="card-subtitle">Annual ETS costs comparison with phase-in schedule</p>
                        </div>
                    </div>
                    <div class="chart-container">
                        <canvas id="comparison-chart"></canvas>
                    </div>
                </div>

                <!-- Analysis Insights -->
                <div class="card">
                    <div class="card-header">
                        <div>
                            <h2 class="card-title">ANALYSIS & INSIGHTS</h2>
                            <p class="card-subtitle">Key findings from the comparison</p>
                        </div>
                    </div>
                    <div id="comparison-insights" class="insights-content">
                        <!-- Dynamic insights will be inserted here -->
                    </div>
                </div>
            </div>
        </div>

        <!-- MRV Tab -->
        <div id="mrv-tab" class="tab-content">
            <div class="card">
                <div class="card-header">
                    <div class="card-icon transport">🚚</div>
                    <div>
                        <h2 class="card-title">Transportation Mode</h2>
                        <p class="card-subtitle">Choose sea or road transport</p>
                    </div>
                </div>

                    <div class="form-group">
                    <label class="form-label" for="transport-mode">Select Transportation Mode</label>
                    <select id="transport-mode" class="form-input" onchange="updateTransportFields()">
                        <option value="">-- Select Mode --</option>
                        <option value="sea">🌊 Sea Transport</option>
                        <option value="road">🛣️ Road Transport</option>
                    </select>
                </div>
                    </div>
            
            <!-- Sea Transport Fields -->
            <div id="sea-fields" class="card" style="display: none;">
                <div class="card-header">
                    <div class="card-icon sea">🚢</div>
                    <div>
                        <h2 class="card-title">Sea Transport Details</h2>
                        <p class="card-subtitle">Configure vessel type and fuel</p>
                    </div>
                </div>
                    
                    <div class="form-group">
                    <label class="form-label" for="vessel-type">Vessel Type</label>
                    <select id="vessel-type" class="form-input" onchange="updateSeaDropdowns(); updateMRVCalculateButton();">
                        <option value="">-- Select Vessel Type --</option>
                    </select>
                    </div>
                
                <div class="form-group">
                    <label class="form-label" for="vessel-size">Size (dwt)</label>
                    <select id="vessel-size" class="form-input" onchange="updateSeaDropdowns(); updateMRVCalculateButton();">
                        <option value="">-- Select Size --</option>
                    </select>
                </div>
                
                    <div class="form-group">
                    <label class="form-label" for="sea-fuel">Fuel Type</label>
                    <select id="sea-fuel" class="form-input" onchange="updateMRVCalculateButton()">
                        <option value="">-- Select Fuel --</option>
                    </select>
                </div>
                    </div>
            
            <!-- Road Transport Fields -->
            <div id="road-fields" class="card" style="display: none;">
                <div class="card-header">
                    <div class="card-icon road">🛣️</div>
                    <div>
                        <h2 class="card-title">Road Transport Details</h2>
                        <p class="card-subtitle">Configure vehicle and fuel type</p>
                    </div>
                </div>
                    
                    <div class="form-group">
                    <label class="form-label" for="road-mode">Vehicle Mode</label>
                    <select id="road-mode" class="form-input" onchange="updateRoadDropdowns(); updateMRVCalculateButton();">
                        <option value="">-- Select Vehicle Mode --</option>
                    </select>
                    </div>
                
                <div class="form-group">
                    <label class="form-label" for="road-load-type">Load Type</label>
                    <select id="road-load-type" class="form-input" onchange="updateRoadDropdowns(); updateMRVCalculateButton();">
                        <option value="">-- Select Load Type --</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label class="form-label" for="road-fuel">Fuel Type</label>
                    <select id="road-fuel" class="form-input" onchange="updateMRVCalculateButton()">
                        <option value="">-- Select Fuel --</option>
                    </select>
                </div>
            </div>
            
            <div id="cargo-fields" class="card" style="display: none;">
                <div class="card-header">
                    <div class="card-icon cargo">📦</div>
                    <div>
                        <h2 class="card-title">Cargo Information</h2>
                        <p class="card-subtitle">Enter cargo weight in tonnes</p>
                    </div>
                </div>
                
                <div class="form-group">
                    <label class="form-label" for="cargo-weight">Cargo Weight (tonnes)</label>
                    <input type="number" id="cargo-weight" class="form-input" placeholder="Enter cargo weight in tonnes" step="0.01" min="0" oninput="updateMRVCalculateButton()">
                </div>
            </div>
            
            <!-- Sea Transport Route (Address Search) -->
            <div id="sea-route-fields" class="card" style="display: none;">
                <div class="card-header">
                    <div class="card-icon route">📍</div>
                    <div>
                        <h2 class="card-title">Route Information (Sea)</h2>
                        <p class="card-subtitle">Search for origin and destination ports</p>
                    </div>
                </div>

                <div class="form-grid">
                    <div class="form-group">
                        <label class="form-label">Origin Location</label>
                        <div class="address-search-container">
                            <svg class="address-search-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path><circle cx="12" cy="10" r="3"></circle></svg>
                            <input type="text" id="sea-origin-mrv-address" class="address-search-input" placeholder="Search for origin port or city..." autocomplete="off">
                            <div class="address-search-spinner" id="sea-origin-mrv-spinner"></div>
                            <button class="address-search-clear" id="sea-origin-mrv-clear" onclick="clearAddressSearch('sea-origin-mrv')">✕</button>
                            <div class="address-suggestions" id="sea-origin-mrv-suggestions"></div>
                        </div>
                        <input type="hidden" id="sea-origin-mrv-lat">
                        <input type="hidden" id="sea-origin-mrv-lon">
                        <div class="coordinates-display" id="sea-origin-mrv-coords">Not selected</div>
                    </div>

                    <div class="form-group">
                        <label class="form-label">Destination Location</label>
                        <div class="address-search-container">
                            <svg class="address-search-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path><circle cx="12" cy="10" r="3"></circle></svg>
                            <input type="text" id="sea-dest-mrv-address" class="address-search-input" placeholder="Search for destination port or city..." autocomplete="off">
                            <div class="address-search-spinner" id="sea-dest-mrv-spinner"></div>
                            <button class="address-search-clear" id="sea-dest-mrv-clear" onclick="clearAddressSearch('sea-dest-mrv')">✕</button>
                            <div class="address-suggestions" id="sea-dest-mrv-suggestions"></div>
                        </div>
                        <input type="hidden" id="sea-dest-mrv-lat">
                        <input type="hidden" id="sea-dest-mrv-lon">
                        <div class="coordinates-display" id="sea-dest-mrv-coords">Not selected</div>
                    </div>
                </div>

                <!-- Map for MRV Sea Route -->
                <div class="map-container" id="mrv-sea-map-container">
                    <div class="map-placeholder" id="mrv-sea-map-placeholder">
                        Select origin and destination to see route on map
                    </div>
                    <div id="mrv-sea-map" style="width: 100%; height: 100%; display: none;"></div>
                </div>

                <button class="btn-primary" id="mrv-calculate-btn" onclick="calculateMRV()" disabled>
                    💰 Calculate ETS Costs
                </button>
            </div>
            
            <!-- Road Transport Route (Address Search) -->
            <div id="road-route-fields" class="card" style="display: none;">
                <div class="card-header">
                    <div class="card-icon route">📍</div>
                    <div>
                        <h2 class="card-title">Route Information (Road)</h2>
                        <p class="card-subtitle">Search for origin and destination addresses</p>
                    </div>
                </div>

                <div class="form-grid">
                    <div class="form-group">
                        <label class="form-label">Origin Address</label>
                        <div class="address-search-container">
                            <svg class="address-search-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path><circle cx="12" cy="10" r="3"></circle></svg>
                            <input type="text" id="road-origin-mrv-address" class="address-search-input" placeholder="Search for origin address..." autocomplete="off">
                            <div class="address-search-spinner" id="road-origin-mrv-spinner"></div>
                            <button class="address-search-clear" id="road-origin-mrv-clear" onclick="clearAddressSearch('road-origin-mrv')">✕</button>
                            <div class="address-suggestions" id="road-origin-mrv-suggestions"></div>
                        </div>
                        <input type="hidden" id="road-origin-mrv-lat">
                        <input type="hidden" id="road-origin-mrv-lon">
                        <div class="coordinates-display" id="road-origin-mrv-coords">Not selected</div>
                    </div>

                    <div class="form-group">
                        <label class="form-label">Destination Address</label>
                        <div class="address-search-container">
                            <svg class="address-search-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path><circle cx="12" cy="10" r="3"></circle></svg>
                            <input type="text" id="road-dest-mrv-address" class="address-search-input" placeholder="Search for destination address..." autocomplete="off">
                            <div class="address-search-spinner" id="road-dest-mrv-spinner"></div>
                            <button class="address-search-clear" id="road-dest-mrv-clear" onclick="clearAddressSearch('road-dest-mrv')">✕</button>
                            <div class="address-suggestions" id="road-dest-mrv-suggestions"></div>
                        </div>
                        <input type="hidden" id="road-dest-mrv-lat">
                        <input type="hidden" id="road-dest-mrv-lon">
                        <div class="coordinates-display" id="road-dest-mrv-coords">Not selected</div>
                    </div>
                </div>

                <!-- Map for MRV Road Route -->
                <div class="map-container" id="mrv-road-map-container">
                    <div class="map-placeholder" id="mrv-road-map-placeholder">
                        Select origin and destination to see route on map
                    </div>
                    <div id="mrv-road-map" style="width: 100%; height: 100%; display: none;"></div>
                </div>

                <button class="btn-primary" id="mrv-calculate-btn-road" onclick="calculateMRV()" disabled>
                    💰 Calculate ETS Costs
                </button>
            </div>
            
            <div id="mrv-results" class="results">
                <div id="mrv-results-content"></div>
            </div>
        </div>
        
        <!-- Distance Tab -->
        <div id="distance-tab" class="tab-content">
            <div class="card">
                <div class="card-header">
                    <div class="card-icon sea">🌊</div>
                    <div>
                        <h2 class="card-title">Maritime Route Information</h2>
                        <p class="card-subtitle">Search for origin and destination ports</p>
                    </div>
                </div>
                
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
            
            <div id="results" class="results">
                <div id="results-content"></div>
            </div>
        </div>
        
        <!-- Road Distance Tab -->
        <div id="road-tab" class="tab-content">
            <div class="card">
                <div class="card-header">
                    <div class="card-icon road">🛣️</div>
                    <div>
                        <h2 class="card-title">Road Route Information</h2>
                        <p class="card-subtitle">Search for origin and destination addresses</p>
                    </div>
                </div>

                <div class="form-grid">
                    <div class="form-group">
                        <label class="form-label">Origin Address</label>
                        <div class="address-search-container">
                            <svg class="address-search-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path><circle cx="12" cy="10" r="3"></circle></svg>
                            <input type="text" id="road-origin-address" class="address-search-input" placeholder="Search for origin address..." autocomplete="off">
                            <div class="address-search-spinner" id="road-origin-spinner"></div>
                            <button class="address-search-clear" id="road-origin-clear" onclick="clearAddressSearch('road-origin')">✕</button>
                            <div class="address-suggestions" id="road-origin-suggestions"></div>
                        </div>
                        <input type="hidden" id="road-origin-lat">
                        <input type="hidden" id="road-origin-lon">
                        <div class="coordinates-display" id="road-origin-coords">Not selected</div>
                    </div>

                    <div class="form-group">
                        <label class="form-label">Destination Address</label>
                        <div class="address-search-container">
                            <svg class="address-search-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path><circle cx="12" cy="10" r="3"></circle></svg>
                            <input type="text" id="road-dest-address" class="address-search-input" placeholder="Search for destination address..." autocomplete="off">
                            <div class="address-search-spinner" id="road-dest-spinner"></div>
                            <button class="address-search-clear" id="road-dest-clear" onclick="clearAddressSearch('road-dest')">✕</button>
                            <div class="address-suggestions" id="road-dest-suggestions"></div>
                        </div>
                        <input type="hidden" id="road-dest-lat">
                        <input type="hidden" id="road-dest-lon">
                        <div class="coordinates-display" id="road-dest-coords">Not selected</div>
                    </div>
                </div>

                <!-- Map for Road Distance -->
                <div class="map-container" id="road-map-container">
                    <div class="map-placeholder" id="road-map-placeholder">
                        Select origin and destination to see route on map
                    </div>
                    <div id="road-map" style="width: 100%; height: 100%; display: none;"></div>
                </div>

                <button class="btn-primary" id="road-calculate-btn" onclick="calculateRoadDistance()" disabled>
                    🛣️ Calculate Road Distance
                </button>
            </div>

            <div id="road-results" class="results">
                <div id="road-results-content"></div>
            </div>
        </div>
    </div>
    
    <script>
        let selectedOrigin = null;
        let selectedDestination = null;
        let selectedMRVOrigin = null;
        let selectedMRVDestination = null;
        let transportOptions = null;

        // Navigation menu functions
        function toggleMenu() {{
            const menuBtn = document.getElementById('menuBtn');
            const navOverlay = document.getElementById('navOverlay');
            menuBtn.classList.toggle('active');
            navOverlay.classList.toggle('active');
            if (navOverlay.classList.contains('active')) {{
                document.body.style.overflow = 'hidden';
            }} else {{
                document.body.style.overflow = '';
            }}
        }}

        function navigateToTab(tabName) {{
            switchTab(tabName);
            toggleMenu();
            setTimeout(() => {{
                document.querySelector('.container').scrollIntoView({{ behavior: 'smooth' }});
            }}, 100);
        }}

        // Helper function to show/update map legend
        function updateMapLegend(mapContainerId, routeColor, routeLabel) {{
            const container = document.getElementById(mapContainerId);
            if (!container) return;

            // Remove existing legend if any
            const existingLegend = container.querySelector('.map-legend');
            if (existingLegend) existingLegend.remove();

            // Create legend HTML
            const legend = document.createElement('div');
            legend.className = 'map-legend';
            legend.innerHTML = `
                <div class="legend-item">
                    <div class="legend-dot" style="background:#22c55e"></div>
                    <span>Origin</span>
                </div>
                <div class="legend-item">
                    <div class="legend-dot" style="background:#ef4444"></div>
                    <span>Destination</span>
                </div>
                <div class="legend-item">
                    <div class="legend-line" style="background:${{routeColor}}"></div>
                    <span>${{routeLabel}}</span>
                </div>
            `;
            container.appendChild(legend);
        }}

        // Helper function to remove map legend
        function removeMapLegend(mapContainerId) {{
            const container = document.getElementById(mapContainerId);
            if (!container) return;
            const legend = container.querySelector('.map-legend');
            if (legend) legend.remove();
        }}

        // Load transport options when DOM is ready
        if (document.readyState === 'loading') {{
            document.addEventListener('DOMContentLoaded', loadTransportOptions);
        }} else {{
            // DOM is already loaded
            loadTransportOptions();
        }}
        
        function loadTransportOptions() {{
            console.log('Loading transport options...');
            fetch('/api/transport-options')
                .then(response => {{
                    console.log('Response status:', response.status);
                    if (!response.ok) {{
                        throw new Error(`HTTP error! status: ${{response.status}}`);
                    }}
                    return response.json();
                }})
                .then(data => {{
                    console.log('Transport options loaded:', data);
                    console.log('Sea vessel types:', data.sea?.vessel_types);
                    console.log('Road modes:', data.road?.modes);
                    transportOptions = data;
                    populateTransportOptions();
                }})
                .catch(error => {{
                    console.error('Error loading transport options:', error);
                    alert('Failed to load transport options: ' + error.message);
                }});
        }}
        
        function populateTransportOptions() {{
            if (!transportOptions) {{
                console.error('transportOptions is null or undefined');
                return;
            }}
            
            if (!transportOptions.sea || !transportOptions.road) {{
                console.error('Invalid transportOptions structure:', transportOptions);
                return;
            }}
            
            console.log('Populating transport options with all_factors...');
            
            // Populate initial vessel types (all available)
            const vesselTypeSelect = document.getElementById('vessel-type');
            if (vesselTypeSelect && transportOptions.sea.vessel_types) {{
                transportOptions.sea.vessel_types.forEach(type => {{
                    const option = document.createElement('option');
                    option.value = type;
                    option.textContent = type;
                    vesselTypeSelect.appendChild(option);
                }});
                console.log(`Populated ${{transportOptions.sea.vessel_types.length}} vessel types`);
            }}
            
            // Populate initial road modes (all available)
            const roadModeSelect = document.getElementById('road-mode');
            if (roadModeSelect && transportOptions.road.modes) {{
                transportOptions.road.modes.forEach(mode => {{
                    const option = document.createElement('option');
                    option.value = mode;
                    option.textContent = mode;
                    roadModeSelect.appendChild(option);
                }});
                console.log(`Populated ${{transportOptions.road.modes.length}} road modes`);
            }}
            
            // Initialize other dropdowns as disabled
            document.getElementById('vessel-size').disabled = true;
            document.getElementById('sea-fuel').disabled = true;
            document.getElementById('road-load-type').disabled = true;
            document.getElementById('road-fuel').disabled = true;

            // Initialize wizard dropdowns
            initWizardDropdowns();
        }}

        function updateSeaDropdowns() {{
            const vesselTypeSelect = document.getElementById('vessel-type');
            const vesselSizeSelect = document.getElementById('vessel-size');
            const seaFuelSelect = document.getElementById('sea-fuel');
            
            if (!vesselTypeSelect || !vesselSizeSelect || !seaFuelSelect) return;
            if (!transportOptions || !transportOptions.sea) return;
            
            const selectedVesselType = vesselTypeSelect.value;
            const selectedSize = vesselSizeSelect.value;
            
            // Get matching options from all_factors
            const matchingSizes = new Set();
            const matchingFuels = new Set();
            
            transportOptions.sea.all_factors.forEach(factor => {{
                // Only filter sizes and fuels based on vessel type (if selected)
                if (selectedVesselType && factor.vessel_type !== selectedVesselType) return;
                
                matchingSizes.add(factor.size);
                
                // Further filter fuels if size is also selected
                if (!selectedSize || factor.size === selectedSize) {{
                    matchingFuels.add(factor.fuel);
                }}
            }});
            
            // Update sizes (only if vessel type is selected)
            if (selectedVesselType) {{
                const sizeValue = vesselSizeSelect.value;
                vesselSizeSelect.innerHTML = '<option value="">-- Select Size --</option>';
                const sortedSizes = Array.from(matchingSizes).sort();
                sortedSizes.forEach(size => {{
                    const option = document.createElement('option');
                    option.value = size;
                    option.textContent = size;
                    if (size === sizeValue) option.selected = true;
                    vesselSizeSelect.appendChild(option);
                }});
                vesselSizeSelect.disabled = false;
            }} else {{
                vesselSizeSelect.innerHTML = '<option value="">-- Select Size --</option>';
                vesselSizeSelect.disabled = true;
            }}
            
            // Update fuels (only if both vessel type and size are selected)
            if (selectedVesselType && selectedSize) {{
                const fuelValue = seaFuelSelect.value;
                seaFuelSelect.innerHTML = '<option value="">-- Select Fuel --</option>';
                const sortedFuels = Array.from(matchingFuels).sort();
                sortedFuels.forEach(fuel => {{
                    const option = document.createElement('option');
                    option.value = fuel;
                    option.textContent = fuel;
                    if (fuel === fuelValue) option.selected = true;
                    seaFuelSelect.appendChild(option);
                }});
                seaFuelSelect.disabled = false;
            }} else {{
                seaFuelSelect.innerHTML = '<option value="">-- Select Fuel --</option>';
                seaFuelSelect.disabled = true;
            }}
        }}
        
        function updateRoadDropdowns() {{
            const roadModeSelect = document.getElementById('road-mode');
            const roadLoadTypeSelect = document.getElementById('road-load-type');
            const roadFuelSelect = document.getElementById('road-fuel');
            
            if (!roadModeSelect || !roadLoadTypeSelect || !roadFuelSelect) return;
            if (!transportOptions || !transportOptions.road) return;
            
            const selectedRoadMode = roadModeSelect.value;
            const selectedLoadType = roadLoadTypeSelect.value;
            
            // Get matching load types and fuels based on selections
            const matchingLoadTypes = new Set();
            const matchingFuels = new Set();
            
            transportOptions.road.all_factors.forEach(factor => {{
                // Filter by mode (if selected)
                if (selectedRoadMode && factor.mode !== selectedRoadMode) return;
                
                // Add load types for this mode
                if (factor.load_type) {{
                    matchingLoadTypes.add(factor.load_type);
                }}
                
                // Filter fuels further if load type is also selected
                if (!selectedLoadType || factor.load_type === selectedLoadType) {{
                    matchingFuels.add(factor.fuel);
                }}
            }});
            
            // Update load types (only if mode is selected)
            if (selectedRoadMode) {{
                const loadTypeValue = roadLoadTypeSelect.value;
                roadLoadTypeSelect.innerHTML = '<option value="">-- Select Load Type --</option>';
                const sortedLoadTypes = Array.from(matchingLoadTypes).sort();
                sortedLoadTypes.forEach(loadType => {{
                    const option = document.createElement('option');
                    option.value = loadType;
                    option.textContent = loadType;
                    if (loadType === loadTypeValue) option.selected = true;
                    roadLoadTypeSelect.appendChild(option);
                }});
                roadLoadTypeSelect.disabled = false;
            }} else {{
                roadLoadTypeSelect.innerHTML = '<option value="">-- Select Load Type --</option>';
                roadLoadTypeSelect.disabled = true;
            }}
            
            // Update fuels (only if mode and load type are selected)
            if (selectedRoadMode && selectedLoadType) {{
                const fuelValue = roadFuelSelect.value;
                roadFuelSelect.innerHTML = '<option value="">-- Select Fuel --</option>';
                const sortedFuels = Array.from(matchingFuels).sort();
                sortedFuels.forEach(fuel => {{
                    const option = document.createElement('option');
                    option.value = fuel;
                    option.textContent = fuel;
                    if (fuel === fuelValue) option.selected = true;
                    roadFuelSelect.appendChild(option);
                }});
                roadFuelSelect.disabled = false;
            }} else {{
                roadFuelSelect.innerHTML = '<option value="">-- Select Fuel --</option>';
                roadFuelSelect.disabled = true;
            }}
        }}
        
        function updateTransportFields() {{
            const transportMode = document.getElementById('transport-mode').value;
            const seaFields = document.getElementById('sea-fields');
            const roadFields = document.getElementById('road-fields');
            const seaRouteFields = document.getElementById('sea-route-fields');
            const roadRouteFields = document.getElementById('road-route-fields');
            const cargoFields = document.getElementById('cargo-fields');
            
            if (transportMode === 'sea') {{
                seaFields.style.display = 'block';
                roadFields.style.display = 'none';
                seaRouteFields.style.display = 'block';
                roadRouteFields.style.display = 'none';
                if (cargoFields) cargoFields.style.display = 'block';
            }} else if (transportMode === 'road') {{
                seaFields.style.display = 'none';
                roadFields.style.display = 'block';
                seaRouteFields.style.display = 'none';
                roadRouteFields.style.display = 'block';
                if (cargoFields) cargoFields.style.display = 'block';
            }} else {{
                seaFields.style.display = 'none';
                roadFields.style.display = 'none';
                seaRouteFields.style.display = 'none';
                roadRouteFields.style.display = 'none';
                if (cargoFields) cargoFields.style.display = 'none';
            }}
            
            updateMRVCalculateButton();
        }}
        
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

        // Note: MRV port search replaced with address search - see initAddressSearch calls in DOMContentLoaded

        // Road distance coordinate inputs
        document.getElementById('road-origin-lat').addEventListener('input', updateRoadCalculateButton);
        document.getElementById('road-origin-lon').addEventListener('input', updateRoadCalculateButton);
        document.getElementById('road-dest-lat').addEventListener('input', updateRoadCalculateButton);
        document.getElementById('road-dest-lon').addEventListener('input', updateRoadCalculateButton);
        
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
            const transportMode = document.getElementById('transport-mode').value;
            const cargoWeight = parseFloat(document.getElementById('cargo-weight').value) || 0;
            const seaBtn = document.getElementById('mrv-calculate-btn');
            const roadBtn = document.getElementById('mrv-calculate-btn-road');

            let isValid = false;

            if (transportMode === 'sea') {{
                const vesselType = document.getElementById('vessel-type').value;
                const vesselSize = document.getElementById('vessel-size').value;
                const seaFuel = document.getElementById('sea-fuel').value;
                const seaOriginLat = document.getElementById('sea-origin-mrv-lat').value;
                const seaOriginLon = document.getElementById('sea-origin-mrv-lon').value;
                const seaDestLat = document.getElementById('sea-dest-mrv-lat').value;
                const seaDestLon = document.getElementById('sea-dest-mrv-lon').value;

                isValid = seaOriginLat && seaOriginLon && seaDestLat && seaDestLon &&
                         vesselType && vesselSize && seaFuel && cargoWeight > 0;
                if (seaBtn) seaBtn.disabled = !isValid;
            }} else if (transportMode === 'road') {{
                const roadMode = document.getElementById('road-mode').value;
                const loadType = document.getElementById('road-load-type').value;
                const roadFuel = document.getElementById('road-fuel').value;
                const originLat = parseFloat(document.getElementById('road-origin-mrv-lat').value);
                const originLon = parseFloat(document.getElementById('road-origin-mrv-lon').value);
                const destLat = parseFloat(document.getElementById('road-dest-mrv-lat').value);
                const destLon = parseFloat(document.getElementById('road-dest-mrv-lon').value);

                isValid = roadMode && loadType && roadFuel && cargoWeight > 0 &&
                         !isNaN(originLat) && !isNaN(originLon) && !isNaN(destLat) && !isNaN(destLon);
                if (roadBtn) roadBtn.disabled = !isValid;
            }}
        }}
        
        function updateRoadCalculateButton() {{
            const originLat = document.getElementById('road-origin-lat').value;
            const originLon = document.getElementById('road-origin-lon').value;
            const destLat = document.getElementById('road-dest-lat').value;
            const destLon = document.getElementById('road-dest-lon').value;
            const btn = document.getElementById('road-calculate-btn');
            
            // Validate coordinates are numbers and within valid ranges
            const isValid = originLat && originLon && destLat && destLon &&
                           !isNaN(parseFloat(originLat)) && !isNaN(parseFloat(originLon)) &&
                           !isNaN(parseFloat(destLat)) && !isNaN(parseFloat(destLon)) &&
                           parseFloat(originLat) >= -90 && parseFloat(originLat) <= 90 &&
                           parseFloat(originLon) >= -180 && parseFloat(originLon) <= 180 &&
                           parseFloat(destLat) >= -90 && parseFloat(destLat) <= 90 &&
                           parseFloat(destLon) >= -180 && parseFloat(destLon) <= 180;
            
            btn.disabled = !isValid;
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
                        <div class="result-header">SEA DISTANCE</div>
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
            const transportMode = document.getElementById('transport-mode').value;
            const cargoWeight = parseFloat(document.getElementById('cargo-weight').value);
            
            if (!transportMode || cargoWeight <= 0) return;
            
            const resultsDiv = document.getElementById('mrv-results');
            const contentDiv = document.getElementById('mrv-results-content');
            
            resultsDiv.classList.add('show');
            contentDiv.innerHTML = '<div class="loading">Calculating ETS costs</div>';
            
            let url = `/api/mrv?transport_mode=${{transportMode}}&cargo_weight=${{cargoWeight}}`;
            
            if (transportMode === 'sea') {{
                const seaOriginLat = parseFloat(document.getElementById('sea-origin-mrv-lat').value);
                const seaOriginLon = parseFloat(document.getElementById('sea-origin-mrv-lon').value);
                const seaDestLat = parseFloat(document.getElementById('sea-dest-mrv-lat').value);
                const seaDestLon = parseFloat(document.getElementById('sea-dest-mrv-lon').value);

                if (isNaN(seaOriginLat) || isNaN(seaOriginLon) || isNaN(seaDestLat) || isNaN(seaDestLon)) return;

                const vesselType = document.getElementById('vessel-type').value;
                const vesselSize = document.getElementById('vessel-size').value;
                const seaFuel = document.getElementById('sea-fuel').value;

                url += `&origin_lat=${{seaOriginLat}}&origin_lon=${{seaOriginLon}}&dest_lat=${{seaDestLat}}&dest_lon=${{seaDestLon}}`;
                url += `&vessel_type=${{encodeURIComponent(vesselType)}}&size=${{encodeURIComponent(vesselSize)}}&fuel=${{encodeURIComponent(seaFuel)}}`;
            }} else if (transportMode === 'road') {{
                const roadMode = document.getElementById('road-mode').value;
                const loadType = document.getElementById('road-load-type').value;
                const roadFuel = document.getElementById('road-fuel').value;
                const originLat = parseFloat(document.getElementById('road-origin-mrv-lat').value);
                const originLon = parseFloat(document.getElementById('road-origin-mrv-lon').value);
                const destLat = parseFloat(document.getElementById('road-dest-mrv-lat').value);
                const destLon = parseFloat(document.getElementById('road-dest-mrv-lon').value);
                
                if (isNaN(originLat) || isNaN(originLon) || isNaN(destLat) || isNaN(destLon)) return;
                
                url += `&origin_lat=${{originLat}}&origin_lon=${{originLon}}&dest_lat=${{destLat}}&dest_lon=${{destLon}}`;
                url += `&road_mode=${{encodeURIComponent(roadMode)}}&load_type=${{encodeURIComponent(loadType)}}&fuel=${{encodeURIComponent(roadFuel)}}`;
            }}
            
            fetch(url)
                .then(response => response.json())
                .then(data => {{
                    if (data.error) {{
                        contentDiv.innerHTML = `<div class="error">${{data.error}}</div>`;
                    }} else {{
                        displayMRVResults(data);
                    }}
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
                        <div class="result-header">🚚 Transport Information</div>
                        <div class="metric-row">
                            <span class="metric-label">Mode</span>
                            <span class="metric-value">${{data.transport_info.mode}}</span>
                        </div>
                `;
                
                if (data.transport_mode === 'sea') {{
                    html += `
                        <div class="metric-row">
                            <span class="metric-label">Vessel Type</span>
                            <span class="metric-value">${{data.transport_info.vessel_type}}</span>
                        </div>
                        <div class="metric-row">
                            <span class="metric-label">Size</span>
                            <span class="metric-value">${{data.transport_info.size}}</span>
                        </div>
                        <div class="metric-row">
                            <span class="metric-label">Fuel</span>
                            <span class="metric-value">${{data.transport_info.fuel}}</span>
                        </div>
                    `;
                }} else {{
                    html += `
                        <div class="metric-row">
                            <span class="metric-label">Vehicle Mode</span>
                            <span class="metric-value">${{data.transport_info.vehicle_mode}}</span>
                        </div>
                        <div class="metric-row">
                            <span class="metric-label">Fuel</span>
                            <span class="metric-value">${{data.transport_info.fuel}}</span>
                        </div>
                    `;
                }}
                
                html += `
                        <div class="metric-row">
                            <span class="metric-label">Emission Factor</span>
                            <span class="metric-value">${{data.transport_info.emission_factor}} g CO₂e/t-km</span>
                        </div>
                        <div class="metric-row">
                            <span class="metric-label">Cargo Weight</span>
                            <span class="metric-value">${{data.cargo_weight}} tonnes</span>
                        </div>
                    </div>
                `;
                
                if (data.distance.success) {{
                    html += `
                        <div class="result-card primary">
                            <div class="result-header">📏 Distance</div>
                            <div class="result-value">${{data.distance.distance_km.toFixed(1)}} <span style="font-size: 1.5rem; color: #64748b;">km</span></div>
                            ${{data.transport_mode === 'sea' ? `<div class="result-subtitle">${{data.distance.distance_nm.toFixed(1)}} nautical miles</div>` : ''}}
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
        
        function calculateRoadDistance() {{
            const originLat = parseFloat(document.getElementById('road-origin-lat').value);
            const originLon = parseFloat(document.getElementById('road-origin-lon').value);
            const destLat = parseFloat(document.getElementById('road-dest-lat').value);
            const destLon = parseFloat(document.getElementById('road-dest-lon').value);
            
            if (isNaN(originLat) || isNaN(originLon) || isNaN(destLat) || isNaN(destLon)) {{
                return;
            }}
            
            const resultsDiv = document.getElementById('road-results');
            const contentDiv = document.getElementById('road-results-content');
            
            resultsDiv.classList.add('show');
            contentDiv.innerHTML = '<div class="loading">Calculating road distance</div>';
            
            const url = `/api/road-distance?origin_lat=${{originLat}}&origin_lon=${{originLon}}&dest_lat=${{destLat}}&dest_lon=${{destLon}}`;
            
            fetch(url)
                .then(response => response.json())
                .then(data => {{
                    displayRoadResults(data);
                }})
                .catch(error => {{
                    contentDiv.innerHTML = `<div class="error">Error: ${{error.message}}</div>`;
                }});
        }}
        
        function displayRoadResults(data) {{
            const contentDiv = document.getElementById('road-results-content');
            let html = '';
            
            if (data.success) {{
                const durationText = data.duration_hours > 0 
                    ? `${{data.duration_hours}}h ${{data.duration_minutes}}m`
                    : `${{data.duration_minutes}}m`;
                
                html += `
                    <div class="result-card primary">
                        <div class="result-header">🛣️ Road Distance</div>
                        <div class="result-value">${{data.distance_km.toFixed(1)}} <span style="font-size: 1.5rem; color: #64748b;">km</span></div>
                        <div class="result-subtitle">${{data.distance_miles.toFixed(1)}} miles</div>
                        <div class="result-meta">Estimated driving time: ${{durationText}}</div>
                        <div class="result-meta">Method: OpenRouteService (Driving Routes)</div>
                    </div>
                    
                    <div class="result-card">
                        <div class="result-header">📍 Route Details</div>
                        <div class="metric-row">
                            <span class="metric-label">Distance (Kilometers)</span>
                            <span class="metric-value">${{data.distance_km.toFixed(2)}} km</span>
                        </div>
                        <div class="metric-row">
                            <span class="metric-label">Distance (Miles)</span>
                            <span class="metric-value">${{data.distance_miles.toFixed(2)}} mi</span>
                        </div>
                        <div class="metric-row">
                            <span class="metric-label">Distance (Meters)</span>
                            <span class="metric-value">${{data.distance_meters.toLocaleString()}} m</span>
                        </div>
                        <div class="metric-row">
                            <span class="metric-label">Estimated Duration</span>
                            <span class="metric-value">${{durationText}}</span>
                        </div>
                        <div class="metric-row">
                            <span class="metric-label">Duration (Seconds)</span>
                            <span class="metric-value">${{data.duration_seconds.toLocaleString()}} s</span>
                        </div>
                    </div>
                `;
            }} else {{
                html += `<div class="error">Error: ${{data.error || 'Failed to calculate road distance'}}</div>`;
            }}
            
            contentDiv.innerHTML = html;
        }}

        // ===== ADDRESS SEARCH AND MAP FUNCTIONALITY =====

        const MAPBOX_TOKEN = 'pk.eyJ1IjoiZXJlbm96Y2V0aW4iLCJhIjoiY21qNzJ4aGRxMDBqdDNjc2VsazlkeWRodiJ9.ppxM8hsfWBKo5nuAkuRmFA';
        let addressSearchDebounceTimers = {{}};
        let addressSearchHighlightedIndex = {{}};
        let roadMap = null;
        let mrvRoadMap = null;
        let roadMarkers = [];
        let mrvRoadMarkers = [];

        // Initialize address search functionality
        function initAddressSearch(prefix, onSelect) {{
            const input = document.getElementById(`${{prefix}}-address`);
            const spinner = document.getElementById(`${{prefix}}-spinner`);
            const clearBtn = document.getElementById(`${{prefix}}-clear`);
            const suggestions = document.getElementById(`${{prefix}}-suggestions`);

            console.log(`initAddressSearch: prefix=${{prefix}}, input=`, input);

            if (!input) {{
                console.error(`initAddressSearch: Input not found for prefix: ${{prefix}}`);
                return;
            }}

            addressSearchHighlightedIndex[prefix] = -1;

            input.addEventListener('input', function(e) {{
                const query = e.target.value;

                // Show/hide clear button
                clearBtn.classList.toggle('show', query.length > 0);

                // Debounce search
                if (addressSearchDebounceTimers[prefix]) {{
                    clearTimeout(addressSearchDebounceTimers[prefix]);
                }}

                if (query.length < 2) {{
                    suggestions.classList.remove('show');
                    return;
                }}

                addressSearchDebounceTimers[prefix] = setTimeout(() => {{
                    searchAddresses(prefix, query);
                }}, 300);
            }});

            input.addEventListener('keydown', function(e) {{
                const items = suggestions.querySelectorAll('.address-suggestion');
                if (!items.length) return;

                if (e.key === 'ArrowDown') {{
                    e.preventDefault();
                    addressSearchHighlightedIndex[prefix] = Math.min(addressSearchHighlightedIndex[prefix] + 1, items.length - 1);
                    updateHighlight(prefix, items);
                }} else if (e.key === 'ArrowUp') {{
                    e.preventDefault();
                    addressSearchHighlightedIndex[prefix] = Math.max(addressSearchHighlightedIndex[prefix] - 1, 0);
                    updateHighlight(prefix, items);
                }} else if (e.key === 'Enter') {{
                    e.preventDefault();
                    if (addressSearchHighlightedIndex[prefix] >= 0 && items[addressSearchHighlightedIndex[prefix]]) {{
                        items[addressSearchHighlightedIndex[prefix]].click();
                    }}
                }} else if (e.key === 'Escape') {{
                    suggestions.classList.remove('show');
                }}
            }});

            input.addEventListener('focus', function() {{
                if (suggestions.children.length > 0) {{
                    suggestions.classList.add('show');
                }}
            }});

            // Click outside to close
            document.addEventListener('click', function(e) {{
                if (!input.contains(e.target) && !suggestions.contains(e.target)) {{
                    suggestions.classList.remove('show');
                }}
            }});
        }}

        function updateHighlight(prefix, items) {{
            items.forEach((item, i) => {{
                item.classList.toggle('highlighted', i === addressSearchHighlightedIndex[prefix]);
            }});
        }}

        function searchAddresses(prefix, query) {{
            const spinner = document.getElementById(`${{prefix}}-spinner`);
            const suggestions = document.getElementById(`${{prefix}}-suggestions`);

            console.log(`searchAddresses: prefix=${{prefix}}, query=${{query}}`);
            spinner.classList.add('show');

            fetch(`/api/geocode?q=${{encodeURIComponent(query)}}&mode=search`)
                .then(response => {{
                    console.log('Geocode API response status:', response.status);
                    return response.json();
                }})
                .then(data => {{
                    console.log('Geocode API data:', data);
                    spinner.classList.remove('show');
                    suggestions.innerHTML = '';
                    addressSearchHighlightedIndex[prefix] = -1;

                    if (data.success && data.data && data.data.length > 0) {{
                        data.data.forEach((result, index) => {{
                            const div = document.createElement('div');
                            div.className = 'address-suggestion';
                            div.innerHTML = `
                                <svg class="address-suggestion-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path><circle cx="12" cy="10" r="3"></circle></svg>
                                <div class="address-suggestion-content">
                                    <div class="address-suggestion-text">${{result.text}}</div>
                                    ${{result.context ? `<div class="address-suggestion-context">${{result.context}}</div>` : ''}}
                                </div>
                            `;
                            div.onclick = () => selectAddress(prefix, result);
                            suggestions.appendChild(div);
                        }});
                        suggestions.classList.add('show');
                    }} else {{
                        suggestions.classList.remove('show');
                    }}
                }})
                .catch(error => {{
                    console.error('Address search error:', error);
                    spinner.classList.remove('show');
                }});
        }}

        function selectAddress(prefix, result) {{
            const input = document.getElementById(`${{prefix}}-address`);
            const latInput = document.getElementById(`${{prefix}}-lat`);
            const lonInput = document.getElementById(`${{prefix}}-lon`);
            const coordsDisplay = document.getElementById(`${{prefix}}-coords`);
            const suggestions = document.getElementById(`${{prefix}}-suggestions`);
            const clearBtn = document.getElementById(`${{prefix}}-clear`);

            input.value = result.placeName;
            latInput.value = result.coordinates.lat;
            lonInput.value = result.coordinates.lng;

            // Show success state with styled location indicator
            coordsDisplay.innerHTML = `
                <div class="location-selected">
                    <svg class="location-selected-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
                        <polyline points="22 4 12 14.01 9 11.01"></polyline>
                    </svg>
                    <div class="location-selected-content">
                        <div class="location-selected-title">Location selected</div>
                        <div class="location-selected-coords">${{result.coordinates.lat.toFixed(6)}}, ${{result.coordinates.lng.toFixed(6)}}</div>
                    </div>
                </div>
            `;
            coordsDisplay.classList.remove('coordinates-display');

            suggestions.classList.remove('show');
            clearBtn.classList.add('show');

            // Update calculate buttons and maps
            if (prefix.includes('mrv')) {{
                updateMRVCalculateButton();
                if (prefix.includes('sea')) {{
                    updateMrvSeaMap();
                }} else {{
                    updateMrvRoadMap();
                }}
            }} else {{
                updateRoadCalculateButton();
                updateRoadMap();
            }}
        }}

        function clearAddressSearch(prefix) {{
            const input = document.getElementById(`${{prefix}}-address`);
            const latInput = document.getElementById(`${{prefix}}-lat`);
            const lonInput = document.getElementById(`${{prefix}}-lon`);
            const coordsDisplay = document.getElementById(`${{prefix}}-coords`);
            const clearBtn = document.getElementById(`${{prefix}}-clear`);
            const suggestions = document.getElementById(`${{prefix}}-suggestions`);

            if (input) input.value = '';
            if (latInput) latInput.value = '';
            if (lonInput) lonInput.value = '';
            if (coordsDisplay) {{
                coordsDisplay.innerHTML = 'Not selected';
                coordsDisplay.classList.add('coordinates-display');
            }}
            if (clearBtn) clearBtn.classList.remove('show');
            if (suggestions) suggestions.classList.remove('show');

            // Update calculate buttons and maps
            if (prefix.includes('mrv')) {{
                updateMRVCalculateButton();
                if (prefix.includes('sea')) {{
                    updateMrvSeaMap();
                }} else {{
                    updateMrvRoadMap();
                }}
            }} else {{
                updateRoadCalculateButton();
                updateRoadMap();
            }}
        }}

        // Initialize maps
        function initMaps() {{
            if (typeof mapboxgl === 'undefined') {{
                console.error('Mapbox GL JS not loaded');
                return;
            }}
            mapboxgl.accessToken = MAPBOX_TOKEN;
        }}

        function updateRoadMap() {{
            const originLat = parseFloat(document.getElementById('road-origin-lat').value);
            const originLon = parseFloat(document.getElementById('road-origin-lon').value);
            const destLat = parseFloat(document.getElementById('road-dest-lat').value);
            const destLon = parseFloat(document.getElementById('road-dest-lon').value);

            const mapDiv = document.getElementById('road-map');
            const placeholder = document.getElementById('road-map-placeholder');

            if (isNaN(originLat) && isNaN(destLat)) {{
                mapDiv.style.display = 'none';
                placeholder.style.display = 'flex';
                return;
            }}

            mapDiv.style.display = 'block';
            placeholder.style.display = 'none';

            if (!roadMap) {{
                roadMap = new mapboxgl.Map({{
                    container: 'road-map',
                    style: 'mapbox://styles/mapbox/light-v11',
                    center: [0, 30],
                    zoom: 2
                }});
                roadMap.addControl(new mapboxgl.NavigationControl());
            }}

            // Clear old markers
            roadMarkers.forEach(m => m.remove());
            roadMarkers = [];

            const bounds = new mapboxgl.LngLatBounds();
            let hasPoints = false;

            if (!isNaN(originLat) && !isNaN(originLon)) {{
                const marker = new mapboxgl.Marker({{ color: '#22c55e' }})
                    .setLngLat([originLon, originLat])
                    .setPopup(new mapboxgl.Popup().setHTML('<div class="marker-label">Origin</div><div class="marker-coords">' + originLat.toFixed(4) + ', ' + originLon.toFixed(4) + '</div>'))
                    .addTo(roadMap);
                roadMarkers.push(marker);
                bounds.extend([originLon, originLat]);
                hasPoints = true;
            }}

            if (!isNaN(destLat) && !isNaN(destLon)) {{
                const marker = new mapboxgl.Marker({{ color: '#ef4444' }})
                    .setLngLat([destLon, destLat])
                    .setPopup(new mapboxgl.Popup().setHTML('<div class="marker-label">Destination</div><div class="marker-coords">' + destLat.toFixed(4) + ', ' + destLon.toFixed(4) + '</div>'))
                    .addTo(roadMap);
                roadMarkers.push(marker);
                bounds.extend([destLon, destLat]);
                hasPoints = true;
            }}

            // Fetch and draw actual road route
            if (!isNaN(originLat) && !isNaN(originLon) && !isNaN(destLat) && !isNaN(destLon)) {{
                placeholder.textContent = 'Loading road route...';
                placeholder.style.display = 'flex';

                fetch(`/api/route-geometry?origin_lat=${{originLat}}&origin_lon=${{originLon}}&dest_lat=${{destLat}}&dest_lon=${{destLon}}&mode=road`)
                    .then(response => response.json())
                    .then(data => {{
                        placeholder.style.display = 'none';
                        if (data.success && data.coordinates && data.coordinates.length > 0) {{
                            const routeData = {{
                                'type': 'Feature',
                                'properties': {{}},
                                'geometry': {{
                                    'type': 'LineString',
                                    'coordinates': data.coordinates
                                }}
                            }};

                            // Extend bounds to include route
                            data.coordinates.forEach(coord => bounds.extend(coord));

                            if (roadMap.isStyleLoaded()) {{
                                try {{
                                    if (roadMap.getSource('route')) {{
                                        roadMap.getSource('route').setData(routeData);
                                    }} else {{
                                        roadMap.addSource('route', {{ 'type': 'geojson', 'data': routeData }});
                                        roadMap.addLayer({{
                                            'id': 'route',
                                            'type': 'line',
                                            'source': 'route',
                                            'layout': {{ 'line-join': 'round', 'line-cap': 'round' }},
                                            'paint': {{ 'line-color': '#f97316', 'line-width': 4, 'line-opacity': 0.8 }}
                                        }});
                                    }}
                                    roadMap.fitBounds(bounds, {{ padding: 60, maxZoom: 12 }});
                                }} catch (e) {{
                                    console.log('Road route layer error:', e);
                                }}
                            }} else {{
                                roadMap.on('load', function() {{
                                    roadMap.addSource('route', {{ 'type': 'geojson', 'data': routeData }});
                                    roadMap.addLayer({{
                                        'id': 'route',
                                        'type': 'line',
                                        'source': 'route',
                                        'layout': {{ 'line-join': 'round', 'line-cap': 'round' }},
                                        'paint': {{ 'line-color': '#f97316', 'line-width': 4, 'line-opacity': 0.8 }}
                                    }});
                                    roadMap.fitBounds(bounds, {{ padding: 60, maxZoom: 12 }});
                                }});
                            }}
                            console.log('Road route loaded with ' + data.coordinates.length + ' waypoints');
                            // Show map legend
                            updateMapLegend('road-map', '#f97316', 'Road Route');
                        }}
                    }})
                    .catch(err => {{
                        console.error('Road route fetch error:', err);
                        placeholder.style.display = 'none';
                    }});
            }} else {{
                // Remove legend if no route
                removeMapLegend('road-map');
            }}

            if (hasPoints) {{
                roadMap.fitBounds(bounds, {{ padding: 60, maxZoom: 12 }});
            }}
        }}

        function updateMrvRoadMap() {{
            const originLat = parseFloat(document.getElementById('road-origin-mrv-lat').value);
            const originLon = parseFloat(document.getElementById('road-origin-mrv-lon').value);
            const destLat = parseFloat(document.getElementById('road-dest-mrv-lat').value);
            const destLon = parseFloat(document.getElementById('road-dest-mrv-lon').value);

            const mapDiv = document.getElementById('mrv-road-map');
            const placeholder = document.getElementById('mrv-road-map-placeholder');

            if (isNaN(originLat) && isNaN(destLat)) {{
                mapDiv.style.display = 'none';
                placeholder.style.display = 'flex';
                return;
            }}

            mapDiv.style.display = 'block';
            placeholder.style.display = 'none';

            if (!mrvRoadMap) {{
                mrvRoadMap = new mapboxgl.Map({{
                    container: 'mrv-road-map',
                    style: 'mapbox://styles/mapbox/light-v11',
                    center: [0, 30],
                    zoom: 2
                }});
                mrvRoadMap.addControl(new mapboxgl.NavigationControl());
            }}

            // Clear old markers
            mrvRoadMarkers.forEach(m => m.remove());
            mrvRoadMarkers = [];

            const bounds = new mapboxgl.LngLatBounds();
            let hasPoints = false;

            if (!isNaN(originLat) && !isNaN(originLon)) {{
                const marker = new mapboxgl.Marker({{ color: '#22c55e' }})
                    .setLngLat([originLon, originLat])
                    .setPopup(new mapboxgl.Popup().setHTML('<div class="marker-label">Origin</div><div class="marker-coords">' + originLat.toFixed(4) + ', ' + originLon.toFixed(4) + '</div>'))
                    .addTo(mrvRoadMap);
                mrvRoadMarkers.push(marker);
                bounds.extend([originLon, originLat]);
                hasPoints = true;
            }}

            if (!isNaN(destLat) && !isNaN(destLon)) {{
                const marker = new mapboxgl.Marker({{ color: '#ef4444' }})
                    .setLngLat([destLon, destLat])
                    .setPopup(new mapboxgl.Popup().setHTML('<div class="marker-label">Destination</div><div class="marker-coords">' + destLat.toFixed(4) + ', ' + destLon.toFixed(4) + '</div>'))
                    .addTo(mrvRoadMap);
                mrvRoadMarkers.push(marker);
                bounds.extend([destLon, destLat]);
                hasPoints = true;
            }}

            // Fetch and draw actual road route
            if (!isNaN(originLat) && !isNaN(originLon) && !isNaN(destLat) && !isNaN(destLon)) {{
                placeholder.textContent = 'Loading road route...';
                placeholder.style.display = 'flex';

                fetch(`/api/route-geometry?origin_lat=${{originLat}}&origin_lon=${{originLon}}&dest_lat=${{destLat}}&dest_lon=${{destLon}}&mode=road`)
                    .then(response => response.json())
                    .then(data => {{
                        placeholder.style.display = 'none';
                        if (data.success && data.coordinates && data.coordinates.length > 0) {{
                            const routeData = {{
                                'type': 'Feature',
                                'properties': {{}},
                                'geometry': {{
                                    'type': 'LineString',
                                    'coordinates': data.coordinates
                                }}
                            }};

                            // Extend bounds to include route
                            data.coordinates.forEach(coord => bounds.extend(coord));

                            if (mrvRoadMap.isStyleLoaded()) {{
                                try {{
                                    if (mrvRoadMap.getSource('road-route')) {{
                                        mrvRoadMap.getSource('road-route').setData(routeData);
                                    }} else {{
                                        mrvRoadMap.addSource('road-route', {{ 'type': 'geojson', 'data': routeData }});
                                        mrvRoadMap.addLayer({{
                                            'id': 'road-route',
                                            'type': 'line',
                                            'source': 'road-route',
                                            'layout': {{ 'line-join': 'round', 'line-cap': 'round' }},
                                            'paint': {{ 'line-color': '#f97316', 'line-width': 4, 'line-opacity': 0.8 }}
                                        }});
                                    }}
                                    mrvRoadMap.fitBounds(bounds, {{ padding: 60, maxZoom: 12 }});
                                }} catch (e) {{
                                    console.log('Road route layer error:', e);
                                }}
                            }} else {{
                                mrvRoadMap.on('load', function() {{
                                    mrvRoadMap.addSource('road-route', {{ 'type': 'geojson', 'data': routeData }});
                                    mrvRoadMap.addLayer({{
                                        'id': 'road-route',
                                        'type': 'line',
                                        'source': 'road-route',
                                        'layout': {{ 'line-join': 'round', 'line-cap': 'round' }},
                                        'paint': {{ 'line-color': '#f97316', 'line-width': 4, 'line-opacity': 0.8 }}
                                    }});
                                    mrvRoadMap.fitBounds(bounds, {{ padding: 60, maxZoom: 12 }});
                                }});
                            }}
                            console.log('Road route loaded with ' + data.coordinates.length + ' waypoints');
                            // Show map legend
                            updateMapLegend('mrv-road-map', '#f97316', 'Road Route');
                        }}
                    }})
                    .catch(err => {{
                        console.error('Road route fetch error:', err);
                        placeholder.style.display = 'none';
                    }});
            }} else {{
                // Remove legend if no route
                removeMapLegend('mrv-road-map');
            }}

            if (hasPoints) {{
                mrvRoadMap.fitBounds(bounds, {{ padding: 60, maxZoom: 12 }});
            }}
        }}

        // Sea route map for MRV
        let mrvSeaMap = null;
        let mrvSeaMarkers = [];

        function updateMrvSeaMap() {{
            const originLat = parseFloat(document.getElementById('sea-origin-mrv-lat').value);
            const originLon = parseFloat(document.getElementById('sea-origin-mrv-lon').value);
            const destLat = parseFloat(document.getElementById('sea-dest-mrv-lat').value);
            const destLon = parseFloat(document.getElementById('sea-dest-mrv-lon').value);

            const mapDiv = document.getElementById('mrv-sea-map');
            const placeholder = document.getElementById('mrv-sea-map-placeholder');

            if (isNaN(originLat) && isNaN(destLat)) {{
                mapDiv.style.display = 'none';
                placeholder.style.display = 'flex';
                return;
            }}

            mapDiv.style.display = 'block';
            placeholder.style.display = 'none';

            if (!mrvSeaMap) {{
                mrvSeaMap = new mapboxgl.Map({{
                    container: 'mrv-sea-map',
                    style: 'mapbox://styles/mapbox/light-v11',
                    center: [0, 30],
                    zoom: 2
                }});
                mrvSeaMap.addControl(new mapboxgl.NavigationControl());
            }}

            // Clear old markers
            mrvSeaMarkers.forEach(m => m.remove());
            mrvSeaMarkers = [];

            const bounds = new mapboxgl.LngLatBounds();
            let hasPoints = false;

            if (!isNaN(originLat) && !isNaN(originLon)) {{
                const marker = new mapboxgl.Marker({{ color: '#22c55e' }})
                    .setLngLat([originLon, originLat])
                    .setPopup(new mapboxgl.Popup().setHTML('<div class="marker-label">Origin</div><div class="marker-coords">' + originLat.toFixed(4) + ', ' + originLon.toFixed(4) + '</div>'))
                    .addTo(mrvSeaMap);
                mrvSeaMarkers.push(marker);
                bounds.extend([originLon, originLat]);
                hasPoints = true;
            }}

            if (!isNaN(destLat) && !isNaN(destLon)) {{
                const marker = new mapboxgl.Marker({{ color: '#ef4444' }})
                    .setLngLat([destLon, destLat])
                    .setPopup(new mapboxgl.Popup().setHTML('<div class="marker-label">Destination</div><div class="marker-coords">' + destLat.toFixed(4) + ', ' + destLon.toFixed(4) + '</div>'))
                    .addTo(mrvSeaMap);
                mrvSeaMarkers.push(marker);
                bounds.extend([destLon, destLat]);
                hasPoints = true;
            }}

            // Fetch and draw actual sea route
            if (!isNaN(originLat) && !isNaN(originLon) && !isNaN(destLat) && !isNaN(destLon)) {{
                // Show loading indicator
                placeholder.textContent = 'Loading sea route...';
                placeholder.style.display = 'flex';

                fetch(`/api/route-geometry?origin_lat=${{originLat}}&origin_lon=${{originLon}}&dest_lat=${{destLat}}&dest_lon=${{destLon}}&mode=sea`)
                    .then(response => response.json())
                    .then(data => {{
                        placeholder.style.display = 'none';
                        if (data.success && data.coordinates && data.coordinates.length > 0) {{
                            const routeData = {{
                                'type': 'Feature',
                                'properties': {{}},
                                'geometry': {{
                                    'type': 'LineString',
                                    'coordinates': data.coordinates
                                }}
                            }};

                            // Extend bounds to include route
                            data.coordinates.forEach(coord => bounds.extend(coord));

                            if (mrvSeaMap.isStyleLoaded()) {{
                                try {{
                                    if (mrvSeaMap.getSource('sea-route')) {{
                                        mrvSeaMap.getSource('sea-route').setData(routeData);
                                    }} else {{
                                        mrvSeaMap.addSource('sea-route', {{ 'type': 'geojson', 'data': routeData }});
                                        mrvSeaMap.addLayer({{
                                            'id': 'sea-route',
                                            'type': 'line',
                                            'source': 'sea-route',
                                            'layout': {{ 'line-join': 'round', 'line-cap': 'round' }},
                                            'paint': {{ 'line-color': '#0ea5e9', 'line-width': 3, 'line-opacity': 0.8 }}
                                        }});
                                    }}
                                    mrvSeaMap.fitBounds(bounds, {{ padding: 60, maxZoom: 10 }});
                                }} catch (e) {{
                                    console.log('Sea route layer error:', e);
                                }}
                            }} else {{
                                mrvSeaMap.on('load', function() {{
                                    mrvSeaMap.addSource('sea-route', {{ 'type': 'geojson', 'data': routeData }});
                                    mrvSeaMap.addLayer({{
                                        'id': 'sea-route',
                                        'type': 'line',
                                        'source': 'sea-route',
                                        'layout': {{ 'line-join': 'round', 'line-cap': 'round' }},
                                        'paint': {{ 'line-color': '#0ea5e9', 'line-width': 3, 'line-opacity': 0.8 }}
                                    }});
                                    mrvSeaMap.fitBounds(bounds, {{ padding: 60, maxZoom: 10 }});
                                }});
                            }}
                            console.log('Sea route loaded with ' + data.coordinates.length + ' waypoints');
                            // Show map legend
                            updateMapLegend('mrv-sea-map', '#0ea5e9', 'Sea Route');
                        }}
                    }})
                    .catch(err => {{
                        console.error('Sea route fetch error:', err);
                        placeholder.style.display = 'none';
                    }});
            }} else {{
                // Remove legend if no route
                removeMapLegend('mrv-sea-map');
            }}

            if (hasPoints) {{
                mrvSeaMap.fitBounds(bounds, {{ padding: 60, maxZoom: 12 }});
            }}
        }}

        // Initialize address search on page load
        document.addEventListener('DOMContentLoaded', function() {{
            initMaps();

            // Road Distance tab
            initAddressSearch('road-origin', updateRoadMap);
            initAddressSearch('road-dest', updateRoadMap);

            // MRV Sea transport
            initAddressSearch('sea-origin-mrv', updateMrvSeaMap);
            initAddressSearch('sea-dest-mrv', updateMrvSeaMap);

            // MRV Road transport
            initAddressSearch('road-origin-mrv', updateMrvRoadMap);
            initAddressSearch('road-dest-mrv', updateMrvRoadMap);

            // Comparison Wizard
            initWizardAddressSearch('wizard-origin');
            initWizardAddressSearch('wizard-dest');
        }});

        // Update the road calculate button check to use the new hidden inputs
        function updateRoadCalculateButton() {{
            const originLat = document.getElementById('road-origin-lat').value;
            const originLon = document.getElementById('road-origin-lon').value;
            const destLat = document.getElementById('road-dest-lat').value;
            const destLon = document.getElementById('road-dest-lon').value;
            const btn = document.getElementById('road-calculate-btn');

            const isValid = originLat && originLon && destLat && destLon &&
                           !isNaN(parseFloat(originLat)) && !isNaN(parseFloat(originLon)) &&
                           !isNaN(parseFloat(destLat)) && !isNaN(parseFloat(destLon)) &&
                           parseFloat(originLat) >= -90 && parseFloat(originLat) <= 90 &&
                           parseFloat(originLon) >= -180 && parseFloat(originLon) <= 180 &&
                           parseFloat(destLat) >= -90 && parseFloat(destLat) <= 90 &&
                           parseFloat(destLon) >= -180 && parseFloat(destLon) <= 180;

            btn.disabled = !isValid;
        }}

        // ===== COMPARISON WIZARD FUNCTIONALITY =====

        let wizardCurrentStep = 1;
        let comparisonChart = null;
        let comparisonMap = null;
        let comparisonMarkers = [];
        let wizardPreviewMap = null;
        let wizardPreviewMarkers = [];
        let comparisonResults = {{ sea: null, road: null }};

        // Initialize wizard dropdowns when transport options are loaded
        function initWizardDropdowns() {{
            if (!transportOptions) return;

            // Populate sea vessel types
            const vesselTypeSelect = document.getElementById('wizard-vessel-type');
            if (vesselTypeSelect && transportOptions.sea && transportOptions.sea.vessel_types) {{
                vesselTypeSelect.innerHTML = '<option value="">-- Select Vessel Type --</option>';
                transportOptions.sea.vessel_types.forEach(type => {{
                    const option = document.createElement('option');
                    option.value = type;
                    option.textContent = type;
                    vesselTypeSelect.appendChild(option);
                }});
            }}

            // Populate road modes
            const roadModeSelect = document.getElementById('wizard-road-mode');
            if (roadModeSelect && transportOptions.road && transportOptions.road.modes) {{
                roadModeSelect.innerHTML = '<option value="">-- Select Mode --</option>';
                transportOptions.road.modes.forEach(mode => {{
                    const option = document.createElement('option');
                    option.value = mode;
                    option.textContent = mode;
                    roadModeSelect.appendChild(option);
                }});
            }}
        }}

        // Sea dropdown cascading logic
        function updateWizardSeaDropdowns() {{
            const vesselTypeSelect = document.getElementById('wizard-vessel-type');
            const vesselSizeSelect = document.getElementById('wizard-vessel-size');
            const seaFuelSelect = document.getElementById('wizard-sea-fuel');

            if (!vesselTypeSelect || !vesselSizeSelect || !seaFuelSelect) return;
            if (!transportOptions || !transportOptions.sea) return;

            const selectedVesselType = vesselTypeSelect.value;
            const selectedSize = vesselSizeSelect.value;

            const matchingSizes = new Set();
            const matchingFuels = new Set();

            transportOptions.sea.all_factors.forEach(factor => {{
                if (selectedVesselType && factor.vessel_type !== selectedVesselType) return;
                matchingSizes.add(factor.size);
                if (!selectedSize || factor.size === selectedSize) {{
                    matchingFuels.add(factor.fuel);
                }}
            }});

            // Update sizes
            if (selectedVesselType) {{
                const sizeValue = vesselSizeSelect.value;
                vesselSizeSelect.innerHTML = '<option value="">-- Select Size --</option>';
                Array.from(matchingSizes).sort().forEach(size => {{
                    const option = document.createElement('option');
                    option.value = size;
                    option.textContent = size;
                    if (size === sizeValue) option.selected = true;
                    vesselSizeSelect.appendChild(option);
                }});
                vesselSizeSelect.disabled = false;
            }} else {{
                vesselSizeSelect.innerHTML = '<option value="">-- Select Size --</option>';
                vesselSizeSelect.disabled = true;
            }}

            // Update fuels
            if (selectedVesselType && vesselSizeSelect.value) {{
                const fuelValue = seaFuelSelect.value;
                seaFuelSelect.innerHTML = '<option value="">-- Select Fuel --</option>';
                Array.from(matchingFuels).sort().forEach(fuel => {{
                    const option = document.createElement('option');
                    option.value = fuel;
                    option.textContent = fuel;
                    if (fuel === fuelValue) option.selected = true;
                    seaFuelSelect.appendChild(option);
                }});
                seaFuelSelect.disabled = false;
            }} else {{
                seaFuelSelect.innerHTML = '<option value="">-- Select Fuel --</option>';
                seaFuelSelect.disabled = true;
            }}
        }}

        // Road dropdown cascading logic
        function updateWizardRoadDropdowns() {{
            const roadModeSelect = document.getElementById('wizard-road-mode');
            const roadLoadTypeSelect = document.getElementById('wizard-road-load-type');
            const roadFuelSelect = document.getElementById('wizard-road-fuel');

            if (!roadModeSelect || !roadLoadTypeSelect || !roadFuelSelect) return;
            if (!transportOptions || !transportOptions.road) return;

            const selectedRoadMode = roadModeSelect.value;
            const selectedLoadType = roadLoadTypeSelect.value;

            const matchingLoadTypes = new Set();
            const matchingFuels = new Set();

            transportOptions.road.all_factors.forEach(factor => {{
                if (selectedRoadMode && factor.mode !== selectedRoadMode) return;
                if (factor.load_type) matchingLoadTypes.add(factor.load_type);
                if (!selectedLoadType || factor.load_type === selectedLoadType) {{
                    matchingFuels.add(factor.fuel);
                }}
            }});

            // Update load types
            if (selectedRoadMode) {{
                const loadTypeValue = roadLoadTypeSelect.value;
                roadLoadTypeSelect.innerHTML = '<option value="">-- Select Load Type --</option>';
                Array.from(matchingLoadTypes).sort().forEach(loadType => {{
                    const option = document.createElement('option');
                    option.value = loadType;
                    option.textContent = loadType;
                    if (loadType === loadTypeValue) option.selected = true;
                    roadLoadTypeSelect.appendChild(option);
                }});
                roadLoadTypeSelect.disabled = false;
            }} else {{
                roadLoadTypeSelect.innerHTML = '<option value="">-- Select Load Type --</option>';
                roadLoadTypeSelect.disabled = true;
            }}

            // Update fuels
            if (selectedRoadMode && roadLoadTypeSelect.value) {{
                const fuelValue = roadFuelSelect.value;
                roadFuelSelect.innerHTML = '<option value="">-- Select Fuel --</option>';
                Array.from(matchingFuels).sort().forEach(fuel => {{
                    const option = document.createElement('option');
                    option.value = fuel;
                    option.textContent = fuel;
                    if (fuel === fuelValue) option.selected = true;
                    roadFuelSelect.appendChild(option);
                }});
                roadFuelSelect.disabled = false;
            }} else {{
                roadFuelSelect.innerHTML = '<option value="">-- Select Fuel --</option>';
                roadFuelSelect.disabled = true;
            }}
        }}

        // Validate current step and update button states
        function updateWizardState() {{
            const nextBtn = document.getElementById('wizard-next-btn');
            const compareBtn = document.getElementById('wizard-compare-btn');

            let stepValid = false;

            if (wizardCurrentStep === 1) {{
                // Step 1: Vehicles + Cargo weight
                const vesselType = document.getElementById('wizard-vessel-type').value;
                const vesselSize = document.getElementById('wizard-vessel-size').value;
                const seaFuel = document.getElementById('wizard-sea-fuel').value;
                const roadMode = document.getElementById('wizard-road-mode').value;
                const loadType = document.getElementById('wizard-road-load-type').value;
                const roadFuel = document.getElementById('wizard-road-fuel').value;
                const cargoWeight = parseFloat(document.getElementById('wizard-cargo-weight').value);

                stepValid = vesselType && vesselSize && seaFuel && roadMode && loadType && roadFuel && cargoWeight > 0;
            }} else if (wizardCurrentStep === 2) {{
                // Step 2: Route selection
                const originLat = document.getElementById('wizard-origin-lat').value;
                const originLon = document.getElementById('wizard-origin-lon').value;
                const destLat = document.getElementById('wizard-dest-lat').value;
                const destLon = document.getElementById('wizard-dest-lon').value;

                stepValid = originLat && originLon && destLat && destLon;
            }}

            if (nextBtn) nextBtn.disabled = !stepValid;
            if (compareBtn) compareBtn.disabled = !stepValid;
        }}

        // Navigate to next step
        function wizardNextStep() {{
            if (wizardCurrentStep >= 2) return;
            wizardCurrentStep++;
            updateWizardUI();
        }}

        // Navigate to previous step
        function wizardPrevStep() {{
            if (wizardCurrentStep <= 1) return;
            wizardCurrentStep--;
            updateWizardUI();
        }}

        // Update wizard UI based on current step
        function updateWizardUI() {{
            // Update step indicators
            document.querySelectorAll('.wizard-step').forEach((step, index) => {{
                const stepNum = index + 1;
                step.classList.remove('active', 'completed');
                if (stepNum < wizardCurrentStep) {{
                    step.classList.add('completed');
                }} else if (stepNum === wizardCurrentStep) {{
                    step.classList.add('active');
                }}
            }});

            // Update step connectors
            document.querySelectorAll('.wizard-step-connector').forEach((connector, index) => {{
                connector.classList.toggle('completed', index < wizardCurrentStep - 1);
            }});

            // Show/hide step content (2 steps now)
            for (let i = 1; i <= 2; i++) {{
                const stepEl = document.getElementById(`wizard-step-${{i}}`);
                if (stepEl) stepEl.style.display = i === wizardCurrentStep ? 'block' : 'none';
            }}

            // Update navigation buttons
            const backBtn = document.getElementById('wizard-back-btn');
            const nextBtn = document.getElementById('wizard-next-btn');
            const compareBtn = document.getElementById('wizard-compare-btn');

            if (backBtn) backBtn.style.display = wizardCurrentStep > 1 ? 'inline-block' : 'none';
            if (nextBtn) nextBtn.style.display = wizardCurrentStep < 2 ? 'inline-block' : 'none';
            if (compareBtn) compareBtn.style.display = wizardCurrentStep === 2 ? 'inline-block' : 'none';

            updateWizardState();

            // Update preview map if on step 2
            if (wizardCurrentStep === 2) {{
                updateWizardPreviewMap();
            }}
        }}

        // Clear wizard address field
        function clearWizardAddress(prefix) {{
            const addressInput = document.getElementById(`${{prefix}}-address`);
            const latInput = document.getElementById(`${{prefix}}-lat`);
            const lonInput = document.getElementById(`${{prefix}}-lon`);
            const coordsDisplay = document.getElementById(`${{prefix}}-coords`);
            const suggestions = document.getElementById(`${{prefix}}-suggestions`);

            if (addressInput) addressInput.value = '';
            if (latInput) latInput.value = '';
            if (lonInput) lonInput.value = '';
            if (coordsDisplay) {{
                coordsDisplay.textContent = 'Not selected';
                coordsDisplay.className = 'coordinates-display';
            }}
            if (suggestions) suggestions.style.display = 'none';

            updateWizardState();
            updateWizardPreviewMap();
        }}

        // Preview map for route selection step
        function updateWizardPreviewMap() {{
            const originLat = parseFloat(document.getElementById('wizard-origin-lat').value);
            const originLon = parseFloat(document.getElementById('wizard-origin-lon').value);
            const destLat = parseFloat(document.getElementById('wizard-dest-lat').value);
            const destLon = parseFloat(document.getElementById('wizard-dest-lon').value);

            const mapDiv = document.getElementById('wizard-preview-map');
            const placeholder = document.getElementById('wizard-preview-map-placeholder');
            const container = document.getElementById('wizard-preview-map-container');

            if (isNaN(originLat) && isNaN(destLat)) {{
                if (mapDiv) mapDiv.style.display = 'none';
                if (placeholder) placeholder.style.display = 'flex';
                return;
            }}

            if (mapDiv) mapDiv.style.display = 'block';
            if (placeholder) placeholder.style.display = 'none';

            if (!wizardPreviewMap) {{
                wizardPreviewMap = new mapboxgl.Map({{
                    container: 'wizard-preview-map',
                    style: 'mapbox://styles/mapbox/light-v11',
                    center: [0, 30],
                    zoom: 2
                }});
                wizardPreviewMap.addControl(new mapboxgl.NavigationControl());
            }}

            // Clear old markers
            wizardPreviewMarkers.forEach(m => m.remove());
            wizardPreviewMarkers = [];

            // Clear old routes
            if (wizardPreviewMap.isStyleLoaded()) {{
                ['preview-sea-route', 'preview-road-route'].forEach(id => {{
                    if (wizardPreviewMap.getLayer(id)) wizardPreviewMap.removeLayer(id);
                    if (wizardPreviewMap.getSource(id)) wizardPreviewMap.removeSource(id);
                }});
            }}

            // Clear old legend
            const existingLegend = container.querySelector('.wizard-preview-legend');
            if (existingLegend) existingLegend.remove();

            const bounds = new mapboxgl.LngLatBounds();
            let hasPoints = false;

            if (!isNaN(originLat) && !isNaN(originLon)) {{
                const marker = new mapboxgl.Marker({{ color: '#22c55e' }})
                    .setLngLat([originLon, originLat])
                    .setPopup(new mapboxgl.Popup().setHTML('<div class="marker-label">Origin</div>'))
                    .addTo(wizardPreviewMap);
                wizardPreviewMarkers.push(marker);
                bounds.extend([originLon, originLat]);
                hasPoints = true;
            }}

            if (!isNaN(destLat) && !isNaN(destLon)) {{
                const marker = new mapboxgl.Marker({{ color: '#ef4444' }})
                    .setLngLat([destLon, destLat])
                    .setPopup(new mapboxgl.Popup().setHTML('<div class="marker-label">Destination</div>'))
                    .addTo(wizardPreviewMap);
                wizardPreviewMarkers.push(marker);
                bounds.extend([destLon, destLat]);
                hasPoints = true;
            }}

            // If both points selected, fetch and show routes
            if (!isNaN(originLat) && !isNaN(originLon) && !isNaN(destLat) && !isNaN(destLon)) {{
                // Show loading state
                placeholder.textContent = 'Loading route previews...';
                placeholder.style.display = 'flex';

                // Fetch both routes in parallel
                Promise.all([
                    fetch(`/api/route-geometry?origin_lat=${{originLat}}&origin_lon=${{originLon}}&dest_lat=${{destLat}}&dest_lon=${{destLon}}&mode=sea`),
                    fetch(`/api/route-geometry?origin_lat=${{originLat}}&origin_lon=${{originLon}}&dest_lat=${{destLat}}&dest_lon=${{destLon}}&mode=road`)
                ])
                .then(([seaRes, roadRes]) => Promise.all([seaRes.json(), roadRes.json()]))
                .then(([seaData, roadData]) => {{
                    placeholder.style.display = 'none';

                    // Wait for map style to load
                    const addRoutes = () => {{
                        // Remove existing route layers/sources
                        ['preview-sea-route', 'preview-road-route'].forEach(id => {{
                            if (wizardPreviewMap.getLayer(id)) wizardPreviewMap.removeLayer(id);
                            if (wizardPreviewMap.getSource(id)) wizardPreviewMap.removeSource(id);
                        }});

                        // Add sea route (blue)
                        if (seaData.success && seaData.coordinates && seaData.coordinates.length > 0) {{
                            wizardPreviewMap.addSource('preview-sea-route', {{
                                'type': 'geojson',
                                'data': {{
                                    'type': 'Feature',
                                    'properties': {{}},
                                    'geometry': {{ 'type': 'LineString', 'coordinates': seaData.coordinates }}
                                }}
                            }});
                            wizardPreviewMap.addLayer({{
                                'id': 'preview-sea-route',
                                'type': 'line',
                                'source': 'preview-sea-route',
                                'layout': {{ 'line-join': 'round', 'line-cap': 'round' }},
                                'paint': {{ 'line-color': '#0ea5e9', 'line-width': 4, 'line-opacity': 0.8 }}
                            }});
                            seaData.coordinates.forEach(coord => bounds.extend(coord));
                        }}

                        // Add road route (orange)
                        if (roadData.success && roadData.coordinates && roadData.coordinates.length > 0) {{
                            wizardPreviewMap.addSource('preview-road-route', {{
                                'type': 'geojson',
                                'data': {{
                                    'type': 'Feature',
                                    'properties': {{}},
                                    'geometry': {{ 'type': 'LineString', 'coordinates': roadData.coordinates }}
                                }}
                            }});
                            wizardPreviewMap.addLayer({{
                                'id': 'preview-road-route',
                                'type': 'line',
                                'source': 'preview-road-route',
                                'layout': {{ 'line-join': 'round', 'line-cap': 'round' }},
                                'paint': {{ 'line-color': '#f97316', 'line-width': 4, 'line-opacity': 0.8 }}
                            }});
                            roadData.coordinates.forEach(coord => bounds.extend(coord));
                        }}

                        // Fit bounds to show both routes
                        wizardPreviewMap.fitBounds(bounds, {{ padding: 50, maxZoom: 8 }});

                        // Add legend
                        updateWizardPreviewLegend(seaData, roadData);
                    }};

                    if (wizardPreviewMap.isStyleLoaded()) {{
                        addRoutes();
                    }} else {{
                        wizardPreviewMap.on('load', addRoutes);
                    }}
                }})
                .catch(err => {{
                    console.error('Route preview error:', err);
                    placeholder.style.display = 'none';
                    if (hasPoints) {{
                        wizardPreviewMap.fitBounds(bounds, {{ padding: 60, maxZoom: 10 }});
                    }}
                }});
            }} else if (hasPoints) {{
                wizardPreviewMap.fitBounds(bounds, {{ padding: 60, maxZoom: 10 }});
            }}
        }}

        function updateWizardPreviewLegend(seaData, roadData) {{
            const container = document.getElementById('wizard-preview-map-container');
            if (!container) return;

            // Remove existing legend
            const existingLegend = container.querySelector('.wizard-preview-legend');
            if (existingLegend) existingLegend.remove();

            const seaDistance = seaData.distance_km ? `${{seaData.distance_km.toFixed(0)}} km` : 'N/A';
            const roadDistance = roadData.distance_km ? `${{roadData.distance_km.toFixed(0)}} km` : 'N/A';

            const legend = document.createElement('div');
            legend.className = 'wizard-preview-legend';
            legend.style.cssText = 'position:absolute;bottom:1rem;left:1rem;background:rgba(255,255,255,0.95);padding:0.75rem 1rem;border-radius:8px;box-shadow:0 2px 8px rgba(0,0,0,0.15);z-index:10;font-size:0.85rem;';
            legend.innerHTML = `
                <div style="display:flex;align-items:center;gap:0.5rem;margin-bottom:0.5rem;">
                    <div style="width:20px;height:4px;background:#0ea5e9;border-radius:2px;"></div>
                    <span><strong>Sea:</strong> ${{seaDistance}}</span>
                </div>
                <div style="display:flex;align-items:center;gap:0.5rem;">
                    <div style="width:20px;height:4px;background:#f97316;border-radius:2px;"></div>
                    <span><strong>Road:</strong> ${{roadDistance}}</span>
                </div>
            `;
            container.appendChild(legend);
        }}

        // Run the comparison - make dual API calls
        async function runComparison() {{
            const compareBtn = document.getElementById('wizard-compare-btn');
            compareBtn.disabled = true;
            compareBtn.textContent = 'CALCULATING...';

            const vesselType = document.getElementById('wizard-vessel-type').value;
            const vesselSize = document.getElementById('wizard-vessel-size').value;
            const seaFuel = document.getElementById('wizard-sea-fuel').value;
            const roadMode = document.getElementById('wizard-road-mode').value;
            const loadType = document.getElementById('wizard-road-load-type').value;
            const roadFuel = document.getElementById('wizard-road-fuel').value;
            const originLat = document.getElementById('wizard-origin-lat').value;
            const originLon = document.getElementById('wizard-origin-lon').value;
            const destLat = document.getElementById('wizard-dest-lat').value;
            const destLon = document.getElementById('wizard-dest-lon').value;
            const cargoWeight = document.getElementById('wizard-cargo-weight').value;

            try {{
                // Make parallel API calls for sea and road
                const [seaResponse, roadResponse, seaRouteResponse, roadRouteResponse] = await Promise.all([
                    fetch(`/api/mrv?transport_mode=sea&cargo_weight=${{cargoWeight}}&origin_lat=${{originLat}}&origin_lon=${{originLon}}&dest_lat=${{destLat}}&dest_lon=${{destLon}}&vessel_type=${{encodeURIComponent(vesselType)}}&size=${{encodeURIComponent(vesselSize)}}&fuel=${{encodeURIComponent(seaFuel)}}`),
                    fetch(`/api/mrv?transport_mode=road&cargo_weight=${{cargoWeight}}&origin_lat=${{originLat}}&origin_lon=${{originLon}}&dest_lat=${{destLat}}&dest_lon=${{destLon}}&road_mode=${{encodeURIComponent(roadMode)}}&load_type=${{encodeURIComponent(loadType)}}&fuel=${{encodeURIComponent(roadFuel)}}`),
                    fetch(`/api/route-geometry?origin_lat=${{originLat}}&origin_lon=${{originLon}}&dest_lat=${{destLat}}&dest_lon=${{destLon}}&mode=sea`),
                    fetch(`/api/route-geometry?origin_lat=${{originLat}}&origin_lon=${{originLon}}&dest_lat=${{destLat}}&dest_lon=${{destLon}}&mode=road`)
                ]);

                const seaData = await seaResponse.json();
                const roadData = await roadResponse.json();
                const seaRouteData = await seaRouteResponse.json();
                const roadRouteData = await roadRouteResponse.json();

                if (seaData.error || roadData.error) {{
                    throw new Error(seaData.error || roadData.error);
                }}

                comparisonResults = {{
                    sea: {{ ...seaData, route: seaRouteData }},
                    road: {{ ...roadData, route: roadRouteData }}
                }};

                displayComparisonResults();

            }} catch (error) {{
                console.error('Comparison error:', error);
                alert('Error running comparison: ' + error.message);
            }} finally {{
                compareBtn.disabled = false;
                compareBtn.textContent = 'RUN COMPARISON';
            }}
        }}

        // Display comparison results
        function displayComparisonResults() {{
            // Show results section, hide wizard
            document.getElementById('comparison-results').style.display = 'block';
            document.getElementById('comparison-wizard').style.display = 'none';

            const sea = comparisonResults.sea;
            const road = comparisonResults.road;

            // Update CO2 metrics
            document.getElementById('sea-co2-value').textContent = sea.emissions.co2_tonnes.toFixed(2);
            document.getElementById('road-co2-value').textContent = road.emissions.co2_tonnes.toFixed(2);
            document.getElementById('sea-distance-detail').textContent = `${{sea.distance.distance_km.toFixed(1)}} km`;
            document.getElementById('road-distance-detail').textContent = `${{road.distance.distance_km.toFixed(1)}} km`;

            // Calculate difference
            const diff = Math.abs(sea.emissions.co2_tonnes - road.emissions.co2_tonnes);
            const diffPercent = ((diff / Math.max(sea.emissions.co2_tonnes, road.emissions.co2_tonnes)) * 100).toFixed(1);
            const betterOption = sea.emissions.co2_tonnes < road.emissions.co2_tonnes ? 'Sea' : 'Road';

            document.getElementById('co2-savings-value').textContent = diff.toFixed(2);
            document.getElementById('co2-savings-percent').textContent = `${{diffPercent}}% lower with ${{betterOption}}`;

            // Update map with both routes
            updateComparisonMap();

            // Update chart
            updateComparisonChart();

            // Generate insights
            generateInsights();

            // Scroll to results
            document.getElementById('comparison-results').scrollIntoView({{ behavior: 'smooth' }});
        }}

        // Update comparison map with both routes
        function updateComparisonMap() {{
            const mapDiv = document.getElementById('comparison-map');
            const placeholder = document.getElementById('comparison-map-placeholder');

            if (mapDiv) mapDiv.style.display = 'block';
            if (placeholder) placeholder.style.display = 'none';

            if (!comparisonMap) {{
                comparisonMap = new mapboxgl.Map({{
                    container: 'comparison-map',
                    style: 'mapbox://styles/mapbox/light-v11',
                    center: [0, 30],
                    zoom: 2
                }});
                comparisonMap.addControl(new mapboxgl.NavigationControl());
            }}

            // Clear old markers
            comparisonMarkers.forEach(m => m.remove());
            comparisonMarkers = [];

            const bounds = new mapboxgl.LngLatBounds();

            // Add origin marker
            const originLat = parseFloat(document.getElementById('wizard-origin-lat').value);
            const originLon = parseFloat(document.getElementById('wizard-origin-lon').value);
            const destLat = parseFloat(document.getElementById('wizard-dest-lat').value);
            const destLon = parseFloat(document.getElementById('wizard-dest-lon').value);

            const originMarker = new mapboxgl.Marker({{ color: '#22c55e' }})
                .setLngLat([originLon, originLat])
                .setPopup(new mapboxgl.Popup().setHTML('<div class="marker-label">Origin</div>'))
                .addTo(comparisonMap);
            comparisonMarkers.push(originMarker);
            bounds.extend([originLon, originLat]);

            const destMarker = new mapboxgl.Marker({{ color: '#ef4444' }})
                .setLngLat([destLon, destLat])
                .setPopup(new mapboxgl.Popup().setHTML('<div class="marker-label">Destination</div>'))
                .addTo(comparisonMap);
            comparisonMarkers.push(destMarker);
            bounds.extend([destLon, destLat]);

            // Add both routes when map is ready
            const addRoutes = () => {{
                // Sea route (blue)
                if (comparisonResults.sea.route && comparisonResults.sea.route.coordinates && comparisonResults.sea.route.coordinates.length > 0) {{
                    const seaRouteData = {{
                        'type': 'Feature',
                        'properties': {{}},
                        'geometry': {{
                            'type': 'LineString',
                            'coordinates': comparisonResults.sea.route.coordinates
                        }}
                    }};

                    try {{
                        if (comparisonMap.getSource('comparison-sea-route')) {{
                            comparisonMap.getSource('comparison-sea-route').setData(seaRouteData);
                        }} else {{
                            comparisonMap.addSource('comparison-sea-route', {{ 'type': 'geojson', 'data': seaRouteData }});
                            comparisonMap.addLayer({{
                                'id': 'comparison-sea-route',
                                'type': 'line',
                                'source': 'comparison-sea-route',
                                'layout': {{ 'line-join': 'round', 'line-cap': 'round' }},
                                'paint': {{ 'line-color': '#0ea5e9', 'line-width': 4, 'line-opacity': 0.8 }}
                            }});
                        }}
                        comparisonResults.sea.route.coordinates.forEach(coord => bounds.extend(coord));
                    }} catch (e) {{
                        console.log('Sea route layer error:', e);
                    }}
                }}

                // Road route (orange)
                if (comparisonResults.road.route && comparisonResults.road.route.coordinates && comparisonResults.road.route.coordinates.length > 0) {{
                    const roadRouteData = {{
                        'type': 'Feature',
                        'properties': {{}},
                        'geometry': {{
                            'type': 'LineString',
                            'coordinates': comparisonResults.road.route.coordinates
                        }}
                    }};

                    try {{
                        if (comparisonMap.getSource('comparison-road-route')) {{
                            comparisonMap.getSource('comparison-road-route').setData(roadRouteData);
                        }} else {{
                            comparisonMap.addSource('comparison-road-route', {{ 'type': 'geojson', 'data': roadRouteData }});
                            comparisonMap.addLayer({{
                                'id': 'comparison-road-route',
                                'type': 'line',
                                'source': 'comparison-road-route',
                                'layout': {{ 'line-join': 'round', 'line-cap': 'round' }},
                                'paint': {{ 'line-color': '#f97316', 'line-width': 4, 'line-opacity': 0.8 }}
                            }});
                        }}
                        comparisonResults.road.route.coordinates.forEach(coord => bounds.extend(coord));
                    }} catch (e) {{
                        console.log('Road route layer error:', e);
                    }}
                }}

                comparisonMap.fitBounds(bounds, {{ padding: 60, maxZoom: 10 }});
                updateComparisonMapLegend();
            }};

            if (comparisonMap.isStyleLoaded()) {{
                addRoutes();
            }} else {{
                comparisonMap.on('load', addRoutes);
            }}
        }}

        // Update comparison map legend
        function updateComparisonMapLegend() {{
            const container = document.getElementById('comparison-map-container');
            if (!container) return;

            const existingLegend = container.querySelector('.comparison-map-legend');
            if (existingLegend) existingLegend.remove();

            const legend = document.createElement('div');
            legend.className = 'comparison-map-legend';
            legend.innerHTML = `
                <div class="legend-item">
                    <div class="legend-dot" style="background:#22c55e"></div>
                    <span>Origin</span>
                </div>
                <div class="legend-item">
                    <div class="legend-dot" style="background:#ef4444"></div>
                    <span>Destination</span>
                </div>
                <div class="legend-item">
                    <div class="legend-line" style="background:#0ea5e9"></div>
                    <span>Sea Route</span>
                </div>
                <div class="legend-item">
                    <div class="legend-line" style="background:#f97316"></div>
                    <span>Road Route</span>
                </div>
            `;
            container.appendChild(legend);
        }}

        // Update comparison chart with Chart.js - Modern design
        function updateComparisonChart() {{
            const ctx = document.getElementById('comparison-chart');
            if (!ctx) return;

            // Destroy existing chart if any
            if (comparisonChart) {{
                comparisonChart.destroy();
            }}

            const years = Object.keys(comparisonResults.sea.ets_costs).sort();
            const seaCosts = years.map(year => comparisonResults.sea.ets_costs[year].cost_eur);
            const roadCosts = years.map(year => comparisonResults.road.ets_costs[year].cost_eur);

            // Create gradient fills
            const chartCtx = ctx.getContext('2d');

            const seaGradient = chartCtx.createLinearGradient(0, 0, 0, 350);
            seaGradient.addColorStop(0, 'rgba(14, 165, 233, 0.35)');
            seaGradient.addColorStop(0.5, 'rgba(14, 165, 233, 0.1)');
            seaGradient.addColorStop(1, 'rgba(14, 165, 233, 0)');

            const roadGradient = chartCtx.createLinearGradient(0, 0, 0, 350);
            roadGradient.addColorStop(0, 'rgba(249, 115, 22, 0.35)');
            roadGradient.addColorStop(0.5, 'rgba(249, 115, 22, 0.1)');
            roadGradient.addColorStop(1, 'rgba(249, 115, 22, 0)');

            comparisonChart = new Chart(ctx, {{
                type: 'line',
                data: {{
                    labels: years,
                    datasets: [
                        {{
                            label: 'Sea Transport',
                            data: seaCosts,
                            borderColor: '#0ea5e9',
                            backgroundColor: seaGradient,
                            borderWidth: 3,
                            fill: true,
                            tension: 0.4,
                            pointRadius: 6,
                            pointHoverRadius: 10,
                            pointBackgroundColor: '#ffffff',
                            pointBorderColor: '#0ea5e9',
                            pointBorderWidth: 3,
                            pointHoverBackgroundColor: '#0ea5e9',
                            pointHoverBorderColor: '#ffffff',
                            pointHoverBorderWidth: 3
                        }},
                        {{
                            label: 'Road Transport',
                            data: roadCosts,
                            borderColor: '#f97316',
                            backgroundColor: roadGradient,
                            borderWidth: 3,
                            fill: true,
                            tension: 0.4,
                            pointRadius: 6,
                            pointHoverRadius: 10,
                            pointBackgroundColor: '#ffffff',
                            pointBorderColor: '#f97316',
                            pointBorderWidth: 3,
                            pointHoverBackgroundColor: '#f97316',
                            pointHoverBorderColor: '#ffffff',
                            pointHoverBorderWidth: 3
                        }}
                    ]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    interaction: {{
                        mode: 'index',
                        intersect: false
                    }},
                    plugins: {{
                        legend: {{
                            position: 'top',
                            align: 'center',
                            labels: {{
                                usePointStyle: true,
                                pointStyle: 'circle',
                                padding: 25,
                                font: {{
                                    size: 13,
                                    weight: '600',
                                    family: "'Inter', 'Segoe UI', sans-serif"
                                }}
                            }}
                        }},
                        tooltip: {{
                            backgroundColor: 'rgba(15, 23, 42, 0.95)',
                            titleFont: {{
                                size: 14,
                                weight: '600',
                                family: "'Inter', 'Segoe UI', sans-serif"
                            }},
                            bodyFont: {{
                                size: 13,
                                family: "'Inter', 'Segoe UI', sans-serif"
                            }},
                            padding: 16,
                            cornerRadius: 12,
                            displayColors: true,
                            boxPadding: 8,
                            callbacks: {{
                                title: function(context) {{
                                    return 'Year ' + context[0].label;
                                }},
                                label: function(context) {{
                                    const value = context.raw;
                                    return ' ' + context.dataset.label + ': €' + value.toLocaleString(undefined, {{minimumFractionDigits: 2, maximumFractionDigits: 2}});
                                }}
                            }}
                        }}
                    }},
                    scales: {{
                        y: {{
                            beginAtZero: true,
                            border: {{
                                display: false
                            }},
                            grid: {{
                                color: 'rgba(148, 163, 184, 0.12)',
                                drawTicks: false
                            }},
                            ticks: {{
                                padding: 16,
                                font: {{
                                    size: 12,
                                    weight: '500',
                                    family: "'Inter', 'Segoe UI', sans-serif"
                                }},
                                color: '#64748b',
                                callback: function(value) {{
                                    return '€' + value.toLocaleString();
                                }}
                            }}
                        }},
                        x: {{
                            border: {{
                                display: false
                            }},
                            grid: {{
                                display: false
                            }},
                            ticks: {{
                                padding: 12,
                                font: {{
                                    size: 13,
                                    weight: '600',
                                    family: "'Inter', 'Segoe UI', sans-serif"
                                }},
                                color: '#334155'
                            }}
                        }}
                    }},
                    animation: {{
                        duration: 1200,
                        easing: 'easeOutQuart'
                    }}
                }}
            }});
        }}

        // Generate analysis insights
        function generateInsights() {{
            const insightsContainer = document.getElementById('comparison-insights');
            if (!insightsContainer) return;

            const sea = comparisonResults.sea;
            const road = comparisonResults.road;

            let insights = [];

            // CO2 comparison insight
            const co2Diff = sea.emissions.co2_tonnes - road.emissions.co2_tonnes;
            if (co2Diff < 0) {{
                insights.push({{
                    type: 'positive',
                    label: 'CO2',
                    title: 'Sea transport is more environmentally friendly',
                    description: `Sea transport produces ${{Math.abs(co2Diff).toFixed(2)}} tonnes less CO2 than road transport for this route.`
                }});
            }} else if (co2Diff > 0) {{
                insights.push({{
                    type: 'positive',
                    label: 'CO2',
                    title: 'Road transport is more environmentally friendly',
                    description: `Road transport produces ${{Math.abs(co2Diff).toFixed(2)}} tonnes less CO2 than sea transport for this route.`
                }});
            }}

            // Distance comparison
            const distDiff = sea.distance.distance_km - road.distance.distance_km;
            insights.push({{
                type: 'neutral',
                label: 'DIST',
                title: 'Route distance comparison',
                description: `Sea route: ${{sea.distance.distance_km.toFixed(1)}} km | Road route: ${{road.distance.distance_km.toFixed(1)}} km (${{Math.abs(distDiff).toFixed(1)}} km ${{distDiff > 0 ? 'longer by sea' : 'longer by road'}})`
            }});

            // ETS Coverage insight
            insights.push({{
                type: 'neutral',
                label: 'ETS',
                title: 'ETS Coverage',
                description: `Sea: ${{sea.ets_coverage.description}} | Road: ${{road.ets_coverage.description}}`
            }});

            // Cost projection insight (2030)
            const seaCost2030 = sea.ets_costs['2030'] ? sea.ets_costs['2030'].cost_eur : 0;
            const roadCost2030 = road.ets_costs['2030'] ? road.ets_costs['2030'].cost_eur : 0;
            const costDiff = seaCost2030 - roadCost2030;
            const betterOption = costDiff < 0 ? 'Sea' : 'Road';

            insights.push({{
                type: costDiff !== 0 ? 'positive' : 'neutral',
                label: 'COST',
                title: `${{betterOption}} transport is more cost-effective by 2030`,
                description: `Projected 2030 ETS costs: Sea €${{seaCost2030.toLocaleString(undefined, {{minimumFractionDigits: 2}})}} | Road €${{roadCost2030.toLocaleString(undefined, {{minimumFractionDigits: 2}})}} - Savings of €${{Math.abs(costDiff).toLocaleString(undefined, {{minimumFractionDigits: 2}})}} with ${{betterOption.toLowerCase()}} transport.`
            }});

            // Render insights
            insightsContainer.innerHTML = insights.map(insight => `
                <div class="insight-item ${{insight.type}}">
                    <span class="insight-label">${{insight.label}}</span>
                    <div class="insight-text">
                        <div class="insight-title">${{insight.title}}</div>
                        <div class="insight-description">${{insight.description}}</div>
                    </div>
                </div>
            `).join('');
        }}

        // Reset wizard to start new comparison
        function resetWizard() {{
            // Reset form fields
            document.getElementById('wizard-vessel-type').value = '';
            document.getElementById('wizard-vessel-size').value = '';
            document.getElementById('wizard-vessel-size').disabled = true;
            document.getElementById('wizard-sea-fuel').value = '';
            document.getElementById('wizard-sea-fuel').disabled = true;
            document.getElementById('wizard-road-mode').value = '';
            document.getElementById('wizard-road-load-type').value = '';
            document.getElementById('wizard-road-load-type').disabled = true;
            document.getElementById('wizard-road-fuel').value = '';
            document.getElementById('wizard-road-fuel').disabled = true;
            document.getElementById('wizard-cargo-weight').value = '';

            // Clear address fields
            clearWizardAddress('wizard-origin');
            clearWizardAddress('wizard-dest');

            // Reset wizard state
            wizardCurrentStep = 1;
            updateWizardUI();

            // Hide results, show wizard
            document.getElementById('comparison-results').style.display = 'none';
            document.getElementById('comparison-wizard').style.display = 'block';

            // Scroll to wizard
            document.getElementById('comparison-wizard').scrollIntoView({{ behavior: 'smooth' }});
        }}

        // Initialize wizard address search
        function initWizardAddressSearch(prefix) {{
            const input = document.getElementById(`${{prefix}}-address`);
            const suggestions = document.getElementById(`${{prefix}}-suggestions`);
            const spinner = document.getElementById(`${{prefix}}-spinner`);

            if (!input || !suggestions) return;

            let searchTimeout = null;

            input.addEventListener('input', function() {{
                const query = this.value.trim();

                if (searchTimeout) clearTimeout(searchTimeout);

                if (query.length < 2) {{
                    suggestions.style.display = 'none';
                    return;
                }}

                searchTimeout = setTimeout(async () => {{
                    if (spinner) spinner.style.display = 'block';

                    try {{
                        const response = await fetch(`/api/geocode?q=${{encodeURIComponent(query)}}&mode=search`);
                        const data = await response.json();

                        if (data.success && data.data && data.data.length > 0) {{
                            suggestions.innerHTML = data.data.map((result, index) => `
                                <div class="address-suggestion" data-index="${{index}}" data-lat="${{result.coordinates.lat}}" data-lon="${{result.coordinates.lng}}" data-text="${{result.placeName}}">
                                    <strong>${{result.text}}</strong>
                                    <span class="suggestion-context">${{result.context || ''}}</span>
                                </div>
                            `).join('');
                            suggestions.style.display = 'block';

                            // Add click handlers
                            suggestions.querySelectorAll('.address-suggestion').forEach(el => {{
                                el.addEventListener('click', function() {{
                                    selectWizardAddress(prefix, {{
                                        text: this.dataset.text,
                                        coordinates: {{
                                            lat: parseFloat(this.dataset.lat),
                                            lng: parseFloat(this.dataset.lon)
                                        }}
                                    }});
                                }});
                            }});
                        }} else {{
                            suggestions.style.display = 'none';
                        }}
                    }} catch (error) {{
                        console.error('Geocode error:', error);
                    }} finally {{
                        if (spinner) spinner.style.display = 'none';
                    }}
                }}, 300);
            }});

            // Hide suggestions on click outside
            document.addEventListener('click', function(e) {{
                if (!input.contains(e.target) && !suggestions.contains(e.target)) {{
                    suggestions.style.display = 'none';
                }}
            }});
        }}

        // Select wizard address
        function selectWizardAddress(prefix, result) {{
            const addressInput = document.getElementById(`${{prefix}}-address`);
            const latInput = document.getElementById(`${{prefix}}-lat`);
            const lonInput = document.getElementById(`${{prefix}}-lon`);
            const coordsDisplay = document.getElementById(`${{prefix}}-coords`);
            const suggestions = document.getElementById(`${{prefix}}-suggestions`);

            if (addressInput) addressInput.value = result.text;
            if (latInput) latInput.value = result.coordinates.lat;
            if (lonInput) lonInput.value = result.coordinates.lng;
            if (suggestions) suggestions.style.display = 'none';

            if (coordsDisplay) {{
                coordsDisplay.innerHTML = `
                    <div class="location-selected">
                        <svg class="location-selected-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
                            <polyline points="22 4 12 14.01 9 11.01"></polyline>
                        </svg>
                        <div class="location-selected-content">
                            <div class="location-selected-title">Location selected</div>
                            <div class="location-selected-coords">${{result.coordinates.lat.toFixed(6)}}, ${{result.coordinates.lng.toFixed(6)}}</div>
                        </div>
                    </div>
                `;
                coordsDisplay.classList.remove('coordinates-display');
            }}

            updateWizardState();
            updateWizardPreviewMap();
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
    print(f"Starting server on port {PORT}...")
    print(f"Open your browser and go to: http://localhost:{PORT}")
    print("Press Ctrl+C to stop the server")
    print("=" * 60)
    
    try:
        with socketserver.TCPServer(("", PORT), CalculatorHandler) as httpd:
            print(f"Server running at http://0.0.0.0:{PORT}")
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
    except Exception as e:
        print(f"Error starting server: {e}")

if __name__ == "__main__":
    main()
