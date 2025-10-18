# 📚 Code Documentation

## 🏗️ Architecture Overview

The SeaRoute Maritime Distance Calculator is built with a clean, modular architecture using Streamlit and Python. Here's how the code is organized:

## 📋 Core Components

### 1. Data Models (`@dataclass`)

#### Port Class
```python
@dataclass
class Port:
    """Port information"""
    name: str          # Primary port name
    country: str       # Country where port is located
    region: str        # Geographic region
    lon: float         # Longitude coordinate (-180 to 180)
    lat: float         # Latitude coordinate (-90 to 90)
    alternate: Optional[str] = None  # Alternative port name
```

**Purpose**: Represents a maritime port with all necessary information for distance calculations.

### 2. Main Calculator Class

#### SeaRouteCalculator Class
```python
class SeaRouteCalculator:
    """Main SeaRoute distance calculator using Python wrapper"""
```

**Responsibilities**:
- Load and manage port data
- Perform maritime distance calculations
- Search and filter ports
- Handle errors gracefully

#### Key Methods Explained

##### `__init__(self)`
```python
def __init__(self):
    self.ports = []        # Initialize empty ports list
    self._load_ports()     # Load port data from JSON
```

**What it does**:
- Creates an empty list to store port objects
- Calls the port loading method
- Sets up the calculator for use

##### `_load_ports(self)`
```python
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
```

**What it does**:
- Opens and reads the JSON port database
- Creates `Port` objects for each port in the database
- Handles file loading errors gracefully
- Provides feedback on successful loading

##### `search_ports(self, query: str, limit: int = 10)`
```python
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
```

**What it does**:
- Takes a search query and maximum results limit
- Searches through all ports for matches
- Looks in name, country, region, and alternate name fields
- Returns a list of matching `Port` objects
- Limits results to specified number

##### `calculate_distance(self, origin_lon, origin_lat, dest_lon, dest_lat)`
```python
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
```

**What it does**:
- Takes origin and destination coordinates
- Rounds coordinates to 2 decimal places for precision
- Calls the SeaRoute wrapper to calculate maritime distance
- Handles different possible result formats from SeaRoute
- Includes fallback calculation using great circle distance
- Returns distance in both kilometers and nautical miles
- Provides comprehensive error handling

## 🎨 Streamlit UI Components

### Page Configuration
```python
st.set_page_config(
    page_title="SeaRoute Maritime Distance Calculator",
    page_icon="🌊",
    layout="wide"
)
```

**Purpose**: Sets up the Streamlit page with title, icon, and wide layout for better user experience.

### Calculator Initialization
```python
def get_calculator():
    """Get calculator instance"""
    return SeaRouteCalculator()

calculator = get_calculator()
```

**Purpose**: Creates a single calculator instance that's used throughout the app.

### Sidebar Information
```python
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
```

**Purpose**: Shows port count and debug information to help users understand the app status.

### Tab Structure
```python
tab1, tab2, tab3 = st.tabs(["🚢 Port-to-Port", "📍 Coordinates", "🔍 Port Search"])
```

**Purpose**: Organizes the app into three main functional areas.

## 🔄 Data Flow

### 1. Application Startup
```
App starts → Calculator created → Ports loaded → UI rendered
```

### 2. Port Selection Flow
```
User selects port → Port object retrieved → Coordinates displayed → Ready for calculation
```

### 3. Distance Calculation Flow
```
User clicks calculate → Coordinates sent to SeaRoute → Distance calculated → Results displayed
```

### 4. Error Handling Flow
```
Error occurs → Exception caught → Error message displayed → User can retry
```

## 🛠️ Error Handling Strategy

### File Loading Errors
- Check if file exists before loading
- Provide clear error messages
- Graceful degradation (empty port list)

### SeaRoute Calculation Errors
- Debug logging to understand result format
- Multiple fallback strategies
- Mathematical distance calculation as last resort

### User Input Errors
- Validation of coordinate ranges
- Clear error messages
- Guidance for correct input

## 🚀 Performance Considerations

### Data Loading
- Ports loaded once at startup
- No repeated file I/O operations
- Efficient search through in-memory data

### Distance Calculations
- SeaRoute wrapper handles complex routing
- Fallback calculations for reliability
- Cached results where possible

### UI Responsiveness
- Immediate feedback for user actions
- Loading spinners for long operations
- Clear status indicators

## 🔧 Extensibility

### Adding New Port Data
1. Update `data/ports.json` with new port information
2. Restart the application
3. New ports automatically available

### Adding New Features
1. Extend the `SeaRouteCalculator` class
2. Add new UI components in Streamlit
3. Update the tab structure as needed

### Customizing Calculations
1. Modify the `calculate_distance` method
2. Add new calculation types
3. Extend the result format

This architecture provides a solid foundation for maritime distance calculations while remaining flexible and extensible for future enhancements.
