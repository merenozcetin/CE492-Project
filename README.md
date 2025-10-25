# 🇪🇺 EU ETS Maritime Compliance Cost Estimator

An open-source EU Emissions Trading System (ETS) cost estimator for maritime voyages, implementing **Method A: MRV-Intensity Estimator** as part of the CE492 Undergraduate Thesis Project at Boğaziçi University.

## 📁 Project Structure

```
searoute-master/
├── src/
│   └── app.py                    # Main Streamlit application
├── data/
│   ├── ports.json               # Port database (13,951 ports)
│   ├── mrv_data.csv             # MRV ship emissions data
│   └── ets_price.csv            # EUA price data by year
├── tools/
│   ├── java_searoute_wrapper.py # Java SeaRoute Python wrapper
│   ├── distance_comparison.py   # Distance accuracy comparison tool
│   └── README.md                # Tools documentation
├── java-searoute/
│   ├── searoute.jar             # Java SeaRoute executable
│   ├── searoute.bat             # Windows batch script
│   ├── searoute.sh              # Linux/Unix shell script
│   └── README.md                # Java SeaRoute documentation
├── marnet/
│   └── *.gpkg                   # Maritime network database files
├── requirements.txt              # Python dependencies
├── LICENSE                       # MIT License
├── .gitignore                    # Git ignore rules
└── README.md                     # This file
```

## 🏗️ Code Architecture

### 📋 Data Classes

#### `Port` Class
```python
@dataclass
class Port:
    """Port information with EEA status"""
    name: str          # Port name (e.g., "Hamburg")
    country: str       # Country (e.g., "Germany")
    region: str        # Region (e.g., "Europe")
    lon: float         # Longitude coordinate
    lat: float         # Latitude coordinate
    alternate: Optional[str] = None  # Alternate port name
    is_eea: bool       # EEA membership status for EU-ETS coverage
```

#### `MRVShip` Class
```python
@dataclass
class MRVShip:
    """MRV ship emissions data"""
    imo_number: str    # IMO ship identification number
    co2_per_nm: float  # CO₂ emissions per nautical mile (kg/nm)
    co2eq_per_nm: float # CO₂ equivalent emissions per nautical mile (kg/nm)
```

#### `ETSPrices` Class
```python
@dataclass
class ETSPrices:
    """EUA price data by year"""
    year: int          # Year (2024-2030)
    price_eur: float   # Average EUA price in EUR per tonne
```

#### `EmissionResult` Class
```python
@dataclass
class EmissionResult:
    """Complete emission calculation result"""
    imo_number: str    # Ship IMO number
    ship_name: str     # Ship name (if available)
    distance_nm: float # Route distance in nautical miles
    co2_emissions: float    # CO₂ emissions (tonnes)
    co2eq_emissions: float  # CO₂ equivalent emissions (tonnes)
    ets_costs: Dict[int, float]  # ETS costs by year (EUR)
```

### 🧮 Core Calculator Class

#### `SeaRouteCalculator` Class
The main calculator class that implements **Method A: MRV-Intensity Estimator** for EU-ETS compliance cost calculation.

**Key Methods:**

1. **`__init__(self)`**
   - Initializes ports, MRV ships, and ETS prices lists
   - Loads all required data files
   - Sets up the calculator for EU-ETS calculations

2. **`_load_ports(self)`**
   - Loads port database from `data/ports.json`
   - Creates `Port` objects with EEA status
   - Handles file loading errors gracefully

3. **`_load_mrv_data(self)`**
   - Loads MRV ship emissions data from `data/mrv_data.csv`
   - Creates `MRVShip` objects with CO₂ and CO₂eq per nautical mile
   - Handles BOM encoding and data validation

4. **`_load_ets_prices(self)`**
   - Loads EUA price data from `data/ets_price.csv`
   - Creates `ETSPrices` objects for cost calculations
   - Supports historical and projected prices

5. **`calculate_distance(self, origin_lon, origin_lat, dest_lon, dest_lat)`**
   - **Primary**: Uses Java SeaRoute for accurate maritime routing with actual shipping routes
   - **Fallback 1**: Python SeaRoute wrapper if Java SeaRoute unavailable
   - **Fallback 2**: Great circle distance calculation as final fallback
   - Returns distance in both km and nautical miles with route complexity information
   - **Accuracy**: 48-137% more accurate than great circle distances

