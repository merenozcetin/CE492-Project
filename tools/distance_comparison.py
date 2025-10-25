#!/usr/bin/env python3
"""
Distance Comparison: Java SeaRoute vs Python SeaRoute Wrapper
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

import searoute as sr
from java_searoute_wrapper import JavaSeaRouteWrapper
import math

def calculate_great_circle_distance(lat1, lon1, lat2, lon2):
    """Calculate great circle distance (Python wrapper method)"""
    lat1, lon1 = math.radians(lat1), math.radians(lon1)
    lat2, lon2 = math.radians(lat2), math.radians(lon2)
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    distance_km = 6371 * c  # Earth radius in km
    distance_nm = distance_km / 1.852
    return distance_km, distance_nm

def compare_distances():
    """Compare distances between Java SeaRoute and Python wrapper"""
    print("Distance Comparison: Java SeaRoute vs Python Wrapper")
    print("=" * 60)
    
    # Test routes
    routes = [
        {
            'name': 'Hamburg to Shanghai',
            'origin_lon': 9.9937, 'origin_lat': 53.5511,
            'dest_lon': 121.8, 'dest_lat': 31.2
        },
        {
            'name': 'Marseille to Shanghai', 
            'origin_lon': 5.3, 'origin_lat': 43.3,
            'dest_lon': 121.8, 'dest_lat': 31.2
        },
        {
            'name': 'New York to Los Angeles',
            'origin_lon': -74.1, 'origin_lat': 40.7,
            'dest_lon': -118.3, 'dest_lat': 33.7
        },
        {
            'name': 'Rotterdam to Singapore',
            'origin_lon': 4.4777, 'origin_lat': 51.9244,
            'dest_lon': 103.8198, 'dest_lat': 1.2966
        }
    ]
    
    java_wrapper = JavaSeaRouteWrapper()
    
    for route in routes:
        print(f"\nRoute: {route['name']}")
        print("-" * 40)
        
        # Java SeaRoute (Actual Shipping Routes)
        java_result = java_wrapper.calculate_distance(
            route['origin_lon'], route['origin_lat'],
            route['dest_lon'], route['dest_lat']
        )
        
        if java_result['success']:
            java_distance_nm = java_result['distance_nm']
            java_distance_km = java_result['distance_km']
            java_waypoints = java_result['route_complexity']
        else:
            print(f"Java SeaRoute Error: {java_result['error']}")
            continue
        
        # Python SeaRoute Wrapper (Great Circle)
        try:
            python_route = sr.searoute(
                origin=[route['origin_lon'], route['origin_lat']],
                destination=[route['dest_lon'], route['dest_lat']]
            )
            
            if isinstance(python_route, dict) and 'length' in python_route:
                python_distance_km = python_route['length'] / 1000
                python_distance_nm = python_distance_km / 1.852
            else:
                # Fallback to great circle calculation
                python_distance_km, python_distance_nm = calculate_great_circle_distance(
                    route['origin_lat'], route['origin_lon'],
                    route['dest_lat'], route['dest_lon']
                )
        except Exception as e:
            # Fallback to great circle calculation
            python_distance_km, python_distance_nm = calculate_great_circle_distance(
                route['origin_lat'], route['origin_lon'],
                route['dest_lat'], route['dest_lon']
            )
        
        # Calculate differences
        difference_nm = java_distance_nm - python_distance_nm
        difference_km = java_distance_km - python_distance_km
        percentage_diff = (difference_nm / python_distance_nm) * 100
        
        # Display results
        print(f"Java SeaRoute (Actual Routes):")
        print(f"  Distance: {java_distance_nm:.1f} nm ({java_distance_km:.1f} km)")
        print(f"  Waypoints: {java_waypoints}")
        print(f"  Method: Actual shipping routes with maritime network")
        
        print(f"\nPython Wrapper (Great Circle):")
        print(f"  Distance: {python_distance_nm:.1f} nm ({python_distance_km:.1f} km)")
        print(f"  Method: Straight-line great circle distance")
        
        print(f"\nDifference:")
        print(f"  Distance: {difference_nm:+.1f} nm ({difference_km:+.1f} km)")
        print(f"  Percentage: {percentage_diff:+.1f}%")
        
        if percentage_diff > 0:
            print(f"  Analysis: Java SeaRoute is {percentage_diff:.1f}% longer (more realistic)")
        else:
            print(f"  Analysis: Java SeaRoute is {abs(percentage_diff):.1f}% shorter")
    
    java_wrapper.cleanup()
    print("\n" + "=" * 60)
    print("Comparison completed!")

if __name__ == "__main__":
    compare_distances()
