# 🌊 SeaRoute Web Interface - User Guide

## 🎯 **Perfect! I've Created a Beautiful Web Interface for You!**

No more Java commands needed! You now have a user-friendly web interface to calculate maritime distances between ports.

## 🚀 **How to Use the Web Interface**

### **Step 1: Start the Web Server**

**Option A: Double-click the batch file**
```
start_web_interface.bat
```

**Option B: Run PowerShell script**
```powershell
.\start_web_interface.ps1
```

**Option C: Manual start**
```bash
python searoute_server.py
```

### **Step 2: Open Your Browser**
- Go to: **http://localhost:8080**
- The beautiful interface will load automatically

### **Step 3: Calculate Distances**
1. **Select Origin Port** from the dropdown menu
2. **Select Destination Port** from the dropdown menu
3. **Click "Calculate Maritime Distance"**
4. **View Results** instantly!

## 🎨 **Interface Features**

### **📋 Pre-loaded Major Ports**
- Marseille, France
- Shanghai, China  
- New York, USA
- Los Angeles, USA
- Singapore
- Rotterdam, Netherlands
- Hamburg, Germany
- Tokyo, Japan
- Hong Kong
- Dubai, UAE
- Santos, Brazil
- Sydney, Australia

### **📍 Custom Coordinates**
- Enter any longitude/latitude coordinates
- Supports decimal degrees format
- Auto-fills when you select ports

### **📊 Results Display**
- **Maritime Distance** in kilometers
- **Origin Approximation** (accuracy to network)
- **Destination Approximation** (accuracy to network)
- **Route Name** for reference

## 🔧 **Technical Details**

### **What Happens Behind the Scenes**
1. You select ports or enter coordinates
2. Web interface sends data to Python server
3. Python creates temporary CSV file
4. Calls SeaRoute Java application
5. Processes maritime network (20km resolution)
6. Returns distance and route information
7. Displays results in beautiful format

### **Performance**
- **Processing Time**: 2-5 seconds per calculation
- **Resolution**: 20km (good balance of speed/accuracy)
- **Network**: Uses actual shipping lanes
- **Canals**: Includes Panama, Suez, and other major passages

## 📁 **Files Created**

### **Web Interface Files**
- `port_calculator.html` - Beautiful web interface
- `searoute_server.py` - Python backend server
- `start_web_interface.bat` - Windows batch launcher
- `start_web_interface.ps1` - PowerShell launcher

### **Requirements**
- ✅ **Java 25** (already installed and working)
- ✅ **Python 3.13** (already installed and working)
- ✅ **SeaRoute JAR** (already available)

## 🎯 **Example Usage**

### **Quick Test**
1. Start server: `start_web_interface.bat`
2. Open browser: http://localhost:8080
3. Select: Marseille → Shanghai
4. Click: "Calculate Maritime Distance"
5. Result: **16,376.9 km** maritime distance

### **Custom Coordinates**
1. Enter custom longitude/latitude
2. Click calculate
3. Get instant maritime distance

## 🛠️ **Troubleshooting**

### **Server Won't Start**
- Ensure Java is installed: `java --version`
- Ensure Python is installed: `python --version`
- Run from project root directory

### **Browser Shows Error**
- Check server is running (should show "Starting web server...")
- Try: http://127.0.0.1:8080 instead
- Check firewall settings

### **Calculation Fails**
- Ensure SeaRoute JAR exists in correct location
- Check Java PATH is set correctly
- Try restarting the server

## 🎉 **You're All Set!**

**The web interface is ready to use!** 

- **Beautiful, modern design**
- **Easy port selection**
- **Custom coordinate input**
- **Instant results**
- **No Java knowledge required**

Just run `start_web_interface.bat` and start calculating maritime distances between any ports worldwide!
