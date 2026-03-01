# HALO Health - Zero-Cost Deployment Guide

Deploy HALO Health completely free using Vercel (Frontend) + Render (Backend) + Neon (Database)

## Prerequisites
- GitHub account
- Vercel account (free)
- Render account (free)
- Neon account (free)

---

## Step 1: Setup Neon Database (5 minutes)

1. Go to https://neon.tech
2. Sign up with GitHub
3. Click **"Create a Project"**
4. Name: `aura-db`
5. Region: Choose closest to you
6. **Copy the connection string** - looks like:
   ```
   postgresql://user:password@ep-xxx.neon.tech/neondb?sslmode=require
   ```
7. Save this for later!

---

## Step 2: Prepare Code for Deployment

### Push to GitHub

```bash
# Initialize git (if not already done)
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit - HALO Health Platform"

# Create GitHub repo (go to github.com/new)
# Then push:
git remote add origin https://github.com/YOUR_USERNAME/halo-health.git
git branch -M main
git push -u origin main
```

---

## Step 3: Deploy Backend to Render (10 minutes)

1. Go to https://render.com
2. Sign up with GitHub
3. Click **"New +" → "Web Service"**
4. Connect your GitHub repo: `aura-platform`
5. Configure:
   - **Name:** `aura-backend`
   - **Region:** Oregon (or closest)
   - **Branch:** `main`
   - **Root Directory:** `backend`
   - **Runtime:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
6. Click **"Advanced"** and add environment variables:
   - `GEMINI_API_KEY` = `your_gemini_key`
   - `DATABASE_URL` = `your_neon_connection_string`
   - `SECRET_KEY` = `your_secret_key_from_.env`
   - `PRO_MODEL` = `gemini-1.5-flash`
   - `FLASH_MODEL` = `gemini-1.5-flash`
7. Select **"Free"** plan
8. Click **"Create Web Service"**
9. Wait for deployment (~5 minutes)
10. **Copy your backend URL:** `https://aura-backend-xxxx.onrender.com`

---

## Step 4: Deploy Frontend to Vercel (5 minutes)

1. Go to https://vercel.com
2. Sign up with GitHub
3. Click **"Add New..." → "Project"**
4. Import your GitHub repo: `aura-platform`
5. Configure:
   - **Framework Preset:** Vite
   - **Root Directory:** `frontend-react`
   - **Build Command:** `npm run build`
   - **Output Directory:** `dist`
6. Click **"Environment Variables"** and add:
   - `VITE_API_URL` = `https://aura-backend-xxxx.onrender.com` (your Render URL)
7. Click **"Deploy"**
8. Wait for deployment (~2 minutes)
9. **Your app is live!** `https://aura-platform.vercel.app`

---

## Step 5: Update Frontend API URL

The frontend needs to know where the backend is:

1. In `frontend-react/src/utils/api_client.ts`, update the API URL:
   ```typescript
   const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
   ```

2. Commit and push:
   ```bash
   git add .
   git commit -m "Update API URL for production"
   git push
   ```

3. Vercel will auto-deploy the update!

---

## Cost Breakdown

| Service | Plan | Cost | Limits |
|---------|------|------|--------|
| **Vercel** | Free | $0 | Unlimited bandwidth |
| **Render** | Free | $0 | 750 hours/month, sleeps after 15 min |
| **Neon** | Free | $0 | 0.5 GB storage, auto-pause |
| **Total** | | **$0/month** | |

---

## Important Notes

### Backend Sleep (Render Free Tier)
- Backend sleeps after 15 minutes of inactivity
- First request after sleep takes ~30 seconds (cold start)
- Solution: Use a free uptime monitor (e.g., UptimeRobot) to ping every 14 minutes

### Database Limits (Neon Free Tier)
- 0.5 GB storage - enough for ~10,000 sessions
- Auto-pauses when inactive (instant resume)
- Can upgrade to paid plan later if needed

### API Rate Limits (Gemini Free Tier)
- 15 requests/minute
- 1,500 requests/day
- Consider upgrading if you get many users

---

## Troubleshooting

### Backend won't start
- Check environment variables are set correctly
- Verify DATABASE_URL includes `?sslmode=require`
- Check logs in Render dashboard

### Frontend can't connect to backend
- Verify VITE_API_URL is set correctly
- Check CORS settings in backend
- Ensure backend is running (check Render dashboard)

### Database connection errors
- Verify Neon connection string is correct
- Ensure `sslmode=require` is in the connection string
- Check Neon dashboard - database might be paused

---

## Next Steps

1. **Set up custom domain** (optional, free with Vercel)
2. **Enable uptime monitoring** to prevent cold starts
3. **Monitor usage** to stay within free tier limits
4. **Upgrade as needed** when you get real users

---

## Support

If you encounter issues:
1. Check Render logs: Dashboard → Logs
2. Check Vercel logs: Deployments → View Function Logs
3. Check Neon status: Dashboard → Operations

Your AURA platform is now live and completely free! 🎉
