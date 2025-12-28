# 🚀 FREE Hosting Guide for Streaming Catalog API

This guide walks you through hosting your API for FREE on various platforms.

---

## Quick Comparison

| Platform | Free Tier | Sleeps? | Setup Time | Best For |
|----------|-----------|---------|------------|----------|
| **Render.com** | ✅ 750 hrs/month | Yes (15 min) | 5 min | Easiest setup |
| **Railway.app** | ✅ $5 credit/month | No | 5 min | Always-on |
| **Fly.io** | ✅ 3 shared VMs | No | 10 min | Performance |
| **Vercel** | ✅ Unlimited | No | 5 min | Serverless |

**My Recommendation:** Start with **Render.com** (easiest) or **Railway.app** (no sleep).

---

# Option 1: Render.com (Recommended - Easiest)

### Step 1: Get Your RapidAPI Key (if you haven't already)

1. Go to: https://rapidapi.com/movie-of-the-night-movie-of-the-night-default/api/streaming-availability
2. Click **"Subscribe to Test"**
3. Select the **Free plan** (100 requests/day)
4. Copy your API key from the **"X-RapidAPI-Key"** field

### Step 2: Push Code to GitHub

```bash
# If you don't have git installed, download from: https://git-scm.com/

# Navigate to your project folder
cd streaming-api

# Initialize git repository
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit - Streaming Catalog API"

# Create a new repository on GitHub (https://github.com/new)
# Then connect and push:
git remote add origin https://github.com/YOUR_USERNAME/streaming-catalog-api.git
git branch -M main
git push -u origin main
```

### Step 3: Deploy to Render

1. Go to **https://render.com** and sign up (use GitHub for easy connection)

2. Click **"New +"** → **"Web Service"**

3. Connect your GitHub repository:
   - Select **"streaming-catalog-api"** (or whatever you named it)

4. Configure the service:
   ```
   Name: streaming-catalog-api
   Region: Oregon (US West) or nearest to you
   Branch: main
   Runtime: Python 3
   Build Command: pip install -r requirements.txt
   Start Command: uvicorn app.main:app --host 0.0.0.0 --port $PORT
   Plan: Free
   ```

5. Click **"Advanced"** → **"Add Environment Variable"**:
   ```
   Key: RAPIDAPI_KEY
   Value: [paste your RapidAPI key here]
   ```

6. Click **"Create Web Service"**

7. Wait 2-3 minutes for deployment. Your API will be live at:
   ```
   https://streaming-catalog-api.onrender.com
   ```

### Step 4: Test Your Live API

```bash
# Test the health endpoint
curl https://streaming-catalog-api.onrender.com/

# Get top 10 Netflix movies
curl "https://streaming-catalog-api.onrender.com/top-movies/netflix?limit=10"

# View the interactive docs
# Open in browser: https://streaming-catalog-api.onrender.com/docs
```

> ⚠️ **Note:** Render free tier sleeps after 15 min of inactivity. First request after sleep takes ~30 seconds.

---

# Option 2: Railway.app (No Sleep - Always On)

### Step 1: Get RapidAPI Key
(Same as above)

### Step 2: Push to GitHub
(Same as above)

### Step 3: Deploy to Railway

1. Go to **https://railway.app** and sign up with GitHub

2. Click **"New Project"** → **"Deploy from GitHub repo"**

3. Select your **streaming-catalog-api** repository

4. Railway auto-detects Python. Click on the service, then:
   - Go to **"Variables"** tab
   - Add: `RAPIDAPI_KEY` = `[your key]`
   - Add: `PORT` = `8000`

5. Go to **"Settings"** tab:
   - Under **"Networking"** → Click **"Generate Domain"**
   - You'll get a URL like: `streaming-catalog-api-production.up.railway.app`

6. Your API is live! Railway gives you **$5 free credit/month** (~500 hours).

---

# Option 3: Fly.io (Best Performance)

### Step 1: Install Fly CLI

```bash
# macOS
brew install flyctl

# Windows (PowerShell)
powershell -Command "iwr https://fly.io/install.ps1 -useb | iex"

# Linux
curl -L https://fly.io/install.sh | sh
```

### Step 2: Sign Up & Login

