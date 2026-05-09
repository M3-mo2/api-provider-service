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
PORT=10736
DATABASE_PATH=/app/data/database.db
DASHBOARD_USERNAME=admin
DASHBOARD_PASSWORD=macro
SECRET_KEY=your-secret-key-here
```

## Important Notes

- Railway uses Python 3.11.9 (from runtime.txt)
- SQLAlchemy upgraded to 2.0.35 for Python 3.13 compatibility
- Database will be stored in `/app/data/database.db`
- Backups in `/app/data/backups`

## Troubleshooting

If you get SQLAlchemy errors:
- Make sure Python version is 3.11.x (not 3.13)
- Check runtime.txt has `python-3.11.9`
- SQLAlchemy 2.0.35 is compatible with Python 3.11-3.12
