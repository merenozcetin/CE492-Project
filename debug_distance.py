#!/usr/bin/env python3
"""
Debug script to investigate distance calculation issues
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'tools'))

from java_searoute_wrapper import JavaSeaRouteWrapper
import math

def calculate_great_circle_distance(lat1, lon1, lat2, lon2):
    """Calculate great circle distance between two points"""
    # Convert to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    # Earth radius in kilometers
    earth_radius = 6371
    distance_km = earth_radius * c
    distance_nm = distance_km / 1.852
    
    return distance_km, distance_nm

def test_distance_calculations():
    """Test distance calculations with known routes"""
    
    print("🔍 Debugging Distance Calculations")
    print("=" * 60)
    
    # Test routes with known distances
    test_routes = [
        {
            'name': 'Hamburg to Shanghai',
            'origin_lon': 9.9937, 'origin_lat': 53.5511,
            'dest_lon': 121.8, 'dest_lat': 31.2,
            'expected_nm': 10400,  # Approximate expected distance
            'tolerance': 1000
        },
        {
            'name': 'Rotterdam to Singapore',
            'origin_lon': 4.4777, 'origin_lat': 51.9244,
            'dest_lon': 103.8198, 'dest_lat': 1.2966,
            'expected_nm': 8500,  # Approximate expected distance
            'tolerance': 1000
        },
        {
            'name': 'New York to Los Angeles',
            'origin_lon': -74.1, 'origin_lat': 40.7,
            'dest_lon': -118.3, 'dest_lat': 33.7,
            'expected_nm': 2400,  # Approximate expected distance
            'tolerance': 500
        }
    ]
    
    # Initialize Java SeaRoute wrapper
    try:
        print("🚀 Initializing Java SeaRoute...")
        java_wrapper = JavaSeaRouteWrapper()
        print("✅ Java SeaRoute initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize Java SeaRoute: {e}")
        return
    
    for route in test_routes:
        print(f"\n📍 Testing: {route['name']}")
        print("-" * 40)
        
        # Calculate great circle distance
        gc_km, gc_nm = calculate_great_circle_distance(
            route['origin_lat'], route['origin_lon'],
            route['dest_lat'], route['dest_lon']
        )
        
        print(f"Great Circle Distance: {gc_nm:.1f} nm ({gc_km:.1f} km)")
        
        # Calculate Java SeaRoute distance
        try:
            java_result = java_wrapper.calculate_distance(
                route['origin_lon'], route['origin_lat'],
                route['dest_lon'], route['dest_lat']
            )
            
            if java_result['success']:
                java_nm = java_result['distance_nm']
                java_km = java_result['distance_km']
                complexity = java_result.get('route_complexity', 0)
                
                print(f"Java SeaRoute Distance: {java_nm:.1f} nm ({java_km:.1f} km)")
                print(f"Route Complexity: {complexity} waypoints")
                
                # Compare with expected
                diff_nm = java_nm - route['expected_nm']
                diff_pct = (diff_nm / route['expected_nm']) * 100
                
                print(f"Expected Distance: ~{route['expected_nm']} nm")
                print(f"Difference: {diff_nm:+.1f} nm ({diff_pct:+.1f}%)")
                
                if abs(diff_nm) <= route['tolerance']:
                    print("✅ Distance is within expected range")
                else:
                    print("⚠️ Distance is outside expected range")
                
                # Check if Java result is reasonable
                if java_nm < gc_nm * 0.8:
                    print("🚨 WARNING: Java SeaRoute distance is suspiciously short!")
                elif java_nm > gc_nm * 3:
                    print("🚨 WARNING: Java SeaRoute distance is suspiciously long!")
                else:
                    print("✅ Java SeaRoute distance seems reasonable")
                    
            else:
                print(f"❌ Java SeaRoute failed: {java_result['error']}")
                
        except Exception as e:
            print(f"❌ Java SeaRoute error: {e}")
        
        print()
    
    # Test with some debug output
    print("🔧 Debugging Java SeaRoute Input/Output...")
    print("-" * 40)
    
    try:
        # Test with Hamburg to Shanghai
        result = java_wrapper.calculate_distance(9.9937, 53.5511, 121.8, 31.2)
        
        if result['success']:
            print("✅ Java SeaRoute calculation successful")
            print(f"Distance: {result['distance_nm']} nm")
            print(f"Properties: {result.get('properties', {})}")
            
            # Check if coordinates are being processed correctly
            coordinates = result.get('coordinates', [])
            if coordinates:
                print(f"Route has {len(coordinates)} line segments")
                total_points = sum(len(line) for line in coordinates)
                print(f"Total waypoints: {total_points}")
            else:
                print("⚠️ No coordinates found in result")
        else:
            print(f"❌ Java SeaRoute failed: {result['error']}")
            
    except Exception as e:
        print(f"❌ Debug test failed: {e}")
    
    # Cleanup
    java_wrapper.cleanup()
    print("\n🏁 Debug test completed!")

if __name__ == "__main__":
    test_distance_calculations()