```bash
fly auth signup
# or if you have an account:
fly auth login
```

### Step 3: Launch Your App

```bash
cd streaming-api

# Initialize Fly app
fly launch

# When prompted:
# - App name: streaming-catalog-api (or your choice)
# - Region: Choose nearest to you
# - Postgres: No
# - Redis: No
# - Deploy now: No (we need to add secrets first)
```

### Step 4: Add Your API Key

```bash
fly secrets set RAPIDAPI_KEY=your_rapidapi_key_here
```

### Step 5: Deploy

```bash
fly deploy
```

### Step 6: Get Your URL

```bash
fly status
# Your app URL: https://streaming-catalog-api.fly.dev
```

---

# Option 4: Vercel (Serverless)

Vercel requires a slight code modification for serverless. Create this file:

### Step 1: Create `vercel.json`

```json
{
  "builds": [
    {
      "src": "app/main.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "app/main.py"
    }
  ]
}
```

### Step 2: Deploy

```bash
# Install Vercel CLI
npm install -g vercel

# Login
vercel login

# Deploy
cd streaming-api
vercel

# Add environment variable
vercel env add RAPIDAPI_KEY
# Paste your key when prompted

# Redeploy with env var
vercel --prod
```

---

# 🧪 Testing Your Deployed API

Once deployed, test all endpoints:

```bash
# Replace YOUR_URL with your actual deployment URL
export API_URL="https://streaming-catalog-api.onrender.com"

# 1. Health check
curl "$API_URL/"

# 2. List services
curl "$API_URL/services"

# 3. Top 10 Netflix movies
curl "$API_URL/top-movies/netflix?limit=10"

# 4. Top 5 movies on Prime with rating >= 8.0
curl "$API_URL/top-movies/prime?limit=5&min_rating=8.0"

# 5. Search for a movie
curl "$API_URL/search?q=inception"

# 6. Get all top movies from all services
curl "$API_URL/top-movies?limit=5"

# 7. Interactive docs (open in browser)
echo "Open: $API_URL/docs"
```

---

# 🔧 Troubleshooting

### "Application Error" or 500 Error
- Check your `RAPIDAPI_KEY` is set correctly in environment variables
- View logs:
  - Render: Dashboard → Your service → "Logs" tab
  - Railway: Dashboard → Your service → "Logs"
  - Fly.io: `fly logs`

### API Returns Empty Results
- Verify your RapidAPI key is valid
- Check you haven't exceeded the free tier (100 requests/day)
- Try a different country code (e.g., `?country=gb`)

### Slow First Response (Render)
- This is normal - free tier sleeps after 15 min
- First request after sleep takes 30 seconds
- Consider Railway if you need always-on

### Build Fails
- Check `requirements.txt` has all dependencies
- Ensure `runtime.txt` specifies Python 3.11.0
- View build logs for specific errors

---

# 📊 Monitoring & Logs

### Render
- Dashboard → Your service → "Logs" tab
- Dashboard → Your service → "Metrics" tab

### Railway  
- Dashboard → Your project → Click service → "Logs"

### Fly.io
```bash
fly logs           # Stream logs
fly status         # Check app status
fly dashboard      # Open web dashboard
```

---

# 🔄 Updating Your API

After making changes to your code:

```bash
# Commit changes
git add .
git commit -m "Updated API"
git push origin main
```

All platforms auto-deploy on push to main branch!

---

# 💡 Tips for Free Tier

1. **Render**: Use a service like UptimeRobot (free) to ping your API every 10 minutes to prevent sleep

2. **Railway**: Monitor your usage - $5 credit ≈ 500 hours of uptime

3. **All platforms**: Cache responses where possible to reduce API calls to RapidAPI

4. **RapidAPI**: The free tier is 100 requests/day. For more:
   - Basic: $10/month for 1,000 requests/day
   - Pro: $50/month for 10,000 requests/day

---

# 🎉 You're Done!

Your API is now live and accessible from anywhere. Share your URL:

```
https://your-app-name.onrender.com/docs
```

Anyone can now:
- Get top movies from any streaming service
- Search for titles with IMDB ratings
- Compare streaming catalogs
- And more!
