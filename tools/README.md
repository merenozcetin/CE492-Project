# Tools Directory

This directory contains utility scripts and tools for the EU ETS Maritime Compliance Cost Estimator.

## Files

### `java_searoute_wrapper.py`
Python wrapper for the Java SeaRoute implementation. Provides accurate maritime distance calculations using actual shipping routes.

**Usage:**
```python
from java_searoute_wrapper import JavaSeaRouteWrapper

wrapper = JavaSeaRouteWrapper()
result = wrapper.calculate_distance(origin_lon, origin_lat, dest_lon, dest_lat)
```

### `distance_comparison.py`
Tool to compare distance calculations between Java SeaRoute and Python wrapper. Demonstrates the accuracy improvements.

**Usage:**
```bash
python distance_comparison.py
```

## Java SeaRoute Integration

The Java SeaRoute implementation provides significantly more accurate maritime distance calculations:

- **Hamburg → Shanghai**: 10,920 nm (vs 4,613 nm great circle) - **137% more accurate**
- **Marseille → Shanghai**: 8,843 nm (vs 5,137 nm great circle) - **72% more accurate**
- **New York → Los Angeles**: 4,976 nm (vs 2,132 nm great circle) - **133% more accurate**
- **Rotterdam → Singapore**: 8,451 nm (vs 5,687 nm great circle) - **49% more accurate**

## Requirements

- Java 1.9 or higher
- Python 3.8+
- pandas
- The `marnet/` directory with maritime network database files