6. **`calculate_emissions(self, imo_number, origin_port, dest_port)`**
   - **Core Method A implementation**: MRV-intensity estimator
   - Calculates CO₂ and CO₂eq emissions based on MRV data
   - Applies EU-ETS coverage rules (100%/50%/0%)
   - Calculates ETS costs with phase-in schedules
   - Returns complete `EmissionResult` object

7. **`_calculate_ets_costs(self, co2_emissions, co2eq_emissions, origin_port, dest_port)`**
   - Applies EU-ETS policy rules:
     - **Coverage**: 100% intra-EEA, 50% extra-EEA, 0% out-of-scope
     - **Phase-in**: 40% (2024), 70% (2025), 100% (2026+)
     - **Emission types**: CO₂ (2024-2025), CO₂eq (2026+)
   - Returns ETS costs by year in EUR

### 🎨 Streamlit UI Components

#### Main Application Structure
```python
# Page configuration
st.set_page_config(
    page_title="ETS Price Calculator",
    page_icon="🇪🇺",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize calculator
calculator = SeaRouteCalculator()

# Two main tabs for EU-ETS calculations
tab1, tab2 = st.tabs(["🚢 MRV Emissions", "📍 Port-to-Port"])
```

#### Tab 1: MRV Emissions (Method A Implementation)
- **IMO Number Input**: Ship identification for MRV data lookup
- **Ship Data Display**: CO₂ and CO₂eq per nautical mile from MRV database
- **Port Selection**: Origin and destination port dropdowns
- **Emission Calculation**: Complete EU-ETS compliance cost calculation
- **Results Display**: 
  - Route distance and emissions (CO₂/CO₂eq)
  - ETS costs by year with phase-in schedules
  - Coverage analysis (intra-EEA/extra-EEA/out-of-scope)
  - Cost projection from 2024 to 2030

#### Tab 2: Port-to-Port Distance
- **Port Selection**: Origin and destination port dropdowns
- **Distance Calculation**: Maritime distance calculation
- **Results Display**: Distance in nautical miles and kilometers

## 🚢 Java SeaRoute Integration

### Why Java SeaRoute?

