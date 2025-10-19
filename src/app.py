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
class ETSPrices:
    """ETS price data for different years"""
    year: int
    price_eur: float

@dataclass
class EmissionResult:
    """Emission calculation result"""
    imo_number: str
    ship_name: str
    distance_nm: float
    co2_emissions: float
    co2eq_emissions: float
    ets_costs: Dict[int, float] = None  # Year -> cost in EUR

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
        self.ets_prices = []
        self._load_ports()
        self._load_mrv_data()
        self._load_ets_prices()
    
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
    
    def _load_ets_prices(self):
        """Load ETS price data from CSV file"""
        try:
            import csv
            import os
            
            # Try multiple possible paths for the ETS price file
            possible_paths = [
                'data/ets_price.csv',
                './data/ets_price.csv',
                '../data/ets_price.csv',
                os.path.join(os.path.dirname(__file__), '..', 'data', 'ets_price.csv'),
                os.path.join(os.getcwd(), 'data', 'ets_price.csv')
            ]
            
            ets_file_path = None
            for path in possible_paths:
                if os.path.exists(path):
                    ets_file_path = path
                    break
            
            if not ets_file_path:
                print(f"❌ ETS price file not found. Tried paths: {possible_paths}")
                return
            
            print(f"📁 Loading ETS prices from: {ets_file_path}")
            
            with open(ets_file_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    if row['year'] and row['average_eua_price_eur']:  # Skip empty rows
                        ets_price = ETSPrices(
                            year=int(row['year']),
                            price_eur=float(row['average_eua_price_eur'])
                        )
                        self.ets_prices.append(ets_price)
            
            print(f"✅ Loaded {len(self.ets_prices)} ETS price entries")
            
        except Exception as e:
            print(f"❌ Error loading ETS prices: {e}")
            import traceback
            traceback.print_exc()
    
    def search_ports(self, query: str, limit: int = 10) -> List[Port]:
        """Search ports by name, country, or region with enhanced country code support"""
        if not query or len(query) < 2:
            return []
            
        query = query.strip().lower()
        matches = []
        
        for port in self.ports:
            # Convert country to string and handle None values
            country_str = str(port.country) if port.country is not None else ""
            
            # Exact country code match (case insensitive)
            if query.upper() == country_str.upper():
                matches.append(port)
            # Port name match
            elif query in port.name.lower():
                matches.append(port)
            # Country name match (if we had country names)
            elif query in country_str.lower():
                matches.append(port)
            # Region match
            elif query in port.region.lower():
                matches.append(port)
            # Alternate name match
            elif port.alternate and query in port.alternate.lower():
                matches.append(port)
        
        # Sort matches: exact country code matches first, then others
        def sort_key(port):
            country_str = str(port.country) if port.country is not None else ""
            if query.upper() == country_str.upper():
                return (0, port.name)  # Country code matches first
            elif query in port.name.lower():
                return (1, port.name)  # Port name matches second
            else:
                return (2, port.name)  # Other matches last
        
        matches.sort(key=sort_key)
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
        
        # Calculate ETS costs
        ets_costs = self._calculate_ets_costs(co2_emissions, co2eq_emissions, origin_port, dest_port)
        
        return EmissionResult(
            imo_number=imo_number,
            ship_name=f"Ship IMO {imo_number}",
            distance_nm=distance_nm,
            co2_emissions=round(co2_emissions, 2),
            co2eq_emissions=round(co2eq_emissions, 2),
            ets_costs=ets_costs
        )
    
    def _calculate_ets_costs(self, co2_emissions: float, co2eq_emissions: float, 
                             origin_port: Port, dest_port: Port) -> Dict[int, float]:
        """Calculate ETS costs for different years based on EU-ETS rules"""
        
        # Determine EEA coverage multiplier
        origin_eea = origin_port.is_eea
        dest_eea = dest_port.is_eea
        
        if origin_eea and dest_eea:
            coverage_multiplier = 1.0  # Both ports in EEA
        elif origin_eea or dest_eea:
            coverage_multiplier = 0.5  # Mixed route (one EEA, one non-EEA)
        else:
            coverage_multiplier = 0.0  # Both ports outside EEA
        
        ets_costs = {}
        
        for ets_price in self.ets_prices:
            year = ets_price.year
            price_eur = ets_price.price_eur
            
            # Phase-in percentages
            if year == 2024:
                phase_in = 0.4
            elif year == 2025:
                phase_in = 0.7
            else:  # 2026 and onwards
                phase_in = 1.0
            
            # Use CO2 for 2024-2025, CO2eq for 2026+
            if year in [2024, 2025]:
                emissions_for_cost = co2_emissions
            else:
                emissions_for_cost = co2eq_emissions
            
            # Calculate cost: emissions (kg) * price (EUR/tonne) * phase-in * coverage
            # Convert kg to tonnes by dividing by 1000
            cost_eur = (emissions_for_cost / 1000) * price_eur * phase_in * coverage_multiplier
            ets_costs[year] = round(cost_eur, 2)
        
        return ets_costs

# Page configuration
st.set_page_config(
    page_title="🇪🇺 ETS Cost Calculator",
    page_icon="🇪🇺",
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
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .main-header h1 {
        color: white;
        margin: 0;
        font-size: 2.5rem;
        font-weight: 700;
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
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    }
    .sidebar-info {
        background: #e8f4fd;
        color: var(--text-color, black);
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    }
    .port-card {
        background: var(--background-color, white);
        color: var(--text-color, black);
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid var(--border-color, #e0e0e0);
        margin: 0.5rem 0;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
        transition: all 0.3s ease;
    }
    .port-card:hover {
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        transform: translateY(-2px);
    }
    .cost-highlight {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
        text-align: center;
    }
    .success-box {
        background: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    .warning-box {
        background: #fff3cd;
        border: 1px solid #ffeaa7;
        color: #856404;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    .error-box {
        background: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    .tab-container {
        background: var(--background-color, white);
        color: var(--text-color, black);
        border-radius: 8px;
        padding: 1rem;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    }
    .stSelectbox > div > div {
        background-color: var(--background-color, white) !important;
        color: var(--text-color, black) !important;
        border-radius: 8px;
        border: 1px solid var(--border-color, #e0e0e0) !important;
    }
    .stSelectbox > div > div > div {
        background-color: var(--background-color, white) !important;
        color: var(--text-color, black) !important;
    }
    .stSelectbox > div > div > div > div {
        background-color: var(--background-color, white) !important;
        color: var(--text-color, black) !important;
    }
    /* Placeholder styling */
    .stSelectbox > div > div > div > div[data-baseweb="select"] {
        background-color: var(--background-color, white) !important;
        color: var(--text-color, black) !important;
    }
    .stSelectbox > div > div > div > div[data-baseweb="select"] > div {
        background-color: var(--background-color, white) !important;
        color: var(--text-color, black) !important;
    }
    .stButton > button {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1) !important;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3) !important;
        background: linear-gradient(90deg, #5a6fd8 0%, #6a4190 100%) !important;
    }
    .stButton > button:disabled {
        background: #cccccc !important;
        color: #666666 !important;
        cursor: not-allowed;
    }
    .metric-container {
        background: var(--background-color, white);
        color: var(--text-color, black);
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Enhanced Header
st.markdown("""
<div class="main-header">
    <h1>🇪🇺 ETS Cost Calculator</h1>
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
        <p><strong>{ets_count} ETS prices</strong> loaded</p>
    </div>
    """.format(
        ports_count=len(calculator.ports),
        ships_count=len(calculator.mrv_ships),
        ets_count=len(calculator.ets_prices)
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
    - **💰 ETS Cost**: Calculate CO₂ emissions and EU-ETS costs for specific ships
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

# Main tabs - Enhanced interface with search functionality
tab1, tab2, tab3 = st.tabs(["💰 ETS Cost", "🚢 Port-to-Port", "🔍 Port Search"])

with tab1:
    st.markdown('<div class="tab-container">', unsafe_allow_html=True)
    
    st.header("💰 ETS Cost Calculator")
    st.markdown("Calculate CO₂ emissions and EU-ETS costs for specific ships using IMO numbers and MRV data")
    
    # Progress indicator
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🚢 Ship Information")
        
        # IMO number input with validation
        imo_number = st.text_input(
            "Enter IMO Number:", 
            placeholder="e.g., 1013676", 
            key="imo_input",
            help="Enter the 7-digit IMO number of the ship"
        )
        
        if imo_number:
            # Validate IMO number format
            if len(imo_number) != 7 or not imo_number.isdigit():
                st.error("❌ IMO number must be exactly 7 digits")
                ship_found = False
                ship_data = None
            else:
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
                        st.markdown('<div class="metric-container">', unsafe_allow_html=True)
                        st.metric("CO₂ per nm", f"{ship_data.co2_per_nm:.1f} kg")
                        st.markdown('</div>', unsafe_allow_html=True)
                    with col1_2:
                        st.markdown('<div class="metric-container">', unsafe_allow_html=True)
                        st.metric("CO₂eq per nm", f"{ship_data.co2eq_per_nm:.1f} kg")
                        st.markdown('</div>', unsafe_allow_html=True)
                else:
                    st.error(f"❌ Ship IMO {imo_number} not found in MRV database")
    
    with col2:
        st.subheader("💰 ETS Cost Calculator")
        
        # Unified port search for both origin and destination
        st.write("**Port Search**")
        port_search = st.text_input(
            "Search ports:",
            placeholder="e.g., 'Hamburg', 'TR', 'Turkey', 'Europe'",
            key="unified_port_search",
            help="Type to search by port name, country code, or region. This will filter both origin and destination port dropdowns."
        )
        
        # Filter ports based on unified search
        if port_search and len(port_search.strip()) >= 2:
            search_query = port_search.strip().lower()
            filtered_ports = []
            for port in calculator.ports:
                country_str = str(port.country) if port.country is not None else ""
                if (search_query in port.name.lower() or 
                    search_query.upper() == country_str.upper() or
                    search_query in country_str.lower() or
                    search_query in port.region.lower()):
                    filtered_ports.append(port)
            
            # Sort: exact country matches first, then port names
            def sort_key(port):
                country_str = str(port.country) if port.country is not None else ""
                if search_query.upper() == country_str.upper():
                    return (0, port.name)
                elif search_query in port.name.lower():
                    return (1, port.name)
                else:
                    return (2, port.name)
            
            filtered_ports.sort(key=sort_key)
            port_options = [f"{p.name} ({p.country})" for p in filtered_ports[:50]]  # Limit to 50 results
        else:
            port_options = [f"{p.name} ({p.country})" for p in calculator.ports]
        
        port_options = ["Select port..."] + port_options
        
        # Origin port selection
        st.write("**Origin Port**")
        origin_choice = st.selectbox("Choose origin port:", port_options, key="mrv_origin_select", index=0)
        
        # Destination port selection  
        st.write("**Destination Port**")
        dest_choice = st.selectbox("Choose destination port:", port_options, key="mrv_dest_select", index=0)
        
        if dest_choice and dest_choice != "Select destination port...":
            for port in calculator.ports:
                if f"{port.name} ({port.country})" == dest_choice:
                    mrv_dest_port = port
                    break
            else:
                mrv_dest_port = None
        else:
            mrv_dest_port = None
        
        if mrv_dest_port:
            st.success(f"✅ **{mrv_dest_port.name}** ({mrv_dest_port.country})")
            st.info(f"📍 Coordinates: {mrv_dest_port.lat:.2f}°N, {mrv_dest_port.lon:.2f}°E")
    
    # Calculate emissions button with enhanced validation
    st.markdown("---")
    
    # Validation status
    validation_status = []
    if not imo_number or len(imo_number) != 7 or not imo_number.isdigit():
        validation_status.append("❌ Valid IMO number required")
    elif not ship_found:
        validation_status.append("❌ IMO number not found in database")
    else:
        validation_status.append("✅ IMO number valid")
    
    if not mrv_origin_port:
        validation_status.append("❌ Origin port required")
    else:
        validation_status.append("✅ Origin port selected")
    
    if not mrv_dest_port:
        validation_status.append("❌ Destination port required")
    else:
        validation_status.append("✅ Destination port selected")
    
    # Show validation status
    for status in validation_status:
        st.write(status)
    
    # Calculate button
    can_calculate = all("✅" in status for status in validation_status)
    
    if st.button("💰 Calculate ETS Cost", type="primary", disabled=not can_calculate):
        if can_calculate:
            try:
                # Progress indicators
                progress_bar.progress(10)
                status_text.text("🔍 Validating ship data...")
                
                progress_bar.progress(30)
                status_text.text("🌊 Calculating maritime distance...")
                
                emission_result = calculator.calculate_emissions(
                    imo_number, mrv_origin_port, mrv_dest_port
                )
                
                progress_bar.progress(70)
                status_text.text("💰 Calculating ETS costs...")
                
                progress_bar.progress(100)
                status_text.text("✅ Calculation complete!")
                
                # Clear progress indicators
                progress_bar.empty()
                status_text.empty()
                
                st.success("✅ ETS Cost Calculation Complete!")
                
                # Enhanced results display
                st.subheader("📊 Route Information")
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown('<div class="metric-container">', unsafe_allow_html=True)
                    st.write(f"**Ship:** IMO {emission_result.imo_number}")
                    st.write(f"**Origin:** {mrv_origin_port.name} ({mrv_origin_port.country})")
                    st.markdown('</div>', unsafe_allow_html=True)
                with col2:
                    st.markdown('<div class="metric-container">', unsafe_allow_html=True)
                    st.write(f"**Destination:** {mrv_dest_port.name} ({mrv_dest_port.country})")
                    st.write(f"**Distance:** {emission_result.distance_nm} nm")
                    st.markdown('</div>', unsafe_allow_html=True)
                
                st.subheader("🌍 CO₂ Emissions")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.markdown('<div class="metric-container">', unsafe_allow_html=True)
                    st.metric(
                        label="Total CO₂ Emissions",
                        value=f"{emission_result.co2_emissions:,.0f} kg",
                        help=f"{emission_result.co2_emissions/1000:.1f} tonnes"
                    )
                    st.markdown('</div>', unsafe_allow_html=True)
                
                with col2:
                    st.markdown('<div class="metric-container">', unsafe_allow_html=True)
                    st.metric(
                        label="Total CO₂eq Emissions", 
                        value=f"{emission_result.co2eq_emissions:,.0f} kg",
                        help=f"{emission_result.co2eq_emissions/1000:.1f} tonnes"
                    )
                    st.markdown('</div>', unsafe_allow_html=True)
                
                with col3:
                    st.markdown('<div class="metric-container">', unsafe_allow_html=True)
                    st.metric(
                        label="Distance",
                        value=f"{emission_result.distance_nm} nm",
                        help="Maritime distance"
                    )
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                # EU-ETS Cost Information - simplified
                st.subheader("🇪🇺 EU-ETS Cost Analysis")
                
                # Display ETS costs by year with enhanced styling
                if emission_result.ets_costs:
                    st.subheader("💰 ETS Costs by Year")
                    
                    # Create a cost summary highlight
                    total_cost_2024 = emission_result.ets_costs.get(2024, 0)
                    total_cost_2030 = emission_result.ets_costs.get(2030, 0)
                    
                    # Calculate cost increase percentage, handling zero costs
                    if total_cost_2024 > 0:
                        cost_increase_pct = ((total_cost_2030/total_cost_2024 - 1) * 100)
                        cost_increase_text = f"Cost increase: {cost_increase_pct:.1f}% over 6 years"
                    else:
                        cost_increase_text = "No costs due to 0% coverage (non-EEA route)"
                    
                    st.markdown(f'''
                    <div class="cost-highlight">
                        <h3>Cost Projection</h3>
                        <p><strong>2024:</strong> €{total_cost_2024:,.0f} | <strong>2030:</strong> €{total_cost_2030:,.0f}</p>
                        <p>{cost_increase_text}</p>
                    </div>
                    ''', unsafe_allow_html=True)
                    
                    # Create columns for cost display with bar styling
                    cost_cols = st.columns(len(emission_result.ets_costs))
                    
                    for i, (year, cost) in enumerate(emission_result.ets_costs.items()):
                        with cost_cols[i]:
                            # Determine phase-in percentage and emission type
                            if year == 2024:
                                phase_in = "40%"
                                emission_type = "CO₂"
                                color = "#28a745"  # Green for early phase
                            elif year == 2025:
                                phase_in = "70%"
                                emission_type = "CO₂"
                                color = "#ffc107"  # Yellow for transition
                            else:
                                phase_in = "100%"
                                emission_type = "CO₂eq"
                                color = "#dc3545"  # Red for full phase
                            
                            st.markdown(f'''
                            <div class="metric-container" style="border-left: 4px solid {color};">
                                <h4 style="color: {color}; margin: 0;">{year}</h4>
                                <h2 style="color: {color}; margin: 0.5rem 0;">€{cost:,.0f}</h2>
                                <small>Phase-in: {phase_in}<br>Based on: {emission_type}</small>
                            </div>
                            ''', unsafe_allow_html=True)
                    
                    # Combined calculation details and coverage information
                    st.markdown("---")
                    st.markdown("""
                    ### 📋 EU-ETS Calculation Details
                    
                    **Coverage Rules:**
                    - **EEA-to-EEA Route**: 100% coverage (both ports in EEA)
                    - **Mixed Route**: 50% coverage (one EEA, one non-EEA port)
                    - **Non-EEA Route**: 0% coverage (both ports outside EEA)
                    
                    **Calculation Method:**
                    - **2024-2025**: Based on CO₂ emissions
                    - **2026+**: Based on CO₂eq emissions  
                    - **Phase-in**: 40% (2024), 70% (2025), 100% (2026+)
                    - **Applies to**: Ships of 5,000 GT and above
                    - **Free allowances**: 100% in 2024, reducing to 0% by 2026
                    """)
                    
            except Exception as e:
                st.error(f"❌ Calculation failed: {e}")
        else:
            st.warning("Please enter IMO number and select both origin and destination ports")
    
    st.markdown('</div>', unsafe_allow_html=True)  # Close tab-container

with tab2:
    st.markdown('<div class="tab-container">', unsafe_allow_html=True)
    st.header("🚢 Port-to-Port Distance Calculation")
    st.markdown("Calculate maritime distances between ports worldwide")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📍 Origin Port")
        
        # Origin port selection - back to original dropdown
        origin_options = [f"{p.name} ({p.country})" for p in calculator.ports]
        origin_options = ["Select origin port..."] + origin_options
        
        origin_choice = st.selectbox("Choose origin port:", origin_options, key="origin_select", index=0)
        
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
        st.subheader("📍 Destination Port")
        
        # Destination port selection - back to original dropdown
        dest_options = [f"{p.name} ({p.country})" for p in calculator.ports]
        dest_options = ["Select destination port..."] + dest_options
        
        dest_choice = st.selectbox("Choose destination port:", dest_options, key="dest_select", index=0)
        
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
    
    # Enhanced distance calculation with validation
    st.markdown("---")
    
    # Validation status
    port_validation = []
    if not origin_port:
        port_validation.append("❌ Origin port required")
    else:
        port_validation.append("✅ Origin port selected")
    
    if not dest_port:
        port_validation.append("❌ Destination port required")
    else:
        port_validation.append("✅ Destination port selected")
    
    # Show validation status
    for status in port_validation:
        st.write(status)
    
    # Calculate button
    can_calculate_distance = all("✅" in status for status in port_validation)
    
    if st.button("🌊 Calculate Distance", type="primary", disabled=not can_calculate_distance):
        if can_calculate_distance:
            with st.spinner("Calculating maritime distance..."):
                distance_result = calculator.calculate_distance(
                    origin_port.lon, origin_port.lat, 
                    dest_port.lon, dest_port.lat
                )
                
                if distance_result['success']:
                    st.success("✅ Distance Calculation Complete!")
                    
                    # Enhanced results display
                    st.subheader("📊 Distance Results")
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.markdown('<div class="metric-container">', unsafe_allow_html=True)
                        st.metric(
                            label="Distance (Nautical Miles)",
                            value=f"{distance_result['distance_nm']} nm"
                        )
                        st.markdown('</div>', unsafe_allow_html=True)
                    
                    with col2:
                        st.markdown('<div class="metric-container">', unsafe_allow_html=True)
                        st.metric(
                            label="Distance (Kilometers)", 
                            value=f"{distance_result['distance_km']} km"
                        )
                        st.markdown('</div>', unsafe_allow_html=True)
                    
                    with col3:
                        st.markdown('<div class="metric-container">', unsafe_allow_html=True)
                        st.metric(
                            label="Route Type",
                            value=distance_result['route_name']
                        )
                        st.markdown('</div>', unsafe_allow_html=True)
                    
                    # Enhanced route details
                    st.subheader("📍 Route Details")
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown('<div class="port-card">', unsafe_allow_html=True)
                        st.write(f"**From:** {origin_port.name} ({origin_port.country})")
                        st.write(f"📍 Coordinates: {origin_port.lat:.2f}°N, {origin_port.lon:.2f}°E")
                        st.write(f"🇪🇺 EEA Status: {'Yes' if origin_port.is_eea else 'No'}")
                        st.markdown('</div>', unsafe_allow_html=True)
                    
                    with col2:
                        st.markdown('<div class="port-card">', unsafe_allow_html=True)
                        st.write(f"**To:** {dest_port.name} ({dest_port.country})")
                        st.write(f"📍 Coordinates: {dest_port.lat:.2f}°N, {dest_port.lon:.2f}°E")
                        st.write(f"🇪🇺 EEA Status: {'Yes' if dest_port.is_eea else 'No'}")
                        st.markdown('</div>', unsafe_allow_html=True)
                    
                    # Route summary
                    st.markdown(f'''
                    <div class="cost-highlight">
                        <h3>Route Summary</h3>
                        <p><strong>Distance:</strong> {distance_result['distance_nm']} nautical miles ({distance_result['distance_km']} km)</p>
                        <p><strong>Calculation Method:</strong> {distance_result['route_name']}</p>
                    </div>
                    ''', unsafe_allow_html=True)
                    
                else:
                    st.error(f"❌ Calculation failed: {distance_result['error']}")
        else:
            st.warning("Please select both origin and destination ports")

    st.markdown('</div>', unsafe_allow_html=True)  # Close tab-container

with tab3:
    st.markdown('<div class="tab-container">', unsafe_allow_html=True)
    
    st.header("🔍 Port Search")
    st.markdown("Search ports by name, country code, or region")
    
    # Search input
    search_query = st.text_input(
        "Search ports:",
        placeholder="e.g., 'Hamburg', 'TR', 'Turkey', 'Europe'",
        help="Search by port name, country code (e.g., TR, DE, US), country name, or region"
    )
    
    # Search options
    col1, col2 = st.columns(2)
    
    with col1:
        search_limit = st.slider("Maximum results:", min_value=5, max_value=100, value=20)
    
    with col2:
        search_type = st.selectbox(
            "Search type:",
            ["All", "Port Name", "Country Code", "Country Name", "Region"],
            help="Filter search results by type"
        )
    
    # Search button
    if st.button("🔍 Search Ports", type="primary"):
        if search_query and len(search_query.strip()) >= 2:
            with st.spinner("Searching ports..."):
                # Get all matching ports
                all_matches = calculator.search_ports(search_query.strip(), limit=1000)
                
                # Filter by search type if specified
                if search_type == "Port Name":
                    matches = [p for p in all_matches if search_query.lower() in p.name.lower()]
                elif search_type == "Country Code":
                    matches = [p for p in all_matches if search_query.upper() == p.country]
                elif search_type == "Country Name":
                    # This would need a country code to name mapping
                    matches = [p for p in all_matches if search_query.lower() in p.country.lower()]
                elif search_type == "Region":
                    matches = [p for p in all_matches if search_query.lower() in p.region.lower()]
                else:  # All
                    matches = all_matches
                
                # Limit results
                matches = matches[:search_limit]
                
                if matches:
                    st.success(f"✅ Found {len(matches)} ports matching '{search_query}'")
                    
                    # Display results in a table
                    st.subheader("📋 Search Results")
                    
                    # Create data for the table
                    search_data = []
                    for port in matches:
                        search_data.append({
                            "Port Name": port.name,
                            "Country": port.country,
                            "Region": port.region,
                            "Latitude": f"{port.lat:.4f}°",
                            "Longitude": f"{port.lon:.4f}°",
                            "EEA Status": "✅ Yes" if port.is_eea else "❌ No"
                        })
                    
                    # Display as a dataframe
                    df = st.dataframe(
                        search_data,
                        use_container_width=True,
                        hide_index=True
                    )
                    
                    # Show summary statistics
                    if matches:
                        st.subheader("📊 Search Summary")
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            st.metric("Total Results", len(matches))
                        
                        with col2:
                            eea_count = sum(1 for p in matches if p.is_eea)
                            st.metric("EEA Ports", eea_count)
                
                with col3:
                    regions = set(p.region for p in matches)
                    st.metric("Regions", len(regions))
                
                with col4:
                    countries = set(p.country for p in matches)
                    st.metric("Countries", len(countries))
                
                # Show top countries
                if countries:
                    st.subheader("🌍 Countries Found")
                    country_counts = {}
                    for port in matches:
                        country_counts[port.country] = country_counts.get(port.country, 0) + 1
                    
                    # Sort by count
                    sorted_countries = sorted(country_counts.items(), key=lambda x: x[1], reverse=True)
                    
                    # Display top 10 countries
                    for country, count in sorted_countries[:10]:
                        st.write(f"**{country}**: {count} ports")
        
        else:
            st.warning(f"❌ No ports found matching '{search_query}'")
            st.info("💡 Try searching with:")
            st.write("- Port names (e.g., 'Hamburg', 'Rotterdam')")
            st.write("- Country codes (e.g., 'TR', 'DE', 'US')")
            st.write("- Regions (e.g., 'Europe', 'Asia', 'North America')")
    
    else:
        st.warning("Please enter at least 2 characters to search")
    
    # Show some example searches
    st.subheader("💡 Search Examples")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.write("**By Country Code:**")
        st.code("TR    # Turkish ports\nDE    # German ports\nUS    # US ports")
    
    with col2:
        st.write("**By Port Name:**")
        st.code("Hamburg\nRotterdam\nShanghai")
    
    with col3:
        st.write("**By Region:**")
        st.code("Europe\nAsia\nNorth America")
    
    st.markdown('</div>', unsafe_allow_html=True)  # Close tab-container

# Footer
st.markdown("---")
st.markdown("**ETS Cost Calculator** - Powered by Python SeaRoute wrapper")
