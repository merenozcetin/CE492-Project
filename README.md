# 🌊 SeaRoute Web Interface

**Calculate maritime distances between ports worldwide with a beautiful web interface!**

## 📁 Project Structure

```
searoute-master/
├── 📖 README.md                    # This file
├── 📄 LICENSE                      # Project license
├── 🌐 web-interface/               # Web application files
│   ├── port_calculator.html        # Beautiful HTML interface
│   └── searoute_server.py          # Python backend server
├── 🚀 scripts/                     # Launcher scripts
│   ├── start_web_interface.bat     # Windows launcher
│   └── start_web_interface.ps1     # PowerShell launcher
├── ☕ searoute-engine/              # SeaRoute calculation engine
│   ├── searoute.jar                # Core Java engine
│   ├── single_test.csv             # Single route template
│   ├── test_input.csv               # Sample routes
│   └── marnet/                      # Maritime network data
│       ├── marnet_plus_5km.gpkg
│       ├── marnet_plus_10km.gpkg
│       ├── marnet_plus_20km.gpkg
│       ├── marnet_plus_50km.gpkg
│       └── marnet_plus_100km.gpkg
└── 📚 docs/                         # Documentation
    ├── SETUP_GUIDE.md              # Detailed setup instructions
    ├── WEB_INTERFACE_GUIDE.md      # Web interface user guide
    └── FINAL_CLEANUP_SUMMARY.md    # Project cleanup summary
```

## 🚀 Quick Start

1. **Start the web server:**
   ```bash
   scripts\start_web_interface.bat
   ```

2. **Open your browser:**
   ```
   http://localhost:8080
   ```

3. **Calculate distances:**
   - Select origin and destination ports
   - Or enter custom coordinates
   - Click "Calculate Maritime Distance"
   - See results instantly!

## ✨ Features

- **🌍 12 Major World Ports** pre-loaded
- **📍 Custom Coordinates** support
- **🚢 Real Maritime Routing** (uses actual shipping lanes)
- **📊 Instant Results** with distance and accuracy info
- **📱 Mobile-Friendly** responsive design
- **🎨 Beautiful Interface** with modern design

## 🔧 Requirements

- **Java JDK 9+** (for SeaRoute engine)
- **Python 3.6+** (for web server)
- **Modern web browser** (Chrome, Firefox, Edge, Safari)

## 📊 Example Results

**Marseille → Shanghai:**
- Maritime Distance: **16,376.9 km**
- Origin Approximation: 0.72 km
- Destination Approximation: 30.43 km

## 🎯 What's Included

- ✅ **Organized folder structure** - Everything in logical folders
- ✅ **Working web interface** - No Java knowledge needed
- ✅ **Pre-loaded major ports** - 12 world ports ready to use
- ✅ **Custom coordinates** - Enter any longitude/latitude
- ✅ **Real maritime routing** - Uses actual shipping lanes, not straight lines
- ✅ **Canal support** - Includes Panama, Suez, and other major passages
- ✅ **Mobile responsive** - Works on phones and tablets
- ✅ **Error handling** - Helpful error messages and troubleshooting

## 🆘 Need Help?

- **Setup Issues**: See `docs/SETUP_GUIDE.md`
- **Web Interface**: See `docs/WEB_INTERFACE_GUIDE.md`
- **Server Won't Start**: Check Java and Python installation
- **Browser Issues**: Try http://127.0.0.1:8080

---

**Ready to calculate maritime distances? Just run `scripts\start_web_interface.bat` and start exploring!** 🚢