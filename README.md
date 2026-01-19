# 🚢 EU ETS Maritime & Road Distance Calculator

A web application for calculating maritime and road distances between ports/locations worldwide. Uses Java SeaRoute for accurate shipping routes and OpenRouteService for road routing.

## 📁 Project Structure

```
searoute-master/
├── server/                    # Main application
│   ├── app.py               # Web server (run this!)
│   ├── data/                # Data files
│   │   ├── ports.json      # 13,951 ports database
│   │   ├── mrv_data.csv    # Ship emissions data
│   │   └── ets_price.csv   # ETS price data
│   ├── tools/               # Helper scripts
│   │   └── java_searoute_wrapper.py
│   ├── java-searoute/       # Java SeaRoute executable
│   │   └── searoute.jar
│   └── marnet/             # Maritime network database
│       └── *.gpkg files
├── docs/                    # Documentation
│   ├── README.md           # This file
│   └── QUICK_START.md      # Quick setup guide
└── requirements.txt         # Python dependencies
```

## 🚀 Quick Start

### Installation

```bash
pip install -r requirements.txt
```

### Run the Application

**Option 1: Using the launcher (Easy)**
```bash
# Windows
start_server.bat

# Linux/Mac
./start_server.sh
```

**Option 2: Manual start**
```bash
cd server
python app.py
```

### Open in Browser

**Local:**
```
http://localhost:8080
```

**Production:**
```
https://ce492-project-production.up.railway.app/
```

## 💻 How to Use

1. **Search for Origin Port** - Type in the search box (e.g., "hamburg")
2. **Select from dropdown** - Click on the port you want
3. **Search for Destination Port** - Type in the search box (e.g., "shanghai")
4. **Select from dropdown** - Click on the port you want
5. **Calculate Distance** - Click the "Calculate Distance" button

## 📊 What You'll See

### Maritime Routes
- **Distance**: In nautical miles and kilometers
- **Route Details**: Number of waypoints
- **ETS Coverage**: EU ETS coverage percentage
- **Accurate Routes**: Based on actual maritime shipping lanes

### Road Routes
- **Distance**: In kilometers and miles
- **Duration**: Estimated driving time
- **Route**: Based on actual road networks via OpenRouteService

## 🎯 Features

### Maritime
- ✅ **13,951 ports worldwide** with search functionality
- ✅ **Java SeaRoute** for accurate maritime routing
- ✅ **ETS coverage calculation** (0%, 50%, or 100%)
- ✅ **Route visualization** on interactive maps

### Road
- ✅ **OpenRouteService integration** for road distance calculation
- ✅ **Geocoding support** - search by city/location name
- ✅ **Driving duration estimates** with hours and minutes
- ✅ **Road route visualization** on maps

### General
- ✅ **Beautiful, responsive design**
- ✅ **Real-time search** as you type
- ✅ **Multi-modal comparison** - compare sea vs road routes
- ✅ **RESTful API** for programmatic access

## 🔧 Technical Details

### Maritime Distance Calculation

The application uses **Java SeaRoute** which provides accurate distances based on actual maritime shipping routes, not straight-line distances.

### Road Distance Calculation

Road distances are calculated using **OpenRouteService**, which provides:
- Accurate driving distances based on actual road networks
- Estimated driving duration
- Route geometry for visualization

### Requirements

- Python 3.8+
- Java (for SeaRoute maritime routing)
- OpenRouteService Python library (for road routing)
- Pandas (for data processing)

### ETS Coverage

- **100%**: Intra-EEA routes (both ports in EEA)
- **50%**: Extra-EEA routes (one port in EEA, one outside)
- **0%**: Out-of-scope routes (both ports outside EEA)

## 🛠️ Troubleshooting

### Java SeaRoute not working?

Make sure Java is installed:
```bash
java -version
```

If Java is not available, install it from https://www.java.com/download/

### Port 8080 already in use?

Edit `server/app.py` and change the port number:
```python
PORT = 8081  # or any other available port
```

## 📚 Documentation

- See `docs/QUICK_START.md` for detailed setup instructions
- See `server/java-searoute/README.md` for Java SeaRoute information

## 📄 License

MIT License - See LICENSE file

---

**🚢 Happy Routing!** - Calculate accurate maritime distances between any two ports worldwide.

