"""
Rate Limiting Middleware
Optional rate limiting for API endpoints
"""

import time
from collections import defaultdict
from flask import request, jsonify
from backend.config import config


class RateLimiter:
    """Simple in-memory rate limiter"""

    def __init__(self):
        self.requests = defaultdict(list)  # {ip: [timestamps]}
        self.enabled = False
        self.requests_per_minute = 60
        self.requests_per_hour = 1000

    def load_config(self):
        """Load rate limiting configuration"""
        self.enabled = config.get("rate_limiting.enabled", False)
        self.requests_per_minute = config.get("rate_limiting.requests_per_minute", 60)
        self.requests_per_hour = config.get("rate_limiting.requests_per_hour", 1000)

    def is_allowed(self, client_ip: str) -> tuple[bool, str]:
        """
        Check if request is allowed
        Returns: (allowed, error_message)
        """
        if not self.enabled:
            return True, ""

        now = time.time()

        # Clean old entries
        self.requests[client_ip] = [
            ts
            for ts in self.requests[client_ip]
            if now - ts < 3600  # Keep last hour
        ]

        # Check per-minute limit
        recent_minute = [ts for ts in self.requests[client_ip] if now - ts < 60]
        if len(recent_minute) >= self.requests_per_minute:
            return (
                False,
                f"Rate limit exceeded: {self.requests_per_minute} requests per minute",
            )

        # Check per-hour limit
        if len(self.requests[client_ip]) >= self.requests_per_hour:
            return (
                False,
                f"Rate limit exceeded: {self.requests_per_hour} requests per hour",
            )

        # Add current request
        self.requests[client_ip].append(now)

        return True, ""


# Global rate limiter instance
rate_limiter = RateLimiter()


def rate_limit_middleware():
    """Middleware to enforce rate limiting"""
    client_ip = request.remote_addr

    allowed, error_msg = rate_limiter.is_allowed(client_ip)

    if not allowed:
        return jsonify({"error": error_msg}), 429
