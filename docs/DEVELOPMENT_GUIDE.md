# 🛠️ Development Guide

## 🚀 Getting Started

### Prerequisites
- Python 3.8 or higher
- pip package manager
- Git (for version control)

### Setup Development Environment

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd searoute-master
   ```

2. **Create virtual environment (recommended)**
   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**
   ```bash
   streamlit run src/app.py
   ```

## 📁 Project Structure Explained

```
searoute-master/
├── src/                           # Source code
│   └── app.py                    # Main Streamlit application
├── data/                          # Data files
│   └── ports.json                # Port database (3,800+ ports)
├── docs/                          # Documentation
│   ├── CODE_DOCUMENTATION.md     # Detailed code explanation
│   └── CE492_Project_Description[1].md  # Project requirements
├── requirements.txt               # Python dependencies
├── LICENSE                        # MIT License
└── README.md                      # Main documentation
```

## 🔧 Development Workflow

### Making Changes

1. **Edit the main application**
   - Modify `src/app.py` for UI changes
   - Update port data in `data/ports.json`
   - Add new features or calculations

2. **Test your changes**
   ```bash
   streamlit run src/app.py
   ```

3. **Commit your changes**
   ```bash
   git add .
   git commit -m "Description of changes"
   git push origin master
   ```

### Code Organization

#### Main Application (`src/app.py`)
- **Data Classes**: `Port` dataclass for port information
- **Calculator Class**: `SeaRouteCalculator` for distance calculations
- **UI Components**: Streamlit interface with tabs and forms
- **Error Handling**: Graceful error handling and user feedback

#### Data Files (`data/`)
- **Port Database**: JSON file with port information
- **Format**: Standardized port data structure
- **Updates**: Easy to add new ports or modify existing ones

#### Documentation (`docs/`)
- **Code Documentation**: Detailed explanation of implementation
- **Project Description**: Original project requirements
- **Development Guide**: This file

## 🧪 Testing

### Manual Testing
1. **Port Loading**: Check if ports load correctly on startup
2. **Port Selection**: Test dropdown functionality
3. **Distance Calculation**: Test with known port pairs
4. **Error Handling**: Test with invalid inputs

### Test Cases
- **Hamburg → Shanghai**: Should be ~8,500 nm
- **Rotterdam → Singapore**: Should be ~6,200 nm
- **New York → London**: Should be ~3,000 nm

### Debug Features
- Console logging for SeaRoute results
- Error messages in UI
- Debug information in sidebar

## 🐛 Debugging

### Common Issues

#### 1. Port Loading Errors
```python
# Check if file exists
if not os.path.exists('data/ports.json'):
    print("❌ Port data file not found!")
```

#### 2. SeaRoute Calculation Errors
```python
# Debug SeaRoute result
print(f"Route result: {route}")
print(f"Route type: {type(route)}")
```

#### 3. Dependency Issues
```bash
# Check installed packages
pip list | grep streamlit
pip list | grep searoute
```

### Debug Tools
- **Console Output**: Print statements for debugging
- **Streamlit Debug**: Built-in error messages
- **File Validation**: Check data file integrity

## 🚀 Deployment

### Local Development
```bash
streamlit run src/app.py
```

### Streamlit Cloud
1. Push to GitHub
2. Connect repository to Streamlit Cloud
3. Set main file to `src/app.py`
4. Deploy automatically

### Other Platforms
- **Heroku**: Add Procfile
- **Railway**: Automatic detection
- **DigitalOcean**: App Platform

## 📈 Performance Optimization

### Data Loading
- Load ports once at startup
- Use in-memory search
- Efficient data structures

### UI Responsiveness
- Immediate user feedback
- Loading indicators
- Error handling

### Calculation Efficiency
- SeaRoute wrapper optimization
- Fallback calculations
- Result caching

## 🔄 Version Control

### Git Workflow
1. **Feature Branch**: Create branch for new features
2. **Development**: Make changes and test
3. **Commit**: Commit with descriptive messages
4. **Push**: Push to remote repository
5. **Merge**: Merge to main branch

### Commit Messages
- Use descriptive commit messages
- Include issue numbers if applicable
- Follow conventional commit format

## 📝 Code Style

### Python Style
- Follow PEP 8 guidelines
- Use type hints where possible
- Write docstrings for functions
- Use meaningful variable names

### Streamlit Best Practices
- Use columns for layout
- Provide user feedback
- Handle errors gracefully
- Keep UI responsive

## 🤝 Contributing

### Before Contributing
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

### Code Review Process
1. Automated checks pass
2. Manual code review
3. Testing verification
4. Documentation updates

## 📞 Support

### Getting Help
- Check the documentation first
- Look at existing issues
- Create a new issue if needed
- Provide detailed error information

### Reporting Issues
- Include error messages
- Describe steps to reproduce
- Provide system information
- Include relevant code snippets

---

**Happy coding! 🚀**
