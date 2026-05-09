# Render Deployment Guide

## Quick Deploy to Render

1. Push your code to GitHub
2. Go to [Render.com](https://render.com)
3. Click "New +" → "Web Service"
4. Connect your GitHub repository
5. Configure:
   - **Name**: api-provider-service
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn backend.app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 300`

## Environment Variables

Add these in Render dashboard:

```
DATABASE_PATH=/opt/render/project/src/data/database.db
DASHBOARD_USERNAME=admin
DASHBOARD_PASSWORD=macro
SECRET_KEY=your-secret-key-here-change-this
PYTHON_VERSION=3.11.9
```

## Important Notes

- Render uses Python 3.11.9 (from runtime.txt)
- Free tier sleeps after 15 min inactivity
- First request after sleep takes 30-60 seconds
- Use [UptimeRobot](https://uptimerobot.com) to ping every 10 min (free)

## Persistent Storage

Render free tier doesn't have persistent disk. Options:

1. **Use PostgreSQL** (recommended):
   - Add PostgreSQL database in Render
   - Update database.py to use PostgreSQL instead of SQLite

2. **Use External Storage**:
   - Store backups in S3/Cloudflare R2
   - Use external database service

## Troubleshooting

### SQLAlchemy Error
- Ensure Python 3.11.x is used (not 3.13)
- Check runtime.txt: `python-3.11.9`

### Database Issues
- SQLite works but data lost on redeploy
- Upgrade to PostgreSQL for production
