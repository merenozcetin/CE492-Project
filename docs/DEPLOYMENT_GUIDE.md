# 🌊 SeaRoute Website Deployment Guide

## 🚀 Quick Deployment Options

### Option 1: Railway (Recommended)
1. **Sign up** at [railway.app](https://railway.app)
2. **Connect GitHub** repository
3. **Deploy** - Railway handles everything automatically
4. **Get your public URL** (e.g., `https://your-app.railway.app`)

### Option 2: Render (Free Tier)
1. **Sign up** at [render.com](https://render.com)
2. **Connect GitHub** repository
3. **Create Web Service**
4. **Deploy** - Free SSL included

### Option 3: Heroku
1. **Sign up** at [heroku.com](https://heroku.com)
2. **Install Heroku CLI**
3. **Run commands:**
   ```bash
   heroku create your-searoute-app
   git add .
   git commit -m "Deploy SeaRoute"
   git push heroku main
   ```

## 📁 Required Files (Already Created)
- ✅ `Procfile` - Tells platform how to run your app
- ✅ `requirements.txt` - Python dependencies
- ✅ `runtime.txt` - Python version
- ✅ Modified server to use environment PORT

## ⚠️ Important Notes

### Java Requirement
Most cloud platforms don't have Java pre-installed. You'll need to:

1. **Add Java to your deployment** (platform-specific)
2. **Or use a platform that supports Java** (like Railway with custom Docker)

### File Structure
Make sure your deployment includes:
- `web-interface/` folder with HTML and Python files
- `searoute-engine/` folder with JAR and data files
- All the deployment files in the root

## 🔧 Platform-Specific Setup

### For Railway:
- Add `Dockerfile` for Java support
- Or use Railway's Java buildpack

### For Render:
- Specify build command: `pip install -r requirements.txt`
- Specify start command: `python web-interface/searoute_server.py`

### For Heroku:
- Add Java buildpack: `heroku buildpacks:add heroku/java`
- Add Python buildpack: `heroku buildpacks:add heroku/python`

## 🌐 After Deployment
Your SeaRoute website will be accessible at:
- Railway: `https://your-app.railway.app`
- Render: `https://your-app.onrender.com`
- Heroku: `https://your-app.herokuapp.com`

## 🎯 Next Steps
1. Choose a platform
2. Create account
3. Connect your code repository
4. Deploy!
5. Share your public URL with the world!

Your SeaRoute website will then be accessible to anyone on the internet! 🌍⚓
