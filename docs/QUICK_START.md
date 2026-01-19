# 🚀 Quick Start Guide

## Installation (30 seconds)

```bash
pip install -r requirements.txt
```

## Running the App

```bash
cd server
python app.py
```

## Access the Web Interface

**Local:**
```
http://localhost:8080
```

**Production (Live):**
```
https://ce492-project-production.up.railway.app/
```

## How to Use

1. **Search for Origin Port** - Type in the search box (e.g., "hamburg")
2. **Select from dropdown** - Click on the port you want
3. **Search for Destination Port** - Type in the search box (e.g., "shanghai")
4. **Select from dropdown** - Click on the port you want
5. **Calculate Distance** - Click the "Calculate Distance" button

## What You'll See

### Maritime Routes
- **Distance**: In nautical miles and kilometers using Java SeaRoute
- **Route Complexity**: Number of waypoints in the route
- **ETS Coverage**: EU ETS coverage percentage
- **Accurate Routes**: Based on actual maritime shipping lanes

### Road Routes
- **Distance**: In kilometers and miles
- **Duration**: Estimated driving time (hours and minutes)
- **Route**: Based on actual road networks via OpenRouteService

## Example Tests

### Maritime: Hamburg → Shanghai
- Java SeaRoute: ~10,920 nm (~20,225 km)
- Route complexity: 45 waypoints
- ETS Coverage: 50% (Mixed route)

### Road: Ankara → İzmir
- Distance: ~520 km (~323 miles)
- Duration: ~5h 12m
- Route: Via OpenRouteService driving profile

## Troubleshooting

### Port search not working?
Make sure `server/data/ports.json` exists (it should, there are 13,951 ports!)

### Java SeaRoute not working?
Install Java: https://www.java.com/download/
The app requires Java to calculate accurate shipping routes.

### Port 8080 in use?
Edit `server/app.py`, find `PORT = 8080`, change to another port like `8081`

## Requirements

- Python 3.8+
- Java (for SeaRoute maritime routing)
- OpenRouteService library (for road routing)
- Pandas (for data processing)

---

**That's it!** Simple and straightforward. 🚢