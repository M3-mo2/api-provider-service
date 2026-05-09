"""
Entry point for the application
"""

from backend.app import app
from backend.config import config

if __name__ == "__main__":
    host = config.get("server.host", "0.0.0.0")
    port = config.get("server.port", 10736)
    debug = config.get("server.debug", False)

    app.run(host=host, port=port, debug=debug)
