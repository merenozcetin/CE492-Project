# SeaRoute Setup Guide for Port Distance Calculation

## ✅ Status: WORKING AND TESTED

**Last Updated**: October 17, 2025
**Tested With**: Java 25 (Oracle JDK)
**Test Route**: Marseille → Shanghai = **16,376.9 km**

## Prerequisites

### 1. Install Java JDK

SeaRoute requires Java 9 or higher. Follow these steps to install Java:

#### Option A: Oracle JDK (Recommended)

1. Go to [Oracle JDK Download Page](https://www.oracle.com/java/technologies/downloads/)
2. Download the latest JDK for Windows (x64)
3. Run the installer and follow the installation wizard
4. **Important**: Add Java to your system PATH:
   - Open System Properties → Advanced → Environment Variables
   - Add `C:\Program Files\Java\jdk-XX\bin` to your PATH variable
   - Replace XX with your Java version number
   - **Restart your command prompt/PowerShell after installation**

#### Option B: OpenJDK (Free Alternative)

1. Go to [Adoptium OpenJDK](https://adoptium.net/)
2. Download the latest LTS version for Windows x64
3. Run the installer and follow the installation wizard
4. The installer should automatically add Java to your PATH

### 2. Verify Installation

Open Command Prompt or PowerShell and run:

```bash
java --version
```

You should see output like:

```
java 25 2025-09-16 LTS
Java(TM) SE Runtime Environment (build 25+37-LTS-3491)
Java HotSpot(TM) 64-Bit Server VM (build 25+37-LTS-3491, mixed mode, sharing)
```

**If Java is not found**, try adding it manually to PATH for the current session:

```powershell
$env:PATH += ";C:\Program Files\Java\jdk-25\bin"
```

## Using SeaRoute

### 🚀 Quick Start (Tested & Working)

1. **Navigate to the SeaRoute directory:**

   ```bash
   cd modules\jar\release\searoute
   ```
2. **Run a test calculation:**

   ```bash
   java -jar searoute.jar -i single_test.csv -res 20 -panama 0
   ```
3. **This will create an `out.geojson` file with the calculated route.**

### 📊 Test Results (Verified Working)

- **Route**: Marseille (5.3°E, 43.3°N) → Shanghai (121.8°E, 31.2°N)
- **Maritime Distance**: **16,376.9 km**
- **Origin Approximation**: 0.72 km from nearest network node
- **Destination Approximation**: 30.43 km from nearest network node
- **Processing Time**: ~2-3 seconds for single route
- **Output Format**: GeoJSON (compatible with GIS software)

### Custom Port Distance Calculation

#### Method 1: Using CSV Input File (Recommended)

1. **Create a CSV file** with your port coordinates (see `port_distance_template.csv`)
2. **Run SeaRoute:**
   ```bash
   java -jar searoute.jar -i port_distance_template.csv -res 20 -panama 0
   ```

   **Note**: Don't specify `-o` parameter - it will create `out.geojson` by default

#### Method 2: Using Pre-made Templates

- **Single route**: Use `single_test.csv`
- **Multiple routes**: Use `major_ports_example.csv`
- **Custom template**: Use `port_distance_template.csv`

#### Method 3: Interactive Scripts

- **PowerShell**: `.\run_searoute.ps1` (Interactive menu)
- **Batch**: `run_searoute.bat` (Simple test)

### Command Line Options

- `-i` : Input CSV file
- `-o` : Output GeoJSON file (optional - defaults to `out.geojson`)
- `-res` : Resolution (5, 10, 20, 50, 100 km) - **20km recommended for speed**
- `-panama` : Avoid Panama Canal (0=use, 1=avoid)
- `-suez` : Avoid Suez Canal (0=use, 1=avoid)
- `-malacca` : Avoid Malacca Strait (0=use, 1=avoid)
- `-gibraltar` : Avoid Gibraltar Strait (0=use, 1=avoid)
- `-h` : Show help

### Output Information

The output GeoJSON file contains:

- `distKM`: Route distance in kilometers
- `dFromKM`: Distance from origin to nearest network node
- `dToKM`: Distance from destination to nearest network node
- `route name`: Name from your CSV file
- `geometry`: MultiLineString with the actual route coordinates

### 📁 Available Files

- `single_test.csv` - Single route template (Marseille-Shanghai)
- `major_ports_example.csv` - Multiple major world ports
- `port_distance_template.csv` - Blank template for custom routes
- `test_input.csv` - Original sample data (15 routes)
- `out.geojson` - Output file (created after running calculations)

## Example Ports

Here are coordinates for some major ports:

| Port        | Longitude | Latitude | Country     |
| ----------- | --------- | -------- | ----------- |
| Marseille   | 5.3       | 43.3     | France      |
| Shanghai    | 121.8     | 31.2     | China       |
| New York    | -74.1     | 40.7     | USA         |
| Los Angeles | -118.3    | 33.7     | USA         |
| Singapore   | 103.8     | 1.3      | Singapore   |
| Rotterdam   | 4.4       | 51.9     | Netherlands |
| Hamburg     | 9.9       | 53.5     | Germany     |
| Tokyo       | 139.7     | 35.7     | Japan       |
| Hong Kong   | 114.2     | 22.3     | Hong Kong   |
| Dubai       | 55.3      | 25.3     | UAE         |
| Santos      | -46.3     | -23.9    | Brazil      |
| Sydney      | 151.2     | -33.9    | Australia   |

## Performance Tips

### Resolution Settings

- **5km**: Highest accuracy, slowest processing (~10-30 seconds per route)
- **10km**: Good accuracy, moderate speed (~5-15 seconds per route)
- **20km**: **Recommended** - Good balance of speed and accuracy (~2-5 seconds per route)
- **50km**: Lower accuracy, faster processing (~1-3 seconds per route)
- **100km**: Lowest accuracy, fastest processing (~1 second per route)

### Batch Processing

For multiple routes, use CSV files instead of individual commands:

```bash
# Good: Process 10 routes at once
java -jar searoute.jar -i major_ports_example.csv -res 20 -panama 0

# Less efficient: Run 10 separate commands
```

## Troubleshooting

### Java Not Found

- **Ensure Java is installed and added to PATH**
- **Restart your command prompt/PowerShell after installation**
- **Try using full path to java.exe**
- **For current session only**: `$env:PATH += ";C:\Program Files\Java\jdk-25\bin"`

### File Not Found Errors

- **Ensure you're in the correct directory**: `cd modules\jar\release\searoute`
- **Check that searoute.jar exists** in the current directory
- **Verify input CSV file path is correct**
- **Use forward slashes or double backslashes in paths**

### Output File Issues

- **Don't specify `-o` parameter** - let it create `out.geojson` by default
- **Avoid complex output file paths** - use simple names like `output.geojson`
- **Check file permissions** - ensure you can write to the directory

### Performance Issues

- **Use higher resolution** (20km or 50km) for faster processing
- **Process routes in batches** using CSV files
- **Increase Java memory** if needed: `java -Xmx2g -jar searoute.jar [options]`

### Common Warnings (Normal)

- **"WARNING: A restricted method..."** - This is normal, ignore it
- **"WARNING: Use of the three-letter time zone ID..."** - This is normal, ignore it
- **"Could not find marnet as resource"** - This is normal, it finds the data automatically

### Getting Help

- **Run**: `java -jar searoute.jar -h` for command options
- **Check**: `QUICK_START.md` for quick reference
- **Use**: `.\run_searoute.ps1` for interactive help
