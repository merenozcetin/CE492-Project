# 🌊 SeaRoute Maritime Distance Calculator

**Calculate maritime distances between ports worldwide with a standalone Python application!**

## 📁 Project Structure

```
searoute-master/
├── 📖 README.md                    # This file
├── 📄 LICENSE                      # Project license
├── 🐍 searoute_calculator.py       # Main standalone calculator
├── 📋 CE492_Project_Description[1].md  # Project requirements
├── 🌐 web-interface/               # Port database
│   └── port_calculator.html        # Port database (3,800+ ports)
└── ☕ searoute-engine/              # SeaRoute calculation engine
    ├── searoute.jar                # Core Java engine
    ├── single_test.csv             # Single route template
    ├── test_input.csv               # Sample routes
    └── marnet/                      # Maritime network data
        ├── marnet_plus_5km.gpkg
        ├── marnet_plus_10km.gpkg
        ├── marnet_plus_20km.gpkg
        ├── marnet_plus_50km.gpkg
        └── marnet_plus_100km.gpkg
```

## 🚀 Quick Start

1. **Run the calculator:**
   ```bash
   python searoute_calculator.py
   ```

2. **Search for ports:**
   ```
   > search hamburg
   > search shanghai
   ```

3. **Calculate distance:**
   ```
   > calculate
   Enter origin port: hamburg
   Enter destination port: shanghai
   ```

4. **Use coordinates:**
   ```
   > coordinates
   Enter origin longitude: 9.99
   Enter origin latitude: 53.55
   Enter destination longitude: 121.8
   Enter destination latitude: 31.2
   ```

## ✨ Features

- **🌍 3,800+ Ports Worldwide** with comprehensive database
- **📍 Custom Coordinates** support for any location
- **🚢 Real Maritime Routing** (uses actual shipping lanes)
- **📊 Results in Nautical Miles** (proper maritime unit)
- **🔍 Smart Port Search** by name, country, or region
- **⚡ Fast Calculations** using Eurostat's SeaRoute engine
- **🎯 Interactive Interface** with helpful commands

## 🔧 Requirements

- **Java JDK 9+** (for SeaRoute engine)
- **Python 3.6+** (for the calculator)
- **Modern terminal** (Windows PowerShell, Command Prompt, or Linux/Mac terminal)

## 📊 Example Results

**Hamburg → Shanghai:**
- Maritime Distance: **8,842.8 nm** (16,376.9 km)
- Origin Approximation: 0.72 km
- Destination Approximation: 30.43 km

## 🎯 Available Commands

- `search <query>` - Search for ports
- `calculate` - Calculate distance between two ports
- `coordinates` - Calculate using longitude/latitude
- `list <country>` - List ports in a country
- `help` - Show all commands
- `quit` - Exit the program

## 🆘 Troubleshooting

### Java Not Found
If you get "Java not found" error:
1. **Install Java JDK 9+** from [Oracle](https://www.oracle.com/java/technologies/downloads/) or [OpenJDK](https://openjdk.org/)
2. **Add Java to PATH** environment variable
3. **Or run:** `$env:PATH += ";C:\Program Files\Java\jdk-XX\bin"` (Windows)

### Port Database Issues
- Ensure `web-interface/port_calculator.html` exists
- The script automatically loads ports from this file

### SeaRoute Engine Issues
- Ensure `searoute-engine/searoute.jar` exists
- Check that Java can run the JAR file

## 🌊 About SeaRoute

This calculator uses **Eurostat's SeaRoute** - the official maritime routing engine that:
- ✅ **Follows actual shipping lanes** (not straight lines)
- ✅ **Includes major canals** (Panama, Suez, etc.)
- ✅ **Accounts for land masses** and navigation constraints
- ✅ **Provides accurate distances** for maritime planning

## 🎓 CE492 Project

This is part of the **CE492 EU-ETS Maritime Compliance Cost Estimator** project at Boğaziçi University. The standalone calculator provides the foundation for maritime distance calculations that will be extended with EU-ETS compliance cost estimation features.

## 📄 License

This project is licensed under the same terms as the original SeaRoute project.

---

**Ready to calculate maritime distances? Just run `python searoute_calculator.py` and start exploring!** 🚢