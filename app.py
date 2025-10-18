#!/usr/bin/env python3
"""
SeaRoute Maritime Distance Calculator - Streamlit App
Clean web application for calculating maritime distances between ports worldwide.
Uses the lightweight Python SeaRoute wrapper.

Usage:
    streamlit run app.py
"""

import streamlit as st
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
    
    @st.cache_data(ttl=3600)  # Cache for 1 hour
    def _load_ports_data():
        """Load port data from JSON file with caching"""
        # Try multiple possible locations for the ports file
        possible_paths = [
            'data/ports.json',
            './data/ports.json',
            '../data/ports.json',
            'ports.json'
        ]
        
        ports_file = None
        for path in possible_paths:
            if os.path.exists(path):
                ports_file = path
                break
        
        if not ports_file:
            print(f"❌ Port data not found in any of these locations: {possible_paths}")
            return []
        
        try:
            with open(ports_file, 'r', encoding='utf-8') as f:
                ports_data = json.load(f)
            
            print(f"✅ Loaded {len(ports_data)} ports from {ports_file}")
            return ports_data
            
        except Exception as e:
            print(f"❌ Error loading ports: {e}")
            return []
    
    def _load_ports(self):
        """Load port database from ports.json"""
        ports_data = self._load_ports_data()
        
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
        
        print(f"✅ Created {len(self.ports)} port objects")
    
    def search_ports(self, query: str, limit: int = 10) -> List[Port]:
        """Search ports by name, country, or region"""
        if not query or len(query) < 2:
            return []
            
        query = query.lower()
        matches = []
        
        for port in self.ports:
            if (query in port.name.lower() or 
                query in port.country.lower() or 
                query in port.region.lower() or
                (port.alternate and query in port.alternate.lower())):
                matches.append(port)
        
        return matches[:limit]
    
    @st.cache_data(ttl=3600)  # Cache for 1 hour
    def calculate_distance(_self, origin_lon: float, origin_lat: float, 
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

# Page configuration
st.set_page_config(
    page_title="SeaRoute Maritime Distance Calculator",
    page_icon="🌊",
    layout="wide"
)

# Header
st.title("🌊 SeaRoute Maritime Distance Calculator")
st.markdown("Calculate maritime distances between ports worldwide using the Python SeaRoute wrapper")

# Initialize calculator
@st.cache_resource
def get_calculator():
    """Get cached calculator instance"""
    return SeaRouteCalculator()

calculator = get_calculator()

# Sidebar info
with st.sidebar:
    st.header("ℹ️ About")
    st.info(f"**{len(calculator.ports)} ports** loaded from database")
    
    # Debug info
    if len(calculator.ports) == 0:
        st.error("❌ No ports loaded!")
        st.write("**Debug Info:**")
        st.write(f"Current directory: {os.getcwd()}")
        st.write(f"Data file exists: {os.path.exists('data/ports.json')}")
        if os.path.exists('data/ports.json'):
            st.write(f"Data file size: {os.path.getsize('data/ports.json')} bytes")
    else:
        st.success("✅ SeaRoute engine ready")
    
    st.header("🔧 Requirements")
    st.markdown("""
    - Python 3.8+
    - Streamlit
    - searoute package
    """)

# Main tabs
tab1, tab2, tab3 = st.tabs(["🚢 Port-to-Port", "📍 Coordinates", "🔍 Port Search"])

with tab1:
    st.header("Port-to-Port Distance Calculation")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Origin Port")
        
        # Dynamic search with selectbox for true autocomplete
        origin_query = st.text_input("Search origin port:", placeholder="e.g., hamburg, rotterdam", key="origin_search")
        
        if origin_query and len(origin_query) >= 2:
            origin_ports = calculator.search_ports(origin_query, 15)
            if origin_ports:
                # Create options list for selectbox
                origin_options = [f"{p.name} ({p.country})" for p in origin_ports]
                
                # Add "Select a port..." as first option
                origin_options = ["Select a port..."] + origin_options
                
                # Use selectbox for autocomplete-like behavior
                origin_choice = st.selectbox(
                    f"Found {len(origin_ports)} ports:", 
                    origin_options, 
                    key="origin_select"
                )
                
                if origin_choice and origin_choice != "Select a port...":
                    # Find the selected port
                    selected_port = None
                    for port in origin_ports:
                        if f"{port.name} ({port.country})" == origin_choice:
                            selected_port = port
                            break
                    
                    if selected_port:
                        st.success(f"✅ **Selected:** {selected_port.name} ({selected_port.country})")
                        st.info(f"📍 Coordinates: {selected_port.lon}°E, {selected_port.lat}°N")
                        origin_port = selected_port
                    else:
                        origin_port = None
                else:
                    origin_port = None
            else:
                st.warning(f"❌ No ports found matching '{origin_query}'")
                origin_port = None
        else:
            origin_port = None
    
    with col2:
        st.subheader("Destination Port")
        
        # Dynamic search with selectbox for true autocomplete
        dest_query = st.text_input("Search destination port:", placeholder="e.g., shanghai, singapore", key="dest_search")
        
        if dest_query and len(dest_query) >= 2:
            dest_ports = calculator.search_ports(dest_query, 15)
            if dest_ports:
                # Create options list for selectbox
                dest_options = [f"{p.name} ({p.country})" for p in dest_ports]
                
                # Add "Select a port..." as first option
                dest_options = ["Select a port..."] + dest_options
                
                # Use selectbox for autocomplete-like behavior
                dest_choice = st.selectbox(
                    f"Found {len(dest_ports)} ports:", 
                    dest_options, 
                    key="dest_select"
                )
                
                if dest_choice and dest_choice != "Select a port...":
                    # Find the selected port
                    selected_port = None
                    for port in dest_ports:
                        if f"{port.name} ({port.country})" == dest_choice:
                            selected_port = port
                            break
                    
                    if selected_port:
                        st.success(f"✅ **Selected:** {selected_port.name} ({selected_port.country})")
                        st.info(f"📍 Coordinates: {selected_port.lon}°E, {selected_port.lat}°N")
                        dest_port = selected_port
                    else:
                        dest_port = None
                else:
                    dest_port = None
            else:
                st.warning(f"❌ No ports found matching '{dest_query}'")
                dest_port = None
        else:
            dest_port = None
    
    # Clear selections button
    if st.button("🗑️ Clear Selections"):
        if 'origin_selected' in st.session_state:
            del st.session_state.origin_selected
        if 'dest_selected' in st.session_state:
            del st.session_state.dest_selected
        st.rerun()
    
    # Calculate button
    if st.button("🚀 Calculate Distance", type="primary"):
        if origin_port and dest_port:
            with st.spinner("Calculating maritime distance..."):
                result = calculator.calculate_distance(
                    origin_port.lon, origin_port.lat, 
                    dest_port.lon, dest_port.lat
                )
                
                if result['success']:
                    st.success("✅ Calculation Complete!")
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric(
                            label="🌊 Maritime Distance",
                            value=f"{result['distance_nm']} nm",
                            help=f"{result['distance_km']} km"
                        )
                    
                    with col2:
                        st.metric(
                            label="📍 Distance (km)",
                            value=f"{result['distance_km']} km"
                        )
                    
                    with col3:
                        st.metric(
                            label="📍 Distance (nm)",
                            value=f"{result['distance_nm']} nm"
                        )
                    
                    st.info(f"🏷️ Route Name: {result['route_name']}")
                    
                else:
                    st.error(f"❌ Calculation failed: {result['error']}")
        else:
            st.warning("Please select both origin and destination ports")

with tab2:
    st.header("Coordinate-based Distance Calculation")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Origin Coordinates")
        origin_lon = st.number_input("Origin Longitude:", value=0.0, format="%.2f", key="origin_lon")
        origin_lat = st.number_input("Origin Latitude:", value=0.0, format="%.2f", key="origin_lat")
    
    with col2:
        st.subheader("Destination Coordinates")
        dest_lon = st.number_input("Destination Longitude:", value=0.0, format="%.2f", key="dest_lon")
        dest_lat = st.number_input("Destination Latitude:", value=0.0, format="%.2f", key="dest_lat")
    
    if st.button("🚀 Calculate Distance from Coordinates", type="primary"):
        with st.spinner("Calculating maritime distance..."):
            result = calculator.calculate_distance(origin_lon, origin_lat, dest_lon, dest_lat)
            
            if result['success']:
                st.success("✅ Calculation Complete!")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric(
                        label="🌊 Maritime Distance",
                        value=f"{result['distance_nm']} nm",
                        help=f"{result['distance_km']} km"
                    )
                
                with col2:
                    st.metric(
                        label="📍 Distance (km)",
                        value=f"{result['distance_km']} km"
                    )
                
                with col3:
                    st.metric(
                        label="📍 Distance (nm)",
                        value=f"{result['distance_nm']} nm"
                    )
                
                st.info(f"🏷️ Route Name: {result['route_name']}")
                
            else:
                st.error(f"❌ Calculation failed: {result['error']}")

with tab3:
    st.header("Port Search")
    
    search_query = st.text_input("Search ports:", placeholder="Search by name, country, or region (e.g., hamburg, germany, container)")
    
    if search_query:
        ports = calculator.search_ports(search_query, 20)
        
        if ports:
            st.success(f"Found {len(ports)} ports matching '{search_query}'")
            
            # Display ports in a table
            port_data = []
            for port in ports:
                port_data.append({
                    "Name": port.name,
                    "Country": port.country,
                    "Region": port.region,
                    "Longitude": f"{port.lon}°E",
                    "Latitude": f"{port.lat}°N",
                    "Alternate": port.alternate or ""
                })
            
            st.dataframe(port_data, use_container_width=True)
        else:
            st.warning(f"No ports found matching '{search_query}'")

# Footer
st.markdown("---")
st.markdown("**SeaRoute Maritime Distance Calculator** - Powered by Python SeaRoute wrapper")
