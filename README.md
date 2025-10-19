# EU ETS Maritime Compliance Cost Estimator

An open-source EU Emissions Trading System (ETS) cost estimator for maritime voyages, implementing **Method A: MRV-Intensity Estimator** as part of the CE492 Undergraduate Thesis Project at Boğaziçi University.

## 📁 Project Structure

```
searoute-master/
├── src/
│   └── app.py                    # Main Streamlit application
├── data/
│   ├── ports.json               # Port database (3,800+ ports)
│   ├── mrv_data.csv             # MRV ship emissions data
│   └── ets_price.csv            # EUA price data by year
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

   - Calculates maritime distance using SeaRoute wrapper
   - Returns distance in both km and nautical miles
   - Includes debug logging and fallback calculations
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

## 🔧 Technical Details

### Dependencies

- **Streamlit**: Web application framework
- **searoute**: Python wrapper for maritime routing
- **pandas**: Data manipulation and CSV processing
- **json**: For loading port data
- **dataclasses**: For clean data structures
- **typing**: For type hints
- **os**: File path resolution and data loading

### Data Flow (Method A: MRV-Intensity Estimator)

1. **App Startup**: Load ports, MRV ships, and ETS prices data
2. **User Input**: Enter IMO number and select ports
3. **MRV Lookup**: Find ship emissions data from MRV database
4. **Distance Calculation**: Use SeaRoute wrapper for maritime distance
5. **Emission Calculation**: Apply MRV intensity data to distance
6. **ETS Cost Calculation**: Apply coverage rules, phase-in schedules, and EUA prices
7. **Result Display**: Show emissions, costs by year, and coverage analysis

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
The application includes **3,800+ ports** worldwide with:
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
  "country": "Germany",
  "region": "Europe",
  "lon": 9.9937,
  "lat": 53.5511,
  "alternate": "Hamburg Port"
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

### Distance Examples
- **Hamburg → Shanghai**: ~8,500 nm (~15,700 km)
- **Rotterdam → Singapore**: ~6,200 nm (~11,500 km)
- **New York → London**: ~3,000 nm (~5,600 km)

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

**🇪🇺 EU ETS Maritime Compliance Cost Estimator** - Method A Implementation for CE492 Project
