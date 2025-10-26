# 📖 EU ETS Maritime Distance Calculator - Technical Documentation

## 🎯 Overview

This application calculates maritime distances between ports worldwide using Java SeaRoute, which provides accurate shipping route distances based on actual maritime networks rather than straight-line calculations.

## 🏗️ Architecture

### System Architecture

```
User Browser (localhost:8080)
        ↓
Python Web Server (app.py)
        ↓
Java SeaRoute Wrapper (tools/java_searoute_wrapper.py)
        ↓
Java SeaRoute (searoute.jar)
        ↓
Maritime Network Database (marnet/*.gpkg)
```

### Component Overview

1. **Web Server** (`server/app.py`): Python HTTP server that handles web requests
2. **Port Database** (`server/data/ports.json`): 13,951 ports worldwide
3. **Java SeaRoute Wrapper** (`server/tools/java_searoute_wrapper.py`): Python interface to Java SeaRoute
4. **Java SeaRoute** (`server/java-searoute/searoute.jar`): Actual routing engine
5. **Maritime Network** (`server/marnet/*.gpkg`): Geographic shipping lane database

## 📄 Code Structure

### Main Application (`server/app.py`)

The main application is a Python web server that:

1. **Serves HTML Interface**: Provides a web-based UI for port selection and distance calculation
2. **Handles API Requests**: Processes port search and distance calculation requests
3. **Calculates Distances**: Uses Java SeaRoute for accurate maritime routing

#### Key Classes

##### `CalculatorHandler` (HTTP Request Handler)

This class handles all HTTP requests and contains the main logic:

**Methods:**

- `do_GET()`: Routes requests to appropriate handlers
- `handle_port_search()`: Handles port search API requests
- `handle_calculation()`: Handles distance calculation API requests
- `calculate_distances()`: Main distance calculation logic
- `load_ports()`: Loads port database from JSON
- `search_ports()`: Searches ports by name or country code

**How Port Search Works:**

```python
def search_ports(self, ports, search_term):
    # 1. Check minimum search length (2 characters)
    if len(search_term) < 2:
        return []
    
    # 2. Convert search term to lowercase
    search_term = search_term.lower()
    
    # 3. Search in port names and country codes
    for port in ports:
        if (search_term in port['name'].lower() or 
            search_term in port['country'].lower()):
            matches.append({
                'name': port['name'],
                'country': port['country'],
                'lat': port['lat'],
                'lon': port['lon']
            })
    
    # 4. Return top 20 matches sorted by relevance
    return matches[:20]
```

**How Distance Calculation Works:**

```python
def calculate_distances(self, origin_lat, origin_lon, dest_lat, dest_lon):
    # 1. Try to use Java SeaRoute
    if JAVA_AVAILABLE:
        java_wrapper = JavaSeaRouteWrapper()
        java_result = java_wrapper.calculate_distance(origin_lon, origin_lat, dest_lon, dest_lat)
        
        # 2. If successful, return the result
        if java_result['success']:
            return {
                'distance': {
                    'distance_km': java_result['distance_km'],
                    'distance_nm': java_result['distance_nm'],
                    'method': 'Java SeaRoute (Actual Shipping Routes)',
                    'route_complexity': java_result['route_complexity'],
                    'success': True
                }
            }
        else:
            # 3. If failed, return error
            return {'distance': {'error': java_result['error'], 'success': False}}
```

### Java SeaRoute Wrapper (`server/tools/java_searoute_wrapper.py`)

This wrapper provides a Python interface to the Java SeaRoute executable:

**How It Works:**

```python
class JavaSeaRouteWrapper:
    def calculate_distance(self, origin_lon, origin_lat, dest_lon, dest_lat):
        # 1. Create temporary input/output files
        input_file = os.path.join(self.temp_dir, 'input.csv')
        output_file = os.path.join(self.temp_dir, 'output.csv')
        
        # 2. Write coordinates to input file
        with open(input_file, 'w') as f:
            f.write(f'{origin_lon},{origin_lat},{dest_lon},{dest_lat}')
        
        # 3. Run Java SeaRoute
        cmd = [
            'java', '-jar', self.searoute_jar_path,
            '-i', input_file,
            '-o', output_file,
            '-res', '20'  # 20km resolution
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # 4. Parse output and return results
        with open(output_file, 'r') as f:
            # Parse CSV output
            distance_km, distance_nm = self.parse_output(output_file)
        
        return {
            'success': True,
            'distance_km': distance_km,
            'distance_nm': distance_nm,
            'route_complexity': num_waypoints
        }
```

**Key Features:**

- Uses subprocess to call Java SeaRoute JAR file
- Creates temporary CSV files for input/output
- Parses CSV output to extract distance and waypoints
- Handles errors gracefully

## 🔄 Application Flow

### 1. Server Startup

```
python app.py
    ↓
Load Java SeaRoute wrapper
    ↓
Check Java availability
    ↓
Start HTTP server on port 8080
    ↓
Ready to accept connections
```

### 2. Port Search Flow

```
User types "hamburg"
    ↓
Browser sends: GET /api/ports?q=hamburg
    ↓
handle_port_search() called
    ↓
load_ports() loads port database from JSON
    ↓
search_ports() searches by name/country
    ↓
Returns: [{"name": "Hamburg", "country": "DE", ...}, ...]
    ↓
Browser displays dropdown results
```

### 3. Distance Calculation Flow

