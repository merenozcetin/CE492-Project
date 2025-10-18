#!/usr/bin/env python3
"""
SeaRoute Maritime Distance Calculator - Streamlit App
Web-based interface for calculating maritime distances between ports worldwide.

Usage:
    streamlit run searoute_streamlit.py
"""

import streamlit as st
import json
import subprocess
import tempfile
import os
import sys
from typing import Dict, List, Tuple, Optional
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

@dataclass
class RouteResult:
    """Maritime route calculation result"""
    origin: Port
    destination: Port
    distance_nm: float
    origin_approx_km: float
    dest_approx_km: float
    route_name: str

class SeaRouteCalculator:
    """Main SeaRoute distance calculator"""
    
    def __init__(self):
        self.ports = []
        self.searoute_jar_path = None
        self.java_path = None
        self._load_ports()
        self._setup_searoute()
    
    def _load_ports(self):
        """Load port database from the web interface HTML file"""
        # Read ports from the HTML file
        html_file = 'web-interface/port_calculator.html'
        if not os.path.exists(html_file):
            st.error("❌ Port database not found. Please ensure web-interface/port_calculator.html exists.")
            return
        
        with open(html_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract ports array from JavaScript
        start_marker = 'const ports = ['
        end_marker = '];'
        
        start_pos = content.find(start_marker)
        end_pos = content.find(end_marker, start_pos)
        
        if start_pos == -1 or end_pos == -1:
            st.error("❌ Could not find ports array in HTML file")
            return
        
        ports_js = content[start_pos + len(start_marker):end_pos]
        
        # Parse JavaScript port objects
        port_lines = ports_js.strip().split('\n')
        for line in port_lines:
            line = line.strip()
            if line.startswith('{') and line.endswith(','):
                line = line[:-1]  # Remove trailing comma
            elif line.startswith('{') and line.endswith('}'):
                pass  # Keep as is
            
            try:
                # Simple parsing of JavaScript object
                if 'name:' in line and 'country:' in line:
                    # Extract values using string manipulation
                    name_start = line.find('"', line.find('name:')) + 1
                    name_end = line.find('"', name_start)
                    name = line[name_start:name_end]
                    
                    country_start = line.find('"', line.find('country:')) + 1
                    country_end = line.find('"', country_start)
                    country = line[country_start:country_end]
                    
                    region_start = line.find('"', line.find('region:')) + 1
                    region_end = line.find('"', region_start)
                    region = line[region_start:region_end]
                    
                    lon_start = line.find('lon:') + 4
                    lon_end = line.find(',', lon_start)
                    lon = float(line[lon_start:lon_end])
                    
                    lat_start = line.find('lat:') + 4
                    lat_end = line.find('}', lat_start)
                    lat = float(line[lat_start:lat_end])
                    
                    # Check for alternate name
                    alternate = None
                    if 'alternate:' in line:
                        alt_start = line.find('"', line.find('alternate:')) + 1
                        alt_end = line.find('"', alt_start)
                        alternate = line[alt_start:alt_end]
                    
                    port = Port(
                        name=name,
                        country=country,
                        region=region,
                        lon=lon,
                        lat=lat,
                        alternate=alternate
                    )
                    self.ports.append(port)
                    
            except (ValueError, IndexError) as e:
                continue  # Skip malformed lines
    
    def _setup_searoute(self):
        """Setup SeaRoute Java engine"""
        # Find SeaRoute JAR
        searoute_jar = 'searoute-engine/searoute.jar'
        if os.path.exists(searoute_jar):
            self.searoute_jar_path = searoute_jar
        else:
            st.error("❌ SeaRoute JAR not found. Please ensure searoute-engine/searoute.jar exists.")
            return
        
        # Find Java
        java_paths = [
            'java',  # Try PATH first
            'C:\\Program Files\\Java\\jdk-25\\bin\\java.exe',
            'C:\\Program Files\\Java\\jdk-17\\bin\\java.exe',
            'C:\\Program Files\\Java\\jdk-11\\bin\\java.exe',
            'C:\\Program Files\\Java\\jdk-9\\bin\\java.exe'
        ]
        
        for java_path in java_paths:
            try:
                if java_path == 'java':
                    result = subprocess.run([java_path, '-version'], capture_output=True, text=True)
                    if result.returncode == 0:
                        self.java_path = java_path
                        break
                else:
                    if os.path.exists(java_path):
                        result = subprocess.run([java_path, '-version'], capture_output=True, text=True)
                        if result.returncode == 0:
                            self.java_path = java_path
                            break
            except (FileNotFoundError, subprocess.SubprocessError):
                continue
        
        if not self.java_path:
            st.error("❌ Java not found. Please install Java JDK 9 or higher.")
            return
    
    def search_ports(self, query: str, limit: int = 10) -> List[Port]:
        """Search ports by name, country, or region"""
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
                          dest_lon: float, dest_lat: float) -> RouteResult:
        """Calculate maritime distance using SeaRoute"""
        
        if not self.searoute_jar_path or not self.java_path:
            raise Exception("SeaRoute engine not properly configured")
        
        # Round coordinates to 2 decimal places
        origin_lon = round(origin_lon, 2)
        origin_lat = round(origin_lat, 2)
        dest_lon = round(dest_lon, 2)
        dest_lat = round(dest_lat, 2)
        
        # Create temporary CSV file
        temp_csv = 'temp_input.csv'
        temp_output = 'out.geojson'
        
        try:
            # Create input CSV
            with open(temp_csv, 'w', newline='') as f:
                f.write('route name,olon,olat,dlon,dlat\n')
                f.write(f'Custom Route,{origin_lon},{origin_lat},{dest_lon},{dest_lat}\n')
            
            # Change to searoute directory
            original_cwd = os.getcwd()
            searoute_dir = 'searoute-engine'
            
            if not os.path.exists(searoute_dir):
                raise Exception(f"SeaRoute directory not found: {searoute_dir}")
            
            os.chdir(searoute_dir)
            
            try:
                # Run SeaRoute
                cmd = [self.java_path, '-jar', 'searoute.jar', temp_csv]
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
                
                if result.returncode != 0:
                    raise Exception(f"SeaRoute failed: {result.stderr}")
                
                # Read output
                if not os.path.exists(temp_output):
                    raise Exception("SeaRoute did not produce output file")
                
                with open(temp_output, 'r', encoding='utf-8') as f:
                    geojson_data = json.load(f)
                
                # Extract results
                if 'features' in geojson_data and len(geojson_data['features']) > 0:
                    feature = geojson_data['features'][0]
                    properties = feature['properties']
                    
                    # Convert km to nautical miles
                    distance_km = float(properties['distKM'])
                    distance_nm = distance_km / 1.852
                    
                    origin_approx_km = float(properties['dFromKM'])
                    dest_approx_km = float(properties['dToKM'])
                    
                    # Create dummy ports for result
                    origin_port = Port("Custom Origin", "Unknown", "Unknown", origin_lon, origin_lat)
                    dest_port = Port("Custom Destination", "Unknown", "Unknown", dest_lon, dest_lat)
                    
                    return RouteResult(
                        origin=origin_port,
                        destination=dest_port,
                        distance_nm=round(distance_nm, 1),
                        origin_approx_km=round(origin_approx_km, 2),
                        dest_approx_km=round(dest_approx_km, 2),
                        route_name=properties.get('route name', 'Custom Route')
                    )
                else:
                    raise Exception("No route found in SeaRoute output")
                    
            finally:
                os.chdir(original_cwd)
                
        finally:
            # Clean up temporary files
            for temp_file in [temp_csv, temp_output]:
                if os.path.exists(temp_file):
                    try:
                        os.remove(temp_file)
                    except:
                        pass
                if os.path.exists(f'searoute-engine/{temp_file}'):
                    try:
                        os.remove(f'searoute-engine/{temp_file}')
                    except:
                        pass

