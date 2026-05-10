"""
Main Flask Application
API Provider Service for Fireworks.ai
"""

from flask import Flask, send_from_directory
from flask_cors import CORS
import asyncio
import os

# Import configuration and database
from backend.config import config
from backend.database import db

# Import routes
from backend.routes.openai_routes import openai_bp
from backend.routes.anthropic_routes import anthropic_bp
from backend.routes.dashboard_routes import dashboard_bp

# Import middleware
from backend.middleware.logging_middleware import logging_middleware
from backend.middleware.rate_limit_middleware import rate_limit_middleware, rate_limiter

# Import services
from backend.services.key_rotator import rotator
from backend.utils.scheduler import scheduler_service


def create_app():
    """Create and configure Flask application"""
    app = Flask(__name__, static_folder="../frontend", static_url_path="")

    # Configure CORS
    if config.get("security.cors_enabled", True):
        allowed_origins = config.get("security.allowed_origins", ["*"])
        CORS(app, origins=allowed_origins)

    # Initialize database
    db_path = config.get("database.path", "data/database.db")
    db.db_path = db_path
    db.initialize()

    # Load API keys into rotator
    keys_count = rotator.load_keys()
    print(f"✓ Loaded {keys_count} API keys")

    # Set rotation enabled
    rotator.set_enabled(config.get("rotation.enabled", True))

    # Load rate limiter config
    rate_limiter.load_config()

    # Register before_request middleware
    @app.before_request
    def before_request():
        logging_middleware()
        result = rate_limit_middleware()
        if result:
            return result

    # Register blueprints
    app.register_blueprint(openai_bp)
    app.register_blueprint(anthropic_bp)
    app.register_blueprint(dashboard_bp)

    # Serve frontend files (removed duplicate, moved to end)

    @app.route("/login")
    def login_page():
        return send_from_directory(app.static_folder, "login.html")

    @app.route("/dashboard")
    def dashboard_page():
        return send_from_directory(app.static_folder, "dashboard.html")

    @app.route("/keys")
    def keys_page():
        return send_from_directory(app.static_folder, "keys.html")

    @app.route("/models")
    def models_page():
        return send_from_directory(app.static_folder, "models.html")

    @app.route("/monitor")
    def monitor_page():
        return send_from_directory(app.static_folder, "monitor.html")

    @app.route("/settings")
    def settings_page():
        return send_from_directory(app.static_folder, "settings.html")

    @app.route("/docs")
    def docs_page():
        return send_from_directory(app.static_folder, "docs.html")

    # Health check endpoint
    @app.route("/health")
    def health():
        return {"status": "ok", "service": "api-provider-service"}, 200

    # Additional health check for Railway/Render
    @app.route("/healthz")
    def healthz():
        return "OK", 200

    # Root endpoint
    @app.route("/")
    def root():
        return send_from_directory(app.static_folder, "index.html")

    # Start background scheduler
    scheduler_service.start()

    return app


# Create app instance
app = create_app()


if __name__ == "__main__":
    host = config.get("server.host", "0.0.0.0")
    port = config.get("server.port", 10736)
    debug = config.get("server.debug", False)

    print(f"""
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║        🔥 Fireworks.ai API Provider Service 🔥           ║
║                                                           ║
║  OpenAI & Anthropic Compatible API Gateway               ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝

✓ Server starting on http://{host}:{port}
✓ Dashboard: http://{host}:{port}/dashboard
✓ API Endpoints:
  - POST /v1/chat/completions (OpenAI)
  - POST /v1/completions (OpenAI)
  - POST /v1/messages (Anthropic)

✓ Configuration loaded
✓ Database initialized
✓ API key rotation: {"enabled" if config.get("rotation.enabled") else "disabled"}
✓ Rate limiting: {"enabled" if config.get("rate_limiting.enabled") else "disabled"}
✓ Auto-backup: {"enabled" if config.get("database.auto_backup") else "disabled"}

Press CTRL+C to stop the server
""")

    app.run(host=host, port=port, debug=debug)