The application now uses **Java SeaRoute** (Eurostat's official implementation) instead of the Python wrapper for maritime distance calculations. This provides **significantly more accurate** distances that match real-world shipping routes.

### Accuracy Comparison

| Route | Java SeaRoute (Actual) | Python Wrapper (Great Circle) | Accuracy Improvement |
|-------|----------------------|------------------------------|---------------------|
| Hamburg → Shanghai | 10,920 nm | 4,613 nm | **+137%** |
| Marseille → Shanghai | 8,843 nm | 5,137 nm | **+72%** |
| New York → Los Angeles | 4,976 nm | 2,132 nm | **+133%** |
| Rotterdam → Singapore | 8,451 nm | 5,687 nm | **+49%** |

### How It Works

1. **Java SeaRoute**: Uses actual maritime network with shipping lanes, canals, and straits
2. **Python Wrapper**: Falls back to great circle distances (straight-line)
3. **Great Circle**: Final fallback for mathematical distance calculation

### Technical Implementation

- **Primary Method**: Java SeaRoute via subprocess calls
- **Fallback System**: Automatic fallback if Java SeaRoute fails
- **Route Complexity**: Shows number of waypoints for actual routes
- **Method Display**: UI shows which calculation method was used

## 🔧 Technical Details

### Dependencies

- **Streamlit**: Web application framework
- **searoute**: Python wrapper for maritime routing (fallback)
- **Java SeaRoute**: Eurostat's Java implementation for accurate maritime routing (primary)
- **pandas**: Data manipulation and CSV processing
- **json**: For loading port data
- **dataclasses**: For clean data structures
- **typing**: For type hints
- **os**: File path resolution and data loading
- **subprocess**: For Java SeaRoute integration
- **tempfile**: For temporary file management

### Data Flow (Method A: MRV-Intensity Estimator)

1. **App Startup**: Load ports, MRV ships, and ETS prices data
2. **User Input**: Enter IMO number and select ports
3. **MRV Lookup**: Find ship emissions data from MRV database
4. **Distance Calculation**: Use Java SeaRoute for accurate maritime distance (with fallbacks)
5. **Emission Calculation**: Apply MRV intensity data to distance
6. **ETS Cost Calculation**: Apply coverage rules, phase-in schedules, and EUA prices
7. **Result Display**: Show emissions, costs by year, and coverage analysis

### Error Handling

- **File Loading**: Graceful handling of missing files
- **SeaRoute Errors**: Debug logging and fallback calculations
- **User Input**: Validation and error messages
- **MRV Data**: BOM handling and data validation
- **Division by Zero**: Proper handling of edge cases

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

### MRV Emissions Calculation (Method A)
1. Go to the **MRV Emissions** tab
2. Enter ship IMO number (e.g., "1234567")
3. Select origin port from dropdown
4. Select destination port from dropdown
5. Click **Calculate MRV Emissions**
6. View results:
   - Ship emissions data (CO₂/CO₂eq per nm)
   - Route distance and total emissions
   - ETS costs by year (2024-2030)
   - Coverage analysis and cost projections

### Port-to-Port Distance Calculation
1. Go to the **Port-to-Port** tab
2. Select origin port from dropdown
3. Select destination port from dropdown
4. Click **Calculate Distance**
5. View maritime distance in nautical miles and kilometers

## 📊 Data Sources

### Port Database
The application includes **13,951 ports** worldwide with:
- Port names and alternate names
- Country and region information
- Precise coordinates (longitude/latitude)
- EEA membership status for EU-ETS coverage

### MRV Ship Database
- **Source**: THETIS-MRV (EMSA) public database
- **Content**: Verified ship emissions data by IMO number
- **Fields**: CO₂ and CO₂eq emissions per nautical mile
- **Coverage**: Ships operating in EU waters

### EUA Price Data
- **Source**: Sandbag Carbon Price Viewer, TradingEconomics
- **Content**: Historical and projected EUA prices by year
- **Period**: 2024-2030
- **Currency**: EUR per tonne CO₂/CO₂eq

### Port Data Format
```json
{
  "name": "Hamburg",
  "country": "DE",
  "region": "Europe",
  "lon": 9.9937,
  "lat": 53.5511,
  "alternate": null,
  "is_eea": true
}
```

## 🔍 Example Calculations

### MRV Emissions Examples
- **Container Ship (IMO: 1234567)**: Hamburg → Shanghai
  - Distance: ~8,500 nm
  - CO₂ emissions: ~850 tonnes
  - ETS costs 2024: €22,000 (40% phase-in)
  - ETS costs 2030: €120,000 (100% phase-in)

- **Bulk Carrier (IMO: 9876543)**: Rotterdam → Singapore
  - Distance: ~6,200 nm
  - CO₂eq emissions: ~620 tonnes
  - Coverage: 50% (extra-EEA route)
  - ETS costs 2024: €8,000 (40% phase-in)

### Distance Examples (Java SeaRoute - Actual Shipping Routes)
- **Hamburg → Shanghai**: ~10,920 nm (~20,225 km) - *137% more accurate than great circle*
- **Rotterdam → Singapore**: ~8,451 nm (~15,651 km) - *49% more accurate than great circle*
- **New York → Los Angeles**: ~4,976 nm (~9,216 km) - *133% more accurate than great circle*
- **Marseille → Shanghai**: ~8,843 nm (~16,377 km) - *72% more accurate than great circle*

## 🎯 CE492 Project Implementation

This application implements **Method A: MRV-Intensity Estimator** from the CE492 Undergraduate Thesis Project at Boğaziçi University. The implementation includes:

### ✅ Implemented Features
- **Method A: MRV-Intensity Estimator** - Complete implementation using THETIS-MRV data
- **EU-ETS Coverage Rules** - 100% intra-EEA, 50% extra-EEA, 0% out-of-scope
- **Phase-in Schedules** - 40% (2024), 70% (2025), 100% (2026+)
- **Emission Types** - CO₂ (2024-2025), CO₂eq (2026+)
- **Cost Calculations** - Complete ETS cost estimation by year
- **Policy-Accurate Implementation** - Following EU Commission regulations

### 🔮 Future Extensions (Method B)
- **Method B: Engineering-Lite Estimator** - Using EPA Marine Emissions Tools
- **AIS Data Integration** - Optional enhancement for real-time tracking
- **CH4/N2O Accounting** - Ready for 2026+ regulatory requirements

## 🛠️ Development Guide

### Setup Development Environment

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd searoute-master
   ```

2. **Create virtual environment (recommended)**
   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**
   ```bash
   streamlit run src/app.py
   ```

### Development Workflow

#### Making Changes
1. **Edit the main application**
   - Modify `src/app.py` for UI changes
   - Update port data in `data/ports.json`
   - Add new features or calculations

2. **Test your changes**
   ```bash
   streamlit run src/app.py
   ```

3. **Commit your changes**
   ```bash
   git add .
   git commit -m "Description of changes"
   git push origin master
   ```

### Code Organization

#### Main Application (`src/app.py`)
- **Data Classes**: `Port`, `MRVShip`, `ETSPrices`, `EmissionResult` dataclasses
- **Calculator Class**: `SeaRouteCalculator` for EU-ETS calculations
- **UI Components**: Streamlit interface with tabs and forms
- **Error Handling**: Graceful error handling and user feedback

#### Data Files (`data/`)
- **Port Database**: JSON file with port information and EEA status
- **MRV Data**: CSV file with ship emissions data
- **ETS Prices**: CSV file with EUA price projections
- **Format**: Standardized data structures for easy updates

## 🧪 Testing

### Manual Testing
1. **Port Loading**: Check if ports load correctly on startup
2. **MRV Data Loading**: Verify ship data loads from CSV
3. **Port Selection**: Test dropdown functionality
4. **Emission Calculation**: Test with known ship/port combinations
5. **ETS Cost Calculation**: Verify cost calculations by year
6. **Error Handling**: Test with invalid inputs

### Test Cases
- **MRV Emissions**: Test with valid IMO numbers
- **Distance Calculation**: Test with known port pairs
- **ETS Costs**: Verify phase-in schedules and coverage rules
- **Error Scenarios**: Test with missing data or invalid inputs

### Debug Features
- Console logging for SeaRoute results
- Error messages in UI
- Debug information in sidebar
- File existence and size checks

## 🐛 Debugging

### Common Issues

#### 1. Port Loading Errors
```python
# Check if file exists
if not os.path.exists('data/ports.json'):
    print("❌ Port data file not found!")
```

#### 2. MRV Data Loading Errors
```python
# Check CSV file and encoding
with open('data/mrv_data.csv', 'r', encoding='utf-8-sig') as f:
    # Handle BOM and data validation
```

#### 3. SeaRoute Calculation Errors
```python
# Debug SeaRoute result
print(f"Route result: {route}")
print(f"Route type: {type(route)}")
```

#### 4. Dependency Issues
```bash
# Check installed packages
pip list | grep streamlit
pip list | grep searoute
pip list | grep pandas
```

### Debug Tools
- **Console Output**: Print statements for debugging
- **Streamlit Debug**: Built-in error messages
- **File Validation**: Check data file integrity
- **Sidebar Debug Info**: Real-time status information

## 🚀 Deployment

### Local Development
```bash
streamlit run src/app.py
```

### Streamlit Cloud
1. Push to GitHub
2. Connect repository to Streamlit Cloud
3. Set main file to `src/app.py`
4. Deploy automatically

### Other Platforms
- **Heroku**: Add Procfile with `web: streamlit run src/app.py --server.port=$PORT --server.address=0.0.0.0`
- **Railway**: Automatic detection
- **DigitalOcean**: App Platform

## 📈 Performance Optimization

### Data Loading
- Ports loaded once at startup
- MRV data cached in memory
- ETS prices loaded once
- Efficient search through in-memory data

### UI Responsiveness
- Immediate user feedback
- Loading indicators for calculations
- Error handling with clear messages
- Theme-aware styling

### Calculation Efficiency
- SeaRoute wrapper optimization
- Fallback calculations for reliability
- Efficient EU-ETS cost calculations
- Cached results where possible

## 🔄 Version Control

### Git Workflow
1. **Feature Branch**: Create branch for new features
2. **Development**: Make changes and test
3. **Commit**: Commit with descriptive messages
4. **Push**: Push to remote repository
5. **Merge**: Merge to main branch

### Commit Messages
- Use descriptive commit messages
- Include issue numbers if applicable
- Follow conventional commit format
- Document major changes

## 📝 Code Style

### Python Style
- Follow PEP 8 guidelines
- Use type hints where possible
- Write docstrings for functions
- Use meaningful variable names

### Streamlit Best Practices
- Use columns for layout
- Provide user feedback
- Handle errors gracefully
- Keep UI responsive
- Theme-aware styling

## 🤝 Contributing

### Before Contributing
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

### Code Review Process
1. Automated checks pass
2. Manual code review
3. Testing verification
4. Documentation updates

## 📞 Support

### Getting Help
- Check the documentation first
- Look at existing issues
- Create a new issue if needed
- Provide detailed error information

### Reporting Issues
- Include error messages
- Describe steps to reproduce
- Provide system information
- Include relevant code snippets

---

**🇪🇺 EU ETS Maritime Compliance Cost Estimator** - Method A Implementation for CE492 Project