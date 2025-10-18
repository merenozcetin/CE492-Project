# 🌊 SeaRoute Maritime Distance Calculator

A clean, modern Streamlit web application for calculating maritime distances between ports worldwide using the Python SeaRoute wrapper.

## 📁 Project Structure

```
searoute-master/
├── src/
│   └── app.py                    # Main Streamlit application
├── data/
│   └── ports.json               # Port database (3,800+ ports)
├── docs/
│   └── CE492_Project_Description[1].md  # Project documentation
├── requirements.txt              # Python dependencies
├── LICENSE                       # MIT License
└── README.md                     # This file
```

## 🏗️ Code Architecture

### 📋 Data Classes

#### `Port` Class
```python
@dataclass
class Port:
    """Port information"""
    name: str          # Port name (e.g., "Hamburg")
    country: str       # Country (e.g., "Germany")
    region: str        # Region (e.g., "Europe")
    lon: float         # Longitude coordinate
    lat: float         # Latitude coordinate
    alternate: Optional[str] = None  # Alternate port name
```

### 🧮 Core Calculator Class

#### `SeaRouteCalculator` Class
The main calculator class that handles all maritime distance calculations.

**Key Methods:**

1. **`__init__(self)`**
   - Initializes empty ports list
   - Loads port data from JSON file
   - Sets up the calculator

2. **`_load_ports(self)`**
   - Loads port database from `data/ports.json`
   - Creates `Port` objects for each port
   - Handles file loading errors gracefully

3. **`search_ports(self, query: str, limit: int = 10)`**
   - Searches ports by name, country, or region
   - Returns list of matching `Port` objects
   - Case-insensitive search
   - Limited to specified number of results

4. **`calculate_distance(self, origin_lon, origin_lat, dest_lon, dest_lat)`**
   - Calculates maritime distance between two coordinates
   - Uses Python SeaRoute wrapper (`sr.searoute()`)
   - Returns distance in both km and nautical miles
   - Includes debug logging and fallback calculations

### 🎨 Streamlit UI Components

#### Main Application Structure
```python
# Page configuration
st.set_page_config(
    page_title="SeaRoute Maritime Distance Calculator",
    page_icon="🌊",
    layout="wide"
)

# Initialize calculator
calculator = SeaRouteCalculator()

# Three main tabs
tab1, tab2, tab3 = st.tabs(["🚢 Port-to-Port", "📍 Coordinates", "🔍 Port Search"])
```

#### Tab 1: Port-to-Port Calculation
- **Origin Port Selection**: Dropdown with all ports
- **Destination Port Selection**: Dropdown with all ports
- **Distance Calculation**: Button to calculate maritime distance
- **Results Display**: Shows distance in nm and km

#### Tab 2: Coordinate-Based Calculation
- **Coordinate Input**: Number inputs for lat/lon
- **Distance Calculation**: Direct coordinate-based calculation
- **Results Display**: Same format as port-to-port

#### Tab 3: Port Search
- **Search Input**: Text input for port search
- **Results Table**: Dataframe showing matching ports
- **Port Details**: Name, country, region, coordinates

## 🔧 Technical Details

### Dependencies
- **Streamlit**: Web application framework
- **searoute**: Python wrapper for maritime routing
- **json**: For loading port data
- **dataclasses**: For clean data structures
- **typing**: For type hints

### Data Flow
1. **App Startup**: Load port data from JSON
2. **User Input**: Select ports or enter coordinates
3. **Calculation**: Use SeaRoute wrapper for distance
4. **Result Display**: Show distance in multiple units

### Error Handling
- **File Loading**: Graceful handling of missing files
- **SeaRoute Errors**: Debug logging and fallback calculations
- **User Input**: Validation and error messages

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- pip

### Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd searoute-master
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the Streamlit application**
   ```bash
   streamlit run src/app.py
   ```

4. **Open your browser**
   ```
   http://localhost:8501
   ```

## 🌊 Usage Guide

### Port-to-Port Calculation
1. Go to the **Port-to-Port** tab
2. Select origin port from dropdown
3. Select destination port from dropdown
4. Click **Calculate Distance**
5. View results in nautical miles and kilometers

### Coordinate Calculation
1. Go to the **Coordinates** tab
2. Enter origin longitude and latitude
3. Enter destination longitude and latitude
4. Click **Calculate Distance**
5. View maritime distance results

### Port Search
1. Go to the **Port Search** tab
2. Enter search terms (name, country, region)
3. Browse the results table
4. View port details and coordinates

## 📊 Port Database

The application includes **3,800+ ports** worldwide with:
- Port names and alternate names
- Country and region information
- Precise coordinates (longitude/latitude)
- Search functionality

### Port Data Format
```json
{
  "name": "Hamburg",
  "country": "Germany",
  "region": "Europe",
  "lon": 9.9937,
  "lat": 53.5511,
  "alternate": "Hamburg Port"
}
```

## 🔍 Example Calculations

- **Hamburg → Shanghai**: ~8,500 nm (~15,700 km)
- **Rotterdam → Singapore**: ~6,200 nm (~11,500 km)
- **New York → London**: ~3,000 nm (~5,600 km)

## 🎯 EU-ETS Extension

This application provides the foundation for the **CE492 EU-ETS Maritime Compliance Cost Estimator** project. The maritime distance calculation is the core component for:

- **Method A: MRV-Intensity Estimator**
- **Method B: Fuel Consumption Estimator**
- **EU-ETS Coverage Rules**
- **Phase-in Schedules**
- **Cost Calculations**

## 🚀 Deployment

### Local Development
```bash
streamlit run src/app.py
```

### Streamlit Cloud
1. Push your code to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub repository
4. Set main file to `src/app.py`
5. Deploy!

### Other Cloud Platforms
The app is ready for deployment on:
- **Heroku** - Add `Procfile` with `web: streamlit run src/app.py --server.port=$PORT --server.address=0.0.0.0`
- **Railway** - Automatic detection
- **DigitalOcean** - App Platform

## 🐛 Debugging

### Common Issues
1. **SeaRoute 'length' error**: The app includes debug logging and fallback calculations
2. **Port loading issues**: Check if `data/ports.json` exists and is valid
3. **Dependencies**: Ensure all packages are installed with `pip install -r requirements.txt`

### Debug Features
- Console logging for SeaRoute results
- Error handling with fallback calculations
- File existence checks
- Data validation

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📞 Support

For questions or issues, please open an issue on GitHub.

---

**🌊 SeaRoute Maritime Distance Calculator** - Powered by Python SeaRoute wrapper