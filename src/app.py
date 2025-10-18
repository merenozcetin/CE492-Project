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
class MRVShip:
    """MRV ship data for emissions calculation"""
    imo_number: str
    co2_per_nm: float
    co2eq_per_nm: float

@dataclass
class EmissionResult:
    """Emission calculation result"""
    imo_number: str
    ship_name: str
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
    is_eea: bool = False

class SeaRouteCalculator:
    """Main SeaRoute distance calculator using Python wrapper"""
    
    def __init__(self):
        self.ports = []
        self.mrv_ships = []
        self._load_ports()
        self._load_mrv_data()
    
    def _load_ports(self):
        """Load port database from ports.json"""
        try:
            with open('data/ports.json', 'r', encoding='utf-8') as f:
                ports_data = json.load(f)
            
            for port_data in ports_data:
                port = Port(
                    name=port_data['name'],
                    country=port_data['country'],
                    region=port_data['region'],
                    lon=port_data['lon'],
                    lat=port_data['lat'],
                    alternate=port_data.get('alternate'),
                    is_eea=port_data.get('is_eea', False)
                )
                self.ports.append(port)
            
            print(f"✅ Loaded {len(self.ports)} ports")
            
        except Exception as e:
            print(f"❌ Error loading ports: {e}")
    
    def _load_mrv_data(self):
        """Load MRV ship data from CSV file"""
        try:
            import csv
            import os
            
            # Try multiple possible paths for the MRV data file
            possible_paths = [
                'data/mrv_data.csv',
                './data/mrv_data.csv',
                '../data/mrv_data.csv',
                os.path.join(os.path.dirname(__file__), '..', 'data', 'mrv_data.csv'),
                os.path.join(os.getcwd(), 'data', 'mrv_data.csv')
            ]
            
            mrv_file_path = None
            for path in possible_paths:
                if os.path.exists(path):
                    mrv_file_path = path
                    break
            
            if not mrv_file_path:
                print(f"❌ MRV data file not found. Tried paths: {possible_paths}")
                return
            
            print(f"📁 Loading MRV data from: {mrv_file_path}")
            
            total_rows = 0
            skipped_rows = 0
            loaded_ships = 0
            
            with open(mrv_file_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                
                # Debug: Print column names
                print(f"📋 CSV Columns: {list(reader.fieldnames)}")
                
                # Test first few rows
                first_row = next(reader, None)
                if first_row:
                    print(f"🔍 First row sample: {first_row}")
                    # Reset file pointer to beginning
                    f.seek(0)
                    reader = csv.DictReader(f)
                for row in reader:
                    total_rows += 1
                    
                    try:
                        # Handle "Division by zero!" by setting to 0
                        co2_value = row['CO₂ emissions per distance [kg CO₂ / n mile]']
                        co2eq_value = row['CO₂eq emissions per distance [kg CO₂eq / n mile]']
                        
                        if co2_value == 'Division by zero!':
                            co2_value = '0'
                        if co2eq_value == 'Division by zero!':
                            co2eq_value = '0'
                        
                        ship = MRVShip(
                            imo_number=row['IMO Number'],
                            co2_per_nm=float(co2_value),
                            co2eq_per_nm=float(co2eq_value)
                        )
                        self.mrv_ships.append(ship)
                        loaded_ships += 1
                        
                    except (ValueError, KeyError) as e:
                        # Skip rows with invalid data
                        skipped_rows += 1
                        print(f"⚠️ Skipped row {total_rows}: {e}")
                        print(f"   Row data: {row}")
                        continue
            
            print(f"📊 MRV Loading Summary:")
            print(f"   Total rows processed: {total_rows}")
            print(f"   Ships loaded: {loaded_ships}")
            print(f"   Rows skipped: {skipped_rows}")
            print(f"✅ Loaded {len(self.mrv_ships)} MRV ships")
            
        except Exception as e:
            print(f"❌ Error loading MRV data: {e}")
            import traceback
            traceback.print_exc()
    
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
            
            # Use Python SeaRoute wrapper
            route = sr.searoute(
                origin=[origin_lon, origin_lat],
                destination=[dest_lon, dest_lat]
            )
            
            # Debug: Print the route result to see its structure
            print(f"Route result: {route}")
            print(f"Route type: {type(route)}")
            print(f"Route keys: {route.keys() if isinstance(route, dict) else 'Not a dict'}")
            
            # Extract distance from route result
            # Try different possible keys for distance
            if isinstance(route, dict):
                if 'length' in route:
                    distance_km = route['length'] / 1000  # Convert from meters to km
                elif 'distance' in route:
                    distance_km = route['distance'] / 1000  # Convert from meters to km
                elif 'total_distance' in route:
                    distance_km = route['total_distance'] / 1000  # Convert from meters to km
                else:
                    # If no distance key found, try to calculate from coordinates
                    import math
                    # Simple great circle distance calculation as fallback
                    lat1, lon1 = math.radians(origin_lat), math.radians(origin_lon)
                    lat2, lon2 = math.radians(dest_lat), math.radians(dest_lon)
                    dlat = lat2 - lat1
                    dlon = lon2 - lon1
                    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
                    c = 2 * math.asin(math.sqrt(a))
                    distance_km = 6371 * c  # Earth radius in km
            else:
                raise Exception(f"Unexpected route result type: {type(route)}")
            
            distance_nm = distance_km / 1.852  # Convert km to nautical miles
            
            return {
                'success': True,
                'distance_km': round(distance_km, 1),
                'distance_nm': round(distance_nm, 1),
                'route_name': 'SeaRoute Calculation'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"SeaRoute calculation failed: {str(e)}"
            }
    
    def calculate_emissions(self, imo_number: str, origin_port: Port, dest_port: Port) -> EmissionResult:
        """Calculate CO2 emissions for a specific ship and route"""
        
        # Find the ship by IMO number
        ship = None
        for mrv_ship in self.mrv_ships:
            if mrv_ship.imo_number == imo_number:
                ship = mrv_ship
                break
        
        if not ship:
            raise Exception(f"Ship with IMO number {imo_number} not found in MRV database")
        
        # Calculate distance first
        distance_result = self.calculate_distance(
            origin_port.lon, origin_port.lat,
            dest_port.lon, dest_port.lat
        )
        
        if not distance_result['success']:
            raise Exception(f"Distance calculation failed: {distance_result['error']}")
        
        distance_nm = distance_result['distance_nm']
        
        # Calculate emissions
        co2_emissions = distance_nm * ship.co2_per_nm
        co2eq_emissions = distance_nm * ship.co2eq_per_nm
        
        return EmissionResult(
            imo_number=imo_number,
            ship_name=f"Ship IMO {imo_number}",
            distance_nm=distance_nm,
            co2_emissions=round(co2_emissions, 2),
            co2eq_emissions=round(co2eq_emissions, 2)
        )

# Page configuration
st.set_page_config(
    page_title="SeaRoute Maritime Calculator",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%);
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        text-align: center;
    }
    .main-header h1 {
        color: white;
        margin: 0;
        font-size: 2.5rem;
    }
    .main-header p {
        color: #e8f4fd;
        margin: 0.5rem 0 0 0;
        font-size: 1.1rem;
    }
    .metric-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #2a5298;
    }
    .sidebar-info {
        background: #e8f4fd;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Enhanced Header
st.markdown("""
<div class="main-header">
    <h1>🌊 SeaRoute Maritime Calculator</h1>
    <p>Calculate maritime distances and CO₂ emissions for ships worldwide</p>
</div>
""", unsafe_allow_html=True)

# Initialize calculator
def get_calculator():
    """Get calculator instance"""
    return SeaRouteCalculator()

calculator = get_calculator()

# Enhanced Sidebar
with st.sidebar:
    st.markdown("""
    <div class="sidebar-info">
        <h3>📊 Database Status</h3>
        <p><strong>{ports_count} ports</strong> loaded</p>
        <p><strong>{ships_count} MRV ships</strong> loaded</p>
    </div>
    """.format(
        ports_count=len(calculator.ports),
        ships_count=len(calculator.mrv_ships)
    ), unsafe_allow_html=True)
    
    # Status indicators
    if len(calculator.ports) == 0:
        st.error("❌ No ports loaded!")
        st.write("**Debug Info:**")
        st.write(f"Current directory: {os.getcwd()}")
        st.write(f"Data file exists: {os.path.exists('data/ports.json')}")
        if os.path.exists('data/ports.json'):
            st.write(f"Data file size: {os.path.getsize('data/ports.json')} bytes")
    
    if len(calculator.mrv_ships) == 0:
        st.error("❌ No MRV ships loaded!")
        st.write("**MRV Debug Info:**")
        st.write(f"MRV file exists: {os.path.exists('data/mrv_data.csv')}")
        if os.path.exists('data/mrv_data.csv'):
            st.write(f"MRV file size: {os.path.getsize('data/mrv_data.csv')} bytes")
    else:
        st.success("✅ SeaRoute engine ready")
    
    st.markdown("---")
    
    st.markdown("### 🔧 Features")
    st.markdown("""
    - **🌍 MRV Emissions**: Calculate CO₂ emissions for specific ships
    - **🚢 Port-to-Port**: Calculate maritime distances
    - **🇪🇺 EU-ETS**: EEA port identification
    - **📊 Real-time**: Live calculations
    """)
    
    st.markdown("### 📋 Requirements")
    st.markdown("""
    - Python 3.8+
    - Streamlit
    - searoute package
    """)

# Main tabs - Simplified interface with MRV Emissions first
tab1, tab2 = st.tabs(["🌍 MRV Emissions", "🚢 Port-to-Port"])

with tab1:
    st.header("🌍 MRV Emissions Calculator")
    st.markdown("Calculate CO₂ emissions for specific ships using IMO numbers and MRV data")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Ship Information")
        
        # IMO number input
        imo_number = st.text_input("Enter IMO Number:", placeholder="e.g., 1013676", key="imo_input")
        
        if imo_number:
            # Check if IMO exists in MRV data
            ship_found = False
            ship_data = None
            for ship in calculator.mrv_ships:
                if ship.imo_number == imo_number:
                    ship_found = True
                    ship_data = ship
                    break
            
            if ship_found:
                st.success(f"✅ Ship IMO {imo_number} found in MRV database")
                col1_1, col1_2 = st.columns(2)
                with col1_1:
                    st.metric("CO₂ per nm", f"{ship_data.co2_per_nm:.1f} kg")
                with col1_2:
                    st.metric("CO₂eq per nm", f"{ship_data.co2eq_per_nm:.1f} kg")
            else:
                st.error(f"❌ Ship IMO {imo_number} not found in MRV database")
    
    with col2:
        st.subheader("Route Information")
        
        # Origin port selection
        st.write("**Origin Port**")
        origin_options = [f"{p.name} ({p.country})" for p in calculator.ports]
        origin_options = ["Select origin port..."] + origin_options
        
        origin_choice = st.selectbox("Choose origin port:", origin_options, key="mrv_origin_select")
        
        if origin_choice and origin_choice != "Select origin port...":
            for port in calculator.ports:
                if f"{port.name} ({port.country})" == origin_choice:
                    mrv_origin_port = port
                    break
            else:
                mrv_origin_port = None
        else:
            mrv_origin_port = None
        
        # Destination port selection
        st.write("**Destination Port**")
        dest_options = [f"{p.name} ({p.country})" for p in calculator.ports]
        dest_options = ["Select destination port..."] + dest_options
        
        dest_choice = st.selectbox("Choose destination port:", dest_options, key="mrv_dest_select")
        
        if dest_choice and dest_choice != "Select destination port...":
            for port in calculator.ports:
                if f"{port.name} ({port.country})" == dest_choice:
                    mrv_dest_port = port
                    break
            else:
                mrv_dest_port = None
        else:
            mrv_dest_port = None
    
    # Calculate emissions button
    if st.button("🌍 Calculate MRV Emissions", type="primary"):
        if imo_number and mrv_origin_port and mrv_dest_port:
            try:
                with st.spinner("Calculating emissions..."):
                    emission_result = calculator.calculate_emissions(
                        imo_number, mrv_origin_port, mrv_dest_port
                    )
                    
                    st.success("✅ MRV Emissions Calculation Complete!")
                    
                    # Display results
                    st.subheader("📊 Route Information")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Ship:** IMO {emission_result.imo_number}")
                        st.write(f"**Origin:** {mrv_origin_port.name} ({mrv_origin_port.country})")
                    with col2:
                        st.write(f"**Destination:** {mrv_dest_port.name} ({mrv_dest_port.country})")
                        st.write(f"**Distance:** {emission_result.distance_nm} nm")
                    
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
                            label="Distance",
                            value=f"{emission_result.distance_nm} nm",
                            help="Maritime distance"
                        )
                    
                    # EU-ETS Information
                    st.subheader("🇪🇺 EU-ETS Information")
                    
                    # Check if route involves EEA ports
                    origin_eea = mrv_origin_port.is_eea
                    dest_eea = mrv_dest_port.is_eea
                    
                    if origin_eea and dest_eea:
                        st.info("**EEA-to-EEA Route**: This route is fully covered by EU-ETS")
                    elif origin_eea or dest_eea:
                        st.warning("**Mixed Route**: This route involves both EEA and non-EEA ports")
                    else:
                        st.info("**Non-EEA Route**: This route is not covered by EU-ETS")
                    
                    st.info("""
                    **EU-ETS Maritime Coverage:**
                    - Applies to ships of 5,000 GT and above
                    - Covers CO₂ emissions from voyages within EU/EEA
                    - Phase-in period: 2024-2026 (40%, 70%, 100%)
                    - Free allowances: 100% in 2024, reducing to 0% by 2026
                    """)
                    
            except Exception as e:
                st.error(f"❌ Calculation failed: {e}")
        else:
            st.warning("Please enter IMO number and select both origin and destination ports")

