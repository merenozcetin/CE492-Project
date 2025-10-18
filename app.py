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
class ShipType:
    """Ship type information"""
    name: str
    co2_per_nm: float
    co2eq_per_nm: float

@dataclass
class EmissionResult:
    """Emission calculation result"""
    ship_type: str
    distance_nm: float
    co2_emissions: float
    co2eq_emissions: float

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
        self.ship_types = []  # Initialize empty list first
        self._load_ports()
        self._load_ship_types()
    
    
    def _load_ports(self):
        """Load port database from ports.json"""
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
            print(f"❌ Ports data not found in any of: {possible_paths}")
            return
        
        try:
            with open(ports_file, 'r', encoding='utf-8') as f:
                ports_data = json.load(f)
            
            print(f"✅ Loaded {len(ports_data)} ports from {ports_file}")
            
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
            
        except Exception as e:
            print(f"❌ Error loading ports: {e}")
    
    def _load_ship_types(self):
        """Load ship types from CSV file"""
        ships_file = 'data/registeredships.csv'
        
        if not os.path.exists(ships_file):
            print(f"❌ Ship types data not found: {ships_file}")
            self.ship_types = []
            return
        
        try:
            import csv
            ship_types = []
            
            with open(ships_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    ship_type = ShipType(
                        name=row['Ship Type'],
                        co2_per_nm=float(row[' Avg. CO₂ emissions per distance [kg CO₂ / n mile]']),
                        co2eq_per_nm=float(row['Avg. CO₂eq emissions per distance [kg CO₂eq / n mile]'])
                    )
                    ship_types.append(ship_type)
            
            self.ship_types = ship_types
            print(f"✅ Created {len(self.ship_types)} ship type objects")
            
        except Exception as e:
            print(f"❌ Error loading ship types: {e}")
            self.ship_types = []
    
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
    
    def calculate_emissions(self, ship_type_name: str, distance_nm: float) -> EmissionResult:
        """Calculate CO2 emissions for a given ship type and distance"""
        # Find the ship type
        ship_type = None
        for st in self.ship_types:
            if st.name == ship_type_name:
                ship_type = st
                break
        
        if not ship_type:
            raise Exception(f"Ship type '{ship_type_name}' not found")
        
        # Calculate emissions
        co2_emissions = distance_nm * ship_type.co2_per_nm
        co2eq_emissions = distance_nm * ship_type.co2eq_per_nm
        
        return EmissionResult(
            ship_type=ship_type_name,
            distance_nm=distance_nm,
            co2_emissions=round(co2_emissions, 2),
            co2eq_emissions=round(co2eq_emissions, 2)
        )

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
def get_calculator():
    """Get calculator instance"""
    return SeaRouteCalculator()

calculator = get_calculator()

# Sidebar info
with st.sidebar:
    st.header("ℹ️ About")
    st.info(f"**{len(calculator.ports)} ports** loaded from database")
    st.info(f"**{len(calculator.ship_types)} ship types** loaded from database")
    
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
tab1, tab2, tab3, tab4 = st.tabs(["🚢 Port-to-Port", "📍 Coordinates", "🔍 Port Search", "🌍 EU-ETS Emissions"])

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

with tab4:
    st.header("🌍 EU-ETS Emissions Calculator")
    st.markdown("Calculate CO₂ emissions for maritime routes based on ship type")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Route Selection")
        
        # Origin port selection
        origin_query = st.text_input("Search origin port:", placeholder="e.g., hamburg, rotterdam", key="eu_origin_search")
        
        if origin_query and len(origin_query) >= 2:
            origin_ports = calculator.search_ports(origin_query, 15)
            if origin_ports:
                origin_options = [f"{p.name} ({p.country})" for p in origin_ports]
                origin_options = ["Select origin port..."] + origin_options
                
                origin_choice = st.selectbox("Origin port:", origin_options, key="eu_origin_select")
                
                if origin_choice and origin_choice != "Select origin port...":
                    for port in origin_ports:
                        if f"{port.name} ({port.country})" == origin_choice:
                            eu_origin_port = port
                            break
                else:
                    eu_origin_port = None
            else:
                st.warning(f"No ports found matching '{origin_query}'")
                eu_origin_port = None
        else:
            eu_origin_port = None
    
    with col2:
        st.subheader("Destination Selection")
        
        # Destination port selection
        dest_query = st.text_input("Search destination port:", placeholder="e.g., shanghai, singapore", key="eu_dest_search")
        
        if dest_query and len(dest_query) >= 2:
            dest_ports = calculator.search_ports(dest_query, 15)
            if dest_ports:
                dest_options = [f"{p.name} ({p.country})" for p in dest_ports]
                dest_options = ["Select destination port..."] + dest_options
                
                dest_choice = st.selectbox("Destination port:", dest_options, key="eu_dest_select")
                
                if dest_choice and dest_choice != "Select destination port...":
                    for port in dest_ports:
                        if f"{port.name} ({port.country})" == dest_choice:
                            eu_dest_port = port
                            break
                else:
                    eu_dest_port = None
            else:
                st.warning(f"No ports found matching '{dest_query}'")
                eu_dest_port = None
        else:
            eu_dest_port = None
    
    # Ship type selection
    st.subheader("🚢 Ship Type Selection")
    
    if calculator.ship_types:
        ship_options = [st.name for st in calculator.ship_types]
        ship_options = ["Select ship type..."] + ship_options
        
        selected_ship_type = st.selectbox("Choose ship type:", ship_options, key="ship_type_select")
        
        if selected_ship_type and selected_ship_type != "Select ship type...":
            # Show ship type info
            ship_type = next((st for st in calculator.ship_types if st.name == selected_ship_type), None)
            if ship_type:
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("CO₂ per nm", f"{ship_type.co2_per_nm:.1f} kg")
                with col2:
                    st.metric("CO₂eq per nm", f"{ship_type.co2eq_per_nm:.1f} kg")
        else:
            ship_type = None
    else:
        st.error("No ship types loaded - check if registeredships.csv exists")
        ship_type = None
    
    # Calculate emissions button
    if st.button("🌍 Calculate Emissions", type="primary"):
        if eu_origin_port and eu_dest_port and ship_type:
            with st.spinner("Calculating distance and emissions..."):
                # Calculate distance first
                distance_result = calculator.calculate_distance(
                    eu_origin_port.lon, eu_origin_port.lat, 
                    eu_dest_port.lon, eu_dest_port.lat
                )
                
                if distance_result['success']:
                    # Calculate emissions
                    try:
                        emission_result = calculator.calculate_emissions(
                            selected_ship_type, 
                            distance_result['distance_nm']
                        )
                        
                        st.success("✅ Emissions Calculation Complete!")
                        
                        # Display results
                        st.subheader("📊 Route Information")
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"**Origin:** {eu_origin_port.name} ({eu_origin_port.country})")
                            st.write(f"**Destination:** {eu_dest_port.name} ({eu_dest_port.country})")
                        with col2:
                            st.write(f"**Distance:** {distance_result['distance_nm']} nm ({distance_result['distance_km']} km)")
                            st.write(f"**Ship Type:** {selected_ship_type}")
                        
                        st.subheader("🌍 CO₂ Emissions")
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.metric(
                                label="Total CO₂ Emissions",
                                value=f"{emission_result.co2_emissions:,.0f} kg",
                                help=f"{emission_result.co2_emissions/1000:.1f} tonnes"
                            )
                        
                        with col2:
                            st.metric(
                                label="Total CO₂eq Emissions", 
                                value=f"{emission_result.co2eq_emissions:,.0f} kg",
                                help=f"{emission_result.co2eq_emissions/1000:.1f} tonnes"
                            )
                        
                        with col3:
                            st.metric(
                                label="CO₂ per nm",
                                value=f"{ship_type.co2_per_nm:.1f} kg",
                                help="Emission factor"
                            )
                        
                        # EU-ETS Information
                        st.subheader("🇪🇺 EU-ETS Information")
                        st.info("""
                        **EU-ETS Maritime Coverage:**
                        - Applies to ships of 5,000 GT and above
                        - Covers CO₂ emissions from voyages within EU/EEA
                        - Phase-in period: 2024-2026 (40%, 70%, 100%)
                        - Free allowances: 100% in 2024, reducing to 0% by 2026
                        """)
                        
                    except Exception as e:
                        st.error(f"❌ Emission calculation failed: {e}")
                else:
                    st.error(f"❌ Distance calculation failed: {distance_result['error']}")
        else:
            st.warning("Please select both origin and destination ports, and choose a ship type")

# Footer
st.markdown("---")
st.markdown("**SeaRoute Maritime Distance Calculator** - Powered by Python SeaRoute wrapper")
