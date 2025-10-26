# Java SeaRoute

This directory contains the essential files for the Java SeaRoute implementation from Eurostat.

## Files

- **`searoute.jar`**: The main Java SeaRoute executable
- **`searoute.bat`**: Windows batch script to run SeaRoute
- **`searoute.sh`**: Linux/Unix shell script to run SeaRoute
- **`README.md`**: Original SeaRoute documentation

## Usage

### Command Line
```bash
# Windows
java -jar searoute.jar -h

# Linux/Unix
./searoute.sh -h
```

### Python Integration
The Java SeaRoute is integrated into the main application via `tools/java_searoute_wrapper.py`.

## Requirements

- Java 1.9 or higher
- The `marnet/` directory with maritime network database files

## Source

This is the official Java SeaRoute implementation from Eurostat:
https://github.com/eurostat/searoute

Only essential files are included here. The full source code and documentation can be found in the original repository.