with tab2:
    st.header("🚢 Port-to-Port Distance Calculation")
    st.markdown("Calculate maritime distances between ports worldwide")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Origin Port")
        
        # Origin port selection - direct dropdown with all ports
        origin_options = [f"{p.name} ({p.country})" for p in calculator.ports]
        origin_options = ["Select origin port..."] + origin_options
        
        origin_choice = st.selectbox("Choose origin port:", origin_options, key="origin_select")
        
        if origin_choice and origin_choice != "Select origin port...":
            for port in calculator.ports:
                if f"{port.name} ({port.country})" == origin_choice:
                    origin_port = port
                    break
            else:
                origin_port = None
        else:
            origin_port = None
        
        if origin_port:
            st.success(f"✅ **{origin_port.name}** ({origin_port.country})")
            st.info(f"📍 Coordinates: {origin_port.lat:.2f}°N, {origin_port.lon:.2f}°E")
    
    with col2:
        st.subheader("Destination Port")
        
        # Destination port selection - direct dropdown with all ports
        dest_options = [f"{p.name} ({p.country})" for p in calculator.ports]
        dest_options = ["Select destination port..."] + dest_options
        
        dest_choice = st.selectbox("Choose destination port:", dest_options, key="dest_select")
        
        if dest_choice and dest_choice != "Select destination port...":
            for port in calculator.ports:
                if f"{port.name} ({port.country})" == dest_choice:
                    dest_port = port
                    break
            else:
                dest_port = None
        else:
            dest_port = None
        
        if dest_port:
            st.success(f"✅ **{dest_port.name}** ({dest_port.country})")
            st.info(f"📍 Coordinates: {dest_port.lat:.2f}°N, {dest_port.lon:.2f}°E")
    
    # Calculate distance button
    if st.button("🌊 Calculate Distance", type="primary"):
        if origin_port and dest_port:
            with st.spinner("Calculating maritime distance..."):
                distance_result = calculator.calculate_distance(
                    origin_port.lon, origin_port.lat, 
                    dest_port.lon, dest_port.lat
                )
                
                if distance_result['success']:
                    st.success("✅ Distance Calculation Complete!")
                    
                    # Display results
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric(
                            label="Distance (Nautical Miles)",
                            value=f"{distance_result['distance_nm']} nm"
                        )
                    
                    with col2:
                        st.metric(
                            label="Distance (Kilometers)", 
                            value=f"{distance_result['distance_km']} km"
                        )
                    
                    with col3:
                        st.metric(
                            label="Route Type",
                            value=distance_result['route_name']
                        )
                    
                    # Additional info
                    st.subheader("📍 Route Details")
                    st.write(f"**From:** {origin_port.name} ({origin_port.country})")
                    st.write(f"**To:** {dest_port.name} ({dest_port.country})")
                    st.write(f"**Distance:** {distance_result['distance_nm']} nautical miles ({distance_result['distance_km']} km)")
                    
                else:
                    st.error(f"❌ Calculation failed: {distance_result['error']}")
        else:
            st.warning("Please select both origin and destination ports")

# Footer
st.markdown("---")
st.markdown("**SeaRoute Maritime Distance Calculator** - Powered by Python SeaRoute wrapper")