# Railway Deployment Guide

## Quick Deploy to Railway

1. Push your code to GitHub
2. Go to [Railway.app](https://railway.app)
3. Click "New Project" → "Deploy from GitHub repo"
4. Select your repository
5. Railway will auto-detect Python and deploy

## Environment Variables

Set these in Railway dashboard:

```
PORT=8080
DATABASE_PATH=/app/data/database.db
DASHBOARD_USERNAME=admin
DASHBOARD_PASSWORD=macro
SECRET_KEY=your-secret-key-here-change-this
PYTHONUNBUFFERED=1
```

## Getting Your URL

After deployment completes:
1. Go to Railway dashboard
2. Click on your service
3. Go to **"Settings"** tab
4. Scroll down to **"Networking"** section
5. Click **"Generate Domain"** button
6. Your URL will be: `https://your-app.up.railway.app`

## Important Notes

- Railway uses Python 3.11.9 (from runtime.txt)
- SQLAlchemy upgraded to 2.0.35 for compatibility
- Database stored in `/app/data/database.db`
- Backups in `/app/data/backups`
- Health check endpoints: `/health` and `/healthz`

## Troubleshooting

### No URL showing?
**Solution**: Go to Settings → Networking → Click "Generate Domain"

### Service keeps restarting?
- Check logs for errors
- Verify all environment variables are set
- Ensure Python 3.11.9 is being used

### SQLAlchemy errors?
- Make sure Python version is 3.11.x (not 3.13)
- Check runtime.txt has `python-3.11.9`
- SQLAlchemy 2.0.35 is compatible with Python 3.11-3.12

### Database errors?
- Ensure DATABASE_PATH is set to `/app/data/database.db`
- Check logs to verify database initialization
