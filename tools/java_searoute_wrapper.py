#!/usr/bin/env python3
"""
Java SeaRoute Wrapper for Python
Provides accurate maritime distance calculations using the Java SeaRoute implementation
"""

import subprocess
import json
import tempfile
import os
from typing import Dict, List, Optional
import pandas as pd

class JavaSeaRouteWrapper:
    """Wrapper for Java SeaRoute implementation"""
    
    def __init__(self, searoute_jar_path: str = "java-searoute/searoute.jar"):
        """
        Initialize the Java SeaRoute wrapper
        
        Args:
            searoute_jar_path: Path to the SeaRoute JAR file
        """
        self.searoute_jar_path = searoute_jar_path
        self.temp_dir = tempfile.mkdtemp()
        
        # Verify JAR file exists
        if not os.path.exists(self.searoute_jar_path):
            raise FileNotFoundError(f"SeaRoute JAR file not found at: {self.searoute_jar_path}")
    
    def calculate_distance(self, origin_lon: float, origin_lat: float, 
                          dest_lon: float, dest_lat: float) -> Dict:
        """
        Calculate maritime distance using Java SeaRoute
        
        Args:
            origin_lon: Origin longitude
            origin_lat: Origin latitude  
            dest_lon: Destination longitude
            dest_lat: Destination latitude
            
        Returns:
            Dictionary with distance results and route information
        """
        try:
            # Create temporary CSV input file
            input_file = os.path.join(self.temp_dir, "input.csv")
            output_file = os.path.join(self.temp_dir, "output.geojson")
            
            # Prepare input data
            input_data = {
                'route name': ['Single Route'],
                'olon': [origin_lon],
                'olat': [origin_lat], 
                'dlon': [dest_lon],
                'dlat': [dest_lat]
            }
            
            # Write CSV file
            df = pd.DataFrame(input_data)
            df.to_csv(input_file, index=False)
            
            # Run Java SeaRoute
            cmd = [
                'java', '-jar', self.searoute_jar_path,
                '-i', input_file,
                '-o', output_file,
                '-res', '20'  # 20km resolution
            ]
            
            # Execute command
            print(f"Running Java command: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            print(f"Java return code: {result.returncode}")
            print(f"Java stdout: {result.stdout}")
            print(f"Java stderr: {result.stderr}")
            
            if result.returncode != 0:
                raise Exception(f"Java SeaRoute failed: {result.stderr}")
            
            # Read output GeoJSON
            if not os.path.exists(output_file):
                raise Exception("Output file was not created")
            
            with open(output_file, 'r', encoding='utf-8') as f:
                geojson_data = json.load(f)
            
            # Extract route information
            if not geojson_data.get('features'):
                raise Exception("No route features found in output")
            
            feature = geojson_data['features'][0]
            properties = feature['properties']
            
            # Extract distance information
            distance_km = float(properties.get('distKM', 0))
            distance_nm = distance_km / 1.852  # Convert km to nautical miles
            
            # Extract route geometry for analysis
            geometry = feature.get('geometry', {})
            coordinates = geometry.get('coordinates', [])
            
            # Calculate route complexity (number of waypoints)
            route_complexity = 0
            if coordinates:
                for line_string in coordinates:
                    route_complexity += len(line_string)
            
            return {
                'success': True,
                'distance_km': round(distance_km, 1),
                'distance_nm': round(distance_nm, 1),
                'route_name': 'Maritime Route (Java SeaRoute)',
                'route_complexity': route_complexity,
                'coordinates': coordinates,
                'properties': properties,
                'method': 'Java SeaRoute (Actual Shipping Routes)'
            }
            
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': 'Java SeaRoute calculation timed out',
                'distance_km': 0,
                'distance_nm': 0,
                'route_name': 'Error',
                'method': 'Java SeaRoute (Timeout)'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'distance_km': 0,
                'distance_nm': 0,
                'route_name': 'Error',
                'method': 'Java SeaRoute (Error)'
            }
    
    def calculate_multiple_routes(self, routes: List[Dict]) -> List[Dict]:
        """
        Calculate multiple routes in batch
        
        Args:
            routes: List of route dictionaries with origin_lon, origin_lat, dest_lon, dest_lat
            
        Returns:
            List of route results
        """
        try:
            # Create temporary CSV input file
            input_file = os.path.join(self.temp_dir, "batch_input.csv")
            output_file = os.path.join(self.temp_dir, "batch_output.geojson")
            
            # Prepare batch input data
            input_data = {
                'route name': [f"Route_{i+1}" for i in range(len(routes))],
                'olon': [route['origin_lon'] for route in routes],
                'olat': [route['origin_lat'] for route in routes],
                'dlon': [route['dest_lon'] for route in routes],
                'dlat': [route['dest_lat'] for route in routes]
            }
            
            # Write CSV file
            df = pd.DataFrame(input_data)
            df.to_csv(input_file, index=False)
            
            # Run Java SeaRoute
            cmd = [
                'java', '-jar', self.searoute_jar_path,
                '-i', input_file,
                '-o', output_file,
                '-res', '20'  # 20km resolution
            ]
            
            # Execute command
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            
            if result.returncode != 0:
                raise Exception(f"Java SeaRoute batch failed: {result.stderr}")
            
            # Read output GeoJSON
            if not os.path.exists(output_file):
                raise Exception("Batch output file was not created")
            
            with open(output_file, 'r', encoding='utf-8') as f:
                geojson_data = json.load(f)
            
            # Process results
            results = []
            features = geojson_data.get('features', [])
            
            for i, feature in enumerate(features):
                properties = feature['properties']
                distance_km = float(properties.get('distKM', 0))
                distance_nm = distance_km / 1.852
                
                results.append({
                    'success': True,
                    'distance_km': round(distance_km, 1),
                    'distance_nm': round(distance_nm, 1),
                    'route_name': f"Route_{i+1}",
                    'properties': properties,
                    'method': 'Java SeaRoute (Batch)'
                })
            
            return results
            
        except Exception as e:
            # Return error results for all routes
            return [{
                'success': False,
                'error': str(e),
                'distance_km': 0,
                'distance_nm': 0,
                'route_name': f"Route_{i+1}",
                'method': 'Java SeaRoute (Batch Error)'
            } for i in range(len(routes))]
    
    def cleanup(self):
        """Clean up temporary files"""
        try:
            import shutil
            shutil.rmtree(self.temp_dir)
        except Exception:
            pass  # Ignore cleanup errors
    
    def __del__(self):
        """Destructor to clean up temporary files"""
        self.cleanup()

