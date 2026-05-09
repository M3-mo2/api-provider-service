"""
Logging Middleware
Logs all incoming requests
"""

from flask import request
from backend.services.monitor_service import monitor


def logging_middleware():
    """Middleware to log requests"""
    # Get client info
    client_ip = request.remote_addr
    user_agent = request.headers.get("User-Agent", "")
    endpoint = request.path
    method = request.method

    # Start tracking request
    request_id = monitor.start_request(endpoint, method, client_ip, user_agent)

    # Store request_id in request context
    request.request_id = request_id
