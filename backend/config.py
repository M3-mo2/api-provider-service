"""
Configuration management system
"""

import os
import yaml
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Configuration manager"""

    def __init__(self, config_path="config/config.yaml"):
        self.config_path = config_path
        self.config = {}
        self.load_config()

    def load_config(self):
        """Load configuration from YAML file and environment variables"""
        # Load YAML config
        if os.path.exists(self.config_path):
            with open(self.config_path, "r") as f:
                self.config = yaml.safe_load(f)
        else:
            print(
                f"Warning: Config file not found at {self.config_path}, using defaults"
            )
            self.config = self._get_default_config()

        # Override with environment variables
        self._override_from_env()

    def _get_default_config(self):
        """Get default configuration"""
        return {
            "server": {"host": "0.0.0.0", "port": 10736, "debug": False},
            "database": {
                "path": "data/database.db",
                "backup_path": "data/backups",
                "auto_backup": True,
                "backup_interval_hours": 10,
            },
            "fireworks": {
                "base_url": "https://api.fireworks.ai/inference/v1",
                "timeout": 300,
                "max_retries": 3,
            },
            "rotation": {
                "enabled": True,
                "strategy": "round-robin",
                "health_check_interval": 300,
                "auto_failover": True,
            },
            "monitoring": {
                "enabled": True,
                "log_requests": True,
                "log_responses": False,
                "retention_days": 30,
                "detailed_logging": True,
            },
            "security": {
                "require_dashboard_auth": True,
                "dashboard_username": "admin",
                "dashboard_password": "macro",
                "cors_enabled": True,
                "allowed_origins": ["*"],
            },
            "rate_limiting": {
                "enabled": False,
                "requests_per_minute": 60,
                "requests_per_hour": 1000,
            },
        }

    def _override_from_env(self):
        """Override configuration with environment variables"""
        # Server
        if os.getenv("HOST"):
            self.config["server"]["host"] = os.getenv("HOST")
        if os.getenv("PORT"):
            self.config["server"]["port"] = int(os.getenv("PORT"))
        if os.getenv("DEBUG"):
            self.config["server"]["debug"] = os.getenv("DEBUG").lower() == "true"

        # Database
        if os.getenv("DATABASE_PATH"):
            self.config["database"]["path"] = os.getenv("DATABASE_PATH")

        # Security
        if os.getenv("DASHBOARD_USERNAME"):
            self.config["security"]["dashboard_username"] = os.getenv(
                "DASHBOARD_USERNAME"
            )
        if os.getenv("DASHBOARD_PASSWORD"):
            self.config["security"]["dashboard_password"] = os.getenv(
                "DASHBOARD_PASSWORD"
            )

        # Fireworks
        if os.getenv("FIREWORKS_BASE_URL"):
            self.config["fireworks"]["base_url"] = os.getenv("FIREWORKS_BASE_URL")

    def get(self, key, default=None):
        """Get configuration value by dot notation (e.g., 'server.port')"""
        keys = key.split(".")
        value = self.config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def set(self, key, value):
        """Set configuration value by dot notation"""
        keys = key.split(".")
        config = self.config

        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        config[keys[-1]] = value

    def save(self):
        """Save configuration to YAML file"""
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        with open(self.config_path, "w") as f:
            yaml.dump(self.config, f, default_flow_style=False)

    def get_all(self):
        """Get all configuration"""
        return self.config


# Global config instance
config = Config()
