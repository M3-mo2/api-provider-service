# Fireworks.ai API Provider Service

🔥 **OpenAI & Anthropic Compatible API Gateway** with intelligent key rotation, monitoring, and modern dashboard.

## Features

- ✅ **OpenAI & Anthropic Compatible** - Drop-in replacement for both APIs
- 🔄 **Smart Key Rotation** - Round-robin distribution with automatic failover
- 📊 **Real-time Monitoring** - Track requests, tokens, costs, and performance
- 💾 **Automatic Backups** - Scheduled backups with easy restore
- 🎨 **Modern Dashboard** - Beautiful GitHub dark theme interface
- ⚡ **High Performance** - Built with Flask and async support
- 🔐 **Secure** - Password-protected dashboard with JWT authentication
- 📈 **Analytics** - Detailed statistics and charts

## Quick Start

### 1. Installation

```bash
# Clone the repository
cd api-provider-service

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env
```

### 2. Configuration

Edit `config/config.yaml` or set environment variables:

```yaml
server:
  host: "0.0.0.0"
  port: 10736

security:
  dashboard_username: "admin"
  dashboard_password: "macro"
```

### 3. Run the Service

```bash
python run.py
```

The service will start on `http://localhost:10736`

### 4. Add API Keys

1. Go to `http://localhost:10736/login`
2. Login with `admin` / `macro`
3. Navigate to **API Keys** page
4. Add your Fireworks.ai API keys

### 5. Use the API

#### With OpenAI SDK:

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:10736/v1",
    api_key="not-needed"  # Keys managed by service
)

response = client.chat.completions.create(
    model="accounts/fireworks/models/llama-v3p1-8b-instruct",
    messages=[{"role": "user", "content": "Hello!"}]
)

print(response.choices[0].message.content)
```

#### With Anthropic SDK:

```python
import anthropic

client = anthropic.Anthropic(
    base_url="http://localhost:10736",
    api_key="not-needed"
)

response = client.messages.create(
    model="accounts/fireworks/models/kimi-k2p5",
    messages=[{"role": "user", "content": "Hello!"}],
    max_tokens=256
)

print(response.content[0].text)
```

#### With cURL:

```bash
curl http://localhost:10736/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "accounts/fireworks/models/llama-v3p1-8b-instruct",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

## API Endpoints

### Inference Endpoints

- `POST /v1/chat/completions` - OpenAI-compatible chat completions
- `POST /v1/completions` - OpenAI-compatible completions
- `POST /v1/messages` - Anthropic-compatible messages

### Dashboard API

- `POST /api/auth/login` - Login to dashboard
- `GET /api/dashboard/stats` - Get statistics
- `GET /api/dashboard/keys` - List API keys
- `POST /api/dashboard/keys` - Add API key
- `PUT /api/dashboard/keys/:id` - Update API key
- `DELETE /api/dashboard/keys/:id` - Delete API key
- `GET /api/dashboard/models` - List models
- `POST /api/dashboard/models` - Add model
- `GET /api/dashboard/logs` - Get request logs
- `POST /api/dashboard/backup` - Create backup
- `POST /api/dashboard/backup/restore` - Restore backup

## Project Structure

```
api-provider-service/
├── backend/
│   ├── app.py                 # Main Flask application
│   ├── config.py              # Configuration management
│   ├── database.py            # Database models
│   ├── routes/                # API routes
│   │   ├── openai_routes.py
│   │   ├── anthropic_routes.py
│   │   └── dashboard_routes.py
│   ├── services/              # Business logic
│   │   ├── key_rotator.py
│   │   ├── fireworks_proxy.py
│   │   ├── monitor_service.py
│   │   └── backup_service.py
│   ├── middleware/            # Middleware
│   │   ├── auth_middleware.py
│   │   ├── logging_middleware.py
│   │   └── rate_limit_middleware.py
│   └── utils/
│       └── scheduler.py
├── frontend/                  # Web UI
│   ├── index.html
│   ├── login.html
│   ├── dashboard.html
│   ├── keys.html
│   ├── models.html
│   ├── monitor.html
│   ├── settings.html
│   ├── css/
│   └── js/
├── config/
│   └── config.yaml
├── data/
│   ├── database.db
│   └── backups/
├── requirements.txt
└── run.py
```

## Configuration

### Environment Variables

```bash
HOST=0.0.0.0
PORT=10736
DEBUG=False
DATABASE_PATH=data/database.db
DASHBOARD_USERNAME=admin
DASHBOARD_PASSWORD=macro
SECRET_KEY=change-this-secret-key-in-production
```

