import streamlit as st
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
        self.ship_types = []
        self._load_ports()
        self._load_ship_types()
    
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
                    alternate=port_data.get('alternate')
                )
                self.ports.append(port)
            
            print(f"✅ Loaded {len(self.ports)} ports")
            
        except Exception as e:
            print(f"❌ Error loading ports: {e}")
    
    def _load_ship_types(self):
        """Load ship types from CSV file"""
        try:
            import csv
            
            with open('data/registeredships.csv', 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    ship_type = ShipType(
                        name=row['Ship Type'],
                        co2_per_nm=float(row[' Avg. CO₂ emissions per distance [kg CO₂ / n mile]']),
                        co2eq_per_nm=float(row['Avg. CO₂eq emissions per distance [kg CO₂eq / n mile]'])
                    )
                    self.ship_types.append(ship_type)
            
            print(f"✅ Loaded {len(self.ship_types)} ship types")
            
        except Exception as e:
            print(f"❌ Error loading ship types: {e}")

# Page configuration
st.set_page_config(
    page_title="SeaRoute Maritime Distance Calculator",
    page_icon="🌊",
    layout="wide"
)

# Header
st.title("🌊 SeaRoute Maritime Distance Calculator")
st.markdown("Calculate maritime distances between ports worldwide")

# Initialize calculator
calculator = SeaRouteCalculator()

# Sidebar info
with st.sidebar:
    st.header("ℹ️ About")
    st.info(f"**{len(calculator.ports)} ports** loaded")
    st.info(f"**{len(calculator.ship_types)} ship types** loaded")

# Main content
st.write("App is working!")