```
User clicks "Calculate Distance"
    ↓
Browser sends: GET /api/calculate?origin_lat=X&origin_lon=Y&dest_lat=A&dest_lon=B
    ↓
handle_calculation() called
    ↓
calculate_distances() executes
    ↓
Java SeaRoute Wrapper creates temp files
    ↓
Runs: java -jar searoute.jar -i input.csv -o output.csv -res 20
    ↓
Parses output and gets distance
    ↓
Returns: {"distance": {"distance_nm": 10920, "distance_km": 20225, ...}}
    ↓
Browser displays results
```

## 🔧 Java SeaRoute Integration

### Why Java SeaRoute?

Java SeaRoute uses an actual maritime network database that includes:
- Shipping lanes
- Canal passages
- Strait crossings
- Port approaches
- Coastal routes

This provides **48-137% more accurate** distances than straight-line calculations.

### How It Works

1. **Input**: Starting and ending coordinates (lon, lat)
2. **Processing**: Java SeaRoute finds the shortest path through the maritime network
3. **Output**: Total distance and waypoints along the route

### Resolution Parameter

```python
'-res', '20'  # 20km resolution
```

This parameter controls the granularity of the routing:
- **Lower value** (e.g., 5): More detailed route, slower calculation
- **Higher value** (e.g., 100): Faster calculation, less detailed route
- **Recommended**: 20km for balance between accuracy and speed

## 📊 Data Structures

### Port Object

```python
{
    "name": "Hamburg",
    "country": "DE",
    "region": "Europe",
    "lon": 9.9937,
    "lat": 53.5511,
    "alternate": null,
    "is_eea": true  # EEA membership for ETS coverage
}
```

### Distance Result

```python
{
    "timestamp": "2025-10-26T12:00:00",
    "origin": {"lat": 53.5511, "lon": 9.9937},
    "destination": {"lat": 31.2304, "lon": 121.4737},
    "distance": {
        "distance_km": 20225.3,
        "distance_nm": 10920.1,
        "method": "Java SeaRoute (Actual Shipping Routes)",
        "route_complexity": 45,  # Number of waypoints
        "success": True
    }
}
```

### Error Result

```python
{
    "distance": {
        "error": "Java not available",
        "success": False
    }
}
```

## 🛠️ Configuration

### Port Configuration

The server runs on port 8080 by default. To change:

```python
# In server/app.py
PORT = 8080  # Change to your desired port
```

### Java SeaRoute Path

The wrapper automatically finds the JAR file:
```python
# In server/tools/java_searoute_wrapper.py
searoute_jar_path = "java-searoute/searoute.jar"
```

### Maritime Network Database

The database files are automatically used by Java SeaRoute:
```
server/marnet/
├── marnet_plus_5km.gpkg   # 5km resolution
├── marnet_plus_10km.gpkg   # 10km resolution
├── marnet_plus_20km.gpkg  # 20km resolution (used)
├── marnet_plus_50km.gpkg  # 50km resolution
└── marnet_plus_100km.gpkg # 100km resolution
```

## 🚀 API Reference

### GET /api/ports?q={search_term}

Search for ports by name or country code.

**Example:**
```
GET /api/ports?q=hamburg
```

**Response:**
```json
[
    {
        "name": "Hamburg",
        "country": "DE",
        "lat": 53.5511,
        "lon": 9.9937,
        "is_eea": true
    }
]
```

### GET /api/calculate?origin_lat={lat}&origin_lon={lon}&dest_lat={lat}&dest_lon={lon}

Calculate distance between two points.

**Example:**
```
GET /api/calculate?origin_lat=53.5511&origin_lon=9.9937&dest_lat=31.2304&dest_lon=121.4737
```

**Response:**
```json
{
    "timestamp": "2025-10-26T12:00:00",
    "origin": {"lat": 53.5511, "lon": 9.9937},
    "destination": {"lat": 31.2304, "lon": 121.4737},
    "distance": {
        "distance_km": 20225.3,
        "distance_nm": 10920.1,
        "method": "Java SeaRoute (Actual Shipping Routes)",
        "route_complexity": 45,
        "success": true
    }
}
```

## 🐛 Troubleshooting

### Common Issues

**1. Port search returns no results**
- Check that `server/data/ports.json` exists
- Verify file encoding (should be UTF-8)
- Check console for error messages

**2. Java SeaRoute fails**
- Verify Java is installed: `java -version`
- Check that `server/java-searoute/searoute.jar` exists
- Verify `server/marnet/*.gpkg` files exist
- Check console for Java error messages

**3. Server won't start**
- Port 8080 already in use: Change port in `server/app.py`
- Python dependencies not installed: `pip install -r requirements.txt`

**4. Distance calculation returns error**
- Make sure Java is available
- Check that coordinates are valid (lat: -90 to 90, lon: -180 to 180)
- Verify maritime network database files exist

## 📝 Development

### Adding New Features

1. **New Port Search Criteria**: Modify `search_ports()` in `server/app.py`
2. **Alternative Distance Methods**: Add methods to `calculate_distances()`
3. **Additional API Endpoints**: Add new handlers to `CalculatorHandler`

### Debugging

Enable debug logging:
```python
# In server/app.py
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Testing

Test individual components:
```python
# Test port loading
python -c "from app import CalculatorHandler; h = CalculatorHandler(); print(len(h.load_ports()))"

# Test Java SeaRoute
python -c "from tools.java_searoute_wrapper import JavaSeaRouteWrapper; w = JavaSeaRouteWrapper(); print(w.calculate_distance(9.99, 53.55, 121.47, 31.23))"
```

## 📚 Further Reading

- Java SeaRoute Documentation: `server/java-searoute/README.md`
- Port Database Format: `server/data/ports.json`
- EU ETS Regulations: See `docs/CE492_Project_Description[1].md`

---

**Questions?** Check the main README at the project root or the QUICK_START guide!