### Config File (config/config.yaml)

```yaml
server:
  host: "0.0.0.0"
  port: 10736
  debug: false

database:
  path: "data/database.db"
  backup_path: "data/backups"
  auto_backup: true
  backup_interval_hours: 10

fireworks:
  base_url: "https://api.fireworks.ai/inference/v1"
  timeout: 300
  max_retries: 3

rotation:
  enabled: true
  strategy: "round-robin"
  health_check_interval: 300
  auto_failover: true

monitoring:
  enabled: true
  log_requests: true
  detailed_logging: true
  retention_days: 30

security:
  require_dashboard_auth: true
  dashboard_username: "admin"
  dashboard_password: "macro"
  cors_enabled: true
  allowed_origins: ["*"]

rate_limiting:
  enabled: false
  requests_per_minute: 60
  requests_per_hour: 1000
```

## Features in Detail

### 🔄 API Key Rotation

The service automatically rotates between multiple Fireworks.ai API keys using a round-robin strategy:

- **Load Balancing**: Distributes requests evenly across all active keys
- **Health Checking**: Monitors key health and skips failed keys
- **Automatic Failover**: Switches to healthy keys when one fails
- **Priority Support**: Higher priority keys are used first
- **Statistics Tracking**: Tracks usage per key

### 📊 Monitoring & Analytics

Real-time monitoring with detailed statistics:

- Total requests and success rate
- Token consumption (input/output/total)
- Average response time
- Cost estimation
- Request logs with filtering
- Charts and visualizations
- Export to CSV

### 💾 Backup & Restore

Automatic and manual backup system:

- **Automatic Backups**: Scheduled backups every 10 hours (configurable)
- **Manual Backups**: Create backups on demand
- **Full Restore**: Restore complete database from backup
- **Backup Contents**: API keys, models, config, usage stats, logs (optional)
- **Integrity Checking**: SHA256 checksums for validation

### 🎨 Dashboard

Modern web interface with GitHub dark theme:

- **Overview**: Statistics and charts
- **API Keys**: Manage Fireworks.ai keys
- **Models**: Configure available models
- **Monitor**: Real-time request logs
- **Settings**: Configure service settings
- **Responsive**: Works on desktop and mobile

## Dependencies

- Flask 3.0.0 - Web framework
- SQLAlchemy 2.0.23 - Database ORM
- httpx 0.25.2 - Async HTTP client
- APScheduler 3.10.4 - Background tasks
- bcrypt 4.1.2 - Password hashing
- PyJWT 2.8.0 - JWT tokens
- Chart.js 4.4.0 - Charts (frontend)

## Security

- Dashboard protected with username/password
- JWT token-based authentication
- Password hashing with bcrypt
- CORS configuration
- Optional rate limiting
- API keys stored in database (not encrypted by default)

## Performance

- Async HTTP requests to Fireworks.ai
- Connection pooling
- Streaming support for real-time responses
- Efficient database queries with indexes
- Background tasks for health checks and backups

## Troubleshooting

### Service won't start

- Check if port 10736 is available
- Verify Python version (3.10+)
- Install all dependencies: `pip install -r requirements.txt`

### API keys not working

- Verify keys are active in dashboard
- Check key health status
- Review logs in Monitor page
- Ensure keys are valid Fireworks.ai keys

### Dashboard login fails

- Default credentials: `admin` / `macro`
- Check `config/config.yaml` for custom credentials
- Clear browser cache and cookies

### Backup fails

- Ensure `data/backups` directory exists and is writable
- Check disk space
- Review logs for error messages

## Production Deployment

For production use:

1. **Change default password** in config
2. **Set strong SECRET_KEY** in .env
3. **Enable HTTPS** with reverse proxy (nginx/caddy)
4. **Use production WSGI server**: `gunicorn -w 4 -b 0.0.0.0:10736 backend.app:app`
5. **Enable rate limiting** if needed
6. **Set up monitoring** and alerts
7. **Regular backups** to external storage
8. **Restrict CORS** origins

## License

This project is provided as-is for use with Fireworks.ai API services.

## Support

For issues or questions:
- Check the documentation at `/` endpoint
- Review Fireworks.ai docs: https://docs.fireworks.ai
- Check application logs in `logs/` directory

## Acknowledgments

- Built with [Fireworks.ai](https://fireworks.ai)
- UI inspired by GitHub's design system
- Charts powered by Chart.js