# Initialize the calculator
@st.cache_resource
def get_calculator():
    """Get cached calculator instance"""
    return SeaRouteCalculator()

def main():
    """Main Streamlit app"""
    
    # Page configuration
    st.set_page_config(
        page_title="SeaRoute Maritime Distance Calculator",
        page_icon="🌊",
        layout="wide"
    )
    
    # Header
    st.title("🌊 SeaRoute Maritime Distance Calculator")
    st.markdown("Calculate maritime distances between ports worldwide using Eurostat's SeaRoute engine")
    
    # Initialize calculator
    calculator = get_calculator()
    
    if not calculator.ports:
        st.error("❌ Failed to load port database. Please ensure web-interface/port_calculator.html exists.")
        return
    
    if not calculator.java_path:
        st.error("❌ Java not found. Please install Java JDK 9 or higher.")
        return
    
    # Sidebar info
    with st.sidebar:
        st.header("ℹ️ About")
        st.info(f"**{len(calculator.ports)} ports** loaded from database")
        st.success("✅ SeaRoute engine ready")
        st.success("✅ Java runtime found")
        
        st.header("🔧 Requirements")
        st.markdown("""
        - Java JDK 9+
        - SeaRoute engine
        - Port database
        """)
    
    # Main content
    tab1, tab2, tab3 = st.tabs(["🚢 Port-to-Port", "📍 Coordinates", "🔍 Port Search"])
    
    with tab1:
        st.header("Port-to-Port Distance Calculation")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Origin Port")
            origin_query = st.text_input("Search origin port:", placeholder="e.g., hamburg, rotterdam")
            
            if origin_query:
                origin_ports = calculator.search_ports(origin_query, 10)
                if origin_ports:
                    origin_options = [f"{p.name} ({p.country})" for p in origin_ports]
                    origin_choice = st.selectbox("Select origin port:", origin_options)
                    origin_port = origin_ports[origin_options.index(origin_choice)]
                else:
                    st.warning("No ports found matching your search")
                    origin_port = None
            else:
                origin_port = None
        
        with col2:
            st.subheader("Destination Port")
            dest_query = st.text_input("Search destination port:", placeholder="e.g., shanghai, singapore")
            
            if dest_query:
                dest_ports = calculator.search_ports(dest_query, 10)
                if dest_ports:
                    dest_options = [f"{p.name} ({p.country})" for p in dest_ports]
                    dest_choice = st.selectbox("Select destination port:", dest_options)
                    dest_port = dest_ports[dest_options.index(dest_choice)]
                else:
                    st.warning("No ports found matching your search")
                    dest_port = None
            else:
                dest_port = None
        
        # Calculate button
        if st.button("🚀 Calculate Distance", type="primary"):
            if origin_port and dest_port:
                with st.spinner("Calculating maritime distance..."):
                    try:
                        result = calculator.calculate_distance(
                            origin_port.lon, origin_port.lat, 
                            dest_port.lon, dest_port.lat
                        )
                        
                        # Display results
                        st.success("✅ Calculation Complete!")
                        
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.metric(
                                label="🌊 Maritime Distance",
                                value=f"{result.distance_nm} nm",
                                help=f"{result.distance_nm * 1.852:.1f} km"
                            )
                        
                        with col2:
                            st.metric(
                                label="📍 Origin Approximation",
                                value=f"{result.origin_approx_km} km"
                            )
                        
                        with col3:
                            st.metric(
                                label="📍 Destination Approximation",
                                value=f"{result.dest_approx_km} km"
                            )
                        
                        st.info(f"🏷️ Route Name: {result.route_name}")
                        
                    except Exception as e:
                        st.error(f"❌ Calculation failed: {e}")
            else:
                st.warning("Please select both origin and destination ports")
    
    with tab2:
        st.header("Coordinate-based Distance Calculation")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Origin Coordinates")
            origin_lon = st.number_input("Origin Longitude:", value=0.0, format="%.2f")
            origin_lat = st.number_input("Origin Latitude:", value=0.0, format="%.2f")
        
        with col2:
            st.subheader("Destination Coordinates")
            dest_lon = st.number_input("Destination Longitude:", value=0.0, format="%.2f")
            dest_lat = st.number_input("Destination Latitude:", value=0.0, format="%.2f")
        
        if st.button("🚀 Calculate Distance from Coordinates", type="primary"):
            with st.spinner("Calculating maritime distance..."):
                try:
                    result = calculator.calculate_distance(origin_lon, origin_lat, dest_lon, dest_lat)
                    
                    # Display results
                    st.success("✅ Calculation Complete!")
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric(
                            label="🌊 Maritime Distance",
                            value=f"{result.distance_nm} nm",
                            help=f"{result.distance_nm * 1.852:.1f} km"
                        )
                    
                    with col2:
                        st.metric(
                            label="📍 Origin Approximation",
                            value=f"{result.origin_approx_km} km"
                        )
                    
                    with col3:
                        st.metric(
                            label="📍 Destination Approximation",
                            value=f"{result.dest_approx_km} km"
                        )
                    
                    st.info(f"🏷️ Route Name: {result.route_name}")
                    
                except Exception as e:
                    st.error(f"❌ Calculation failed: {e}")
    
    with tab3:
        st.header("Port Search")
        
        search_query = st.text_input("Search ports:", placeholder="e.g., hamburg, germany, container")
        
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
    st.markdown("**SeaRoute Maritime Distance Calculator** - Powered by Eurostat's SeaRoute engine")

if __name__ == "__main__":
    main()
