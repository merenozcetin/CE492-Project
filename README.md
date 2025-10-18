# 🌊 SeaRoute Maritime Distance Calculator

A clean, modern Streamlit web application for calculating maritime distances between ports worldwide using the Python SeaRoute wrapper.

## ✨ Features

- **🚢 Port-to-Port Calculation** - Search and select ports with autocomplete
- **📍 Coordinate Calculation** - Direct latitude/longitude input
- **🔍 Port Search** - Browse 2,948+ ports worldwide
- **📊 Distance Results** - Display in both kilometers and nautical miles
- **🎨 Modern UI** - Clean, responsive Streamlit interface
- **⚡ Fast** - Python-based, no Java dependencies

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
   streamlit run app.py
   ```

4. **Open your browser**
   ```
   http://localhost:8501
   ```

## 📁 Project Structure

```
searoute-master/
├── app.py                 # Main Streamlit application
├── requirements.txt        # Python dependencies
├── data/
│   └── ports.json        # Port database (2,948 ports)
└── README.md             # This file
```

## 🌊 Usage

### Port-to-Port Calculation
1. Go to the **Port-to-Port** tab
2. Search for your origin port (e.g., "hamburg")
3. Select from the dropdown
4. Search for your destination port (e.g., "shanghai")
5. Select from the dropdown
6. Click **Calculate Distance**

### Coordinate Calculation
1. Go to the **Coordinates** tab
2. Enter origin longitude and latitude
3. Enter destination longitude and latitude
4. Click **Calculate Distance**

### Port Search
1. Go to the **Port Search** tab
2. Enter search terms (name, country, region)
3. Browse the results

## 📦 Dependencies

- **Streamlit** - Web framework
- **searoute** - Python SeaRoute wrapper for maritime routing

## 🚀 Deployment

### Local Development
```bash
streamlit run app.py
```

### Streamlit Cloud
1. Push your code to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub repository
4. Set main file to `app.py`
5. Deploy!

### Other Cloud Platforms
The app is ready for deployment on:
- **Heroku** - Add `Procfile` with `web: streamlit run app.py --server.port=$PORT --server.address=0.0.0.0`
- **Railway** - Automatic detection
- **DigitalOcean** - App Platform

## 🎯 EU-ETS Extension

This application provides the foundation for the **CE492 EU-ETS Maritime Compliance Cost Estimator** project. The maritime distance calculation is the core component for:

- **Method A: MRV-Intensity Estimator**
- **Method B: Fuel Consumption Estimator**
- **EU-ETS Coverage Rules**
- **Phase-in Schedules**
- **Cost Calculations**

## 📊 Port Database

The application includes **2,948 ports** worldwide with:
- Port names and alternate names
- Country and region information
- Precise coordinates (longitude/latitude)
- Search functionality

## 🔍 Example Calculations

- **Hamburg → Shanghai**: ~8,500 nm (~15,700 km)
- **Rotterdam → Singapore**: ~6,200 nm (~11,500 km)
- **New York → London**: ~3,000 nm (~5,600 km)

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

**🌊 SeaRoute Maritime Distance Calculator** - Powered by Python SeaRoute wrapper