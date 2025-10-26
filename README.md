# 🚢 EU ETS Maritime Distance Calculator

A simple web application for calculating maritime distances between ports worldwide using Java SeaRoute for accurate shipping routes.

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

```bash
cd server
python app.py
```

### Open in Browser

```
http://localhost:8080
```

## 💻 How to Use

1. **Search for Origin Port** - Type in the search box (e.g., "hamburg")
2. **Select from dropdown** - Click on the port you want
3. **Search for Destination Port** - Type in the search box (e.g., "shanghai")
4. **Select from dropdown** - Click on the port you want
5. **Calculate Distance** - Click the "Calculate Distance" button

## 📊 What You'll See

- **Distance**: In nautical miles and kilometers
- **Route Details**: Number of waypoints
- **ETS Coverage**: EU ETS coverage percentage
- **Accurate Routes**: Based on actual maritime shipping lanes

## 🎯 Features

- ✅ **13,951 ports worldwide** with search functionality
- ✅ **Java SeaRoute** for accurate maritime routing
- ✅ **ETS coverage calculation** (0%, 50%, or 100%)
- ✅ **Beautiful, responsive design**
- ✅ **Real-time port search** as you type
- ✅ **No external dependencies** - runs locally

## 🔧 Technical Details

### Distance Calculation

The application uses **Java SeaRoute** which provides accurate distances based on actual maritime shipping routes, not straight-line distances.

### Requirements

- Python 3.8+
- Java (for SeaRoute routing)
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