# Test function
def test_java_searoute():
    """Test the Java SeaRoute wrapper"""
    print("Testing Java SeaRoute Wrapper...")
    
    try:
        wrapper = JavaSeaRouteWrapper()
        
        # Test single route: Hamburg to Shanghai
        print("\nTesting Hamburg -> Shanghai")
        result = wrapper.calculate_distance(9.9937, 53.5511, 121.8, 31.2)
        
        if result['success']:
            print(f"SUCCESS Distance: {result['distance_nm']} nm ({result['distance_km']} km)")
            print(f"SUCCESS Route complexity: {result['route_complexity']} waypoints")
            print(f"SUCCESS Method: {result['method']}")
        else:
            print(f"ERROR: {result['error']}")
        
        # Test batch routes
        print("\nTesting batch routes...")
        routes = [
            {'origin_lon': 5.3, 'origin_lat': 43.3, 'dest_lon': 121.8, 'dest_lat': 31.2},  # Marseille-Shanghai
            {'origin_lon': -74.1, 'origin_lat': 40.7, 'dest_lon': -118.3, 'dest_lat': 33.7}  # New York-Los Angeles
        ]
        
        batch_results = wrapper.calculate_multiple_routes(routes)
        
        for i, result in enumerate(batch_results):
            if result['success']:
                print(f"SUCCESS Route {i+1}: {result['distance_nm']} nm ({result['distance_km']} km)")
            else:
                print(f"ERROR Route {i+1}: {result['error']}")
        
        wrapper.cleanup()
        print("\nJava SeaRoute wrapper test completed!")
        
    except Exception as e:
        print(f"Test failed: {e}")

if __name__ == "__main__":
    test_java_searoute()
