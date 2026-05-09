"""
API Key Rotation Service - Round-robin with health checking
"""

import time
from datetime import datetime
from threading import Lock
from backend.database import db, APIKey


class APIKeyRotator:
    """
    Smart API key rotation system with round-robin distribution,
    health checking, and automatic failover
    """

    def __init__(self):
        self.current_index = 0
        self.keys = []
        self.health_status = {}  # {key_id: {'healthy': bool, 'last_check': timestamp}}
        self.lock = Lock()
        self.enabled = True

    def load_keys(self):
        """Load active API keys from database"""
        session = db.get_session()
        try:
            # Get all active keys ordered by priority (higher priority first)
            keys = (
                session.query(APIKey)
                .filter(APIKey.is_active == True)
                .order_by(APIKey.priority.desc(), APIKey.id)
                .all()
            )

            with self.lock:
                self.keys = keys

                # Initialize health status for new keys
                for key in keys:
                    if key.id not in self.health_status:
                        self.health_status[key.id] = {
                            "healthy": True,
                            "last_check": time.time(),
                            "consecutive_failures": 0,
                        }

            return len(keys)
        finally:
            session.close()

    def get_next_key(self):
        """
        Get the next API key using round-robin strategy
        Skips disabled and unhealthy keys
        Returns None if no healthy keys available
        """
        if not self.enabled:
            # If rotation disabled, return first active key
            session = db.get_session()
            try:
                key = session.query(APIKey).filter(APIKey.is_active == True).first()
                return key.api_key if key else None
            finally:
                session.close()

        with self.lock:
            if not self.keys:
                self.load_keys()

            if not self.keys:
                return None

            # Try to find a healthy key
            attempts = 0
            max_attempts = len(self.keys)

            while attempts < max_attempts:
                key = self.keys[self.current_index]

                # Move to next index for next call
                self.current_index = (self.current_index + 1) % len(self.keys)
                attempts += 1

                # Check if key is healthy
                if self._is_key_healthy(key.id):
                    # Update last used timestamp
                    self._update_last_used(key.id)
                    return key.api_key

            # No healthy keys found
            return None

    def _is_key_healthy(self, key_id):
        """Check if a key is healthy"""
        if key_id not in self.health_status:
            return True

        status = self.health_status[key_id]

        # If marked as unhealthy and not enough time passed, skip
        if not status["healthy"]:
            # Retry after 5 minutes
            if time.time() - status["last_check"] < 300:
                return False
            else:
                # Time to retry, mark as healthy temporarily
                status["healthy"] = True
                status["consecutive_failures"] = 0

        return True

    def mark_key_success(self, api_key):
        """Mark a key as successful"""
        key_id = self._get_key_id(api_key)
        if key_id:
            with self.lock:
                if key_id in self.health_status:
                    self.health_status[key_id]["healthy"] = True
                    self.health_status[key_id]["consecutive_failures"] = 0
                    self.health_status[key_id]["last_check"] = time.time()

            # Update database stats
            self._update_key_stats(key_id, success=True)

    def mark_key_failed(self, api_key, error_message=None):
        """Mark a key as failed"""
        key_id = self._get_key_id(api_key)
        if key_id:
            with self.lock:
                if key_id not in self.health_status:
                    self.health_status[key_id] = {
                        "healthy": True,
                        "last_check": time.time(),
                        "consecutive_failures": 0,
                    }

                status = self.health_status[key_id]
                status["consecutive_failures"] += 1
                status["last_check"] = time.time()

                # Mark as unhealthy after 3 consecutive failures
                if status["consecutive_failures"] >= 3:
                    status["healthy"] = False
                    print(
                        f"⚠ API Key {key_id} marked as unhealthy after {status['consecutive_failures']} failures"
                    )

            # Update database stats
            self._update_key_stats(key_id, success=False)

    def _get_key_id(self, api_key):
        """Get key ID from API key string"""
        with self.lock:
            for key in self.keys:
                if key.api_key == api_key:
                    return key.id
        return None

    def _update_last_used(self, key_id):
        """Update last used timestamp in database"""
        session = db.get_session()
        try:
            key = session.query(APIKey).filter(APIKey.id == key_id).first()
            if key:
                key.last_used_at = datetime.utcnow()
                session.commit()
        except Exception as e:
            session.rollback()
            print(f"Error updating last_used_at: {e}")
        finally:
            session.close()

    def _update_key_stats(self, key_id, success=True):
        """Update key statistics in database"""
        session = db.get_session()
        try:
            key = session.query(APIKey).filter(APIKey.id == key_id).first()
            if key:
                key.total_requests += 1
                if not success:
                    key.failed_requests += 1

                # Calculate success rate
                if key.total_requests > 0:
                    key.success_rate = (
                        (key.total_requests - key.failed_requests) / key.total_requests
                    ) * 100

                session.commit()
        except Exception as e:
            session.rollback()
            print(f"Error updating key stats: {e}")
        finally:
            session.close()

    def get_health_status(self):
        """Get health status of all keys"""
        with self.lock:
            return {
                "total_keys": len(self.keys),
                "healthy_keys": sum(1 for k in self.keys if self._is_key_healthy(k.id)),
                "keys": [
                    {
                        "id": key.id,
                        "name": key.name,
                        "healthy": self._is_key_healthy(key.id),
                        "consecutive_failures": self.health_status.get(key.id, {}).get(
                            "consecutive_failures", 0
                        ),
                        "total_requests": key.total_requests,
                        "success_rate": key.success_rate,
                    }
                    for key in self.keys
                ],
            }

    def health_check(self, api_key):
        """
        Perform health check on a specific API key
        Returns True if key is working, False otherwise
        """
        import requests

        try:
            response = requests.post(
                "https://api.fireworks.ai/inference/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "accounts/fireworks/models/llama-v3p1-8b-instruct",
                    "messages": [{"role": "user", "content": "test"}],
                    "max_tokens": 1,
                },
                timeout=10,
            )
            return response.status_code == 200
        except Exception as e:
            print(f"Health check failed: {e}")
            return False

    def run_health_checks(self):
        """Run health checks on all keys"""
        with self.lock:
            keys_to_check = list(self.keys)

        for key in keys_to_check:
            is_healthy = self.health_check(key.api_key)

            with self.lock:
                if key.id in self.health_status:
                    self.health_status[key.id]["healthy"] = is_healthy
                    self.health_status[key.id]["last_check"] = time.time()
                    if is_healthy:
                        self.health_status[key.id]["consecutive_failures"] = 0

    def set_enabled(self, enabled):
        """Enable or disable rotation"""
        self.enabled = enabled


# Global rotator instance
rotator = APIKeyRotator()
