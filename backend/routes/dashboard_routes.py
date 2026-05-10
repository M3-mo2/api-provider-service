"""
Dashboard API routes
Handles all dashboard-related API endpoints
"""

from flask import Blueprint, request, jsonify
from backend.middleware.auth_middleware import require_auth, AuthMiddleware
from backend.database import db, APIKey, Model, Config
from backend.services.key_rotator import rotator
from backend.services.monitor_service import monitor
from backend.services.backup_service import backup_service
from backend.config import config
from datetime import datetime

dashboard_bp = Blueprint("dashboard", __name__)


# Authentication endpoints
@dashboard_bp.route("/api/auth/login", methods=["POST"])
def login():
    """Login endpoint"""
    data = request.get_json()

    if not data or "username" not in data or "password" not in data:
        return jsonify({"error": "Username and password required"}), 400

    success, result = AuthMiddleware.authenticate(data["username"], data["password"])

    if success:
        return jsonify({"token": result, "username": data["username"]}), 200
    else:
        return jsonify({"error": result}), 401


@dashboard_bp.route("/api/auth/verify", methods=["GET"])
@require_auth
def verify_token():
    """Verify token endpoint"""
    return jsonify({"valid": True, "username": request.username}), 200


# Statistics endpoints
@dashboard_bp.route("/api/dashboard/stats", methods=["GET"])
@require_auth
def get_stats():
    """Get dashboard statistics"""
    try:
        stats = monitor.get_stats_summary()
        top_keys = monitor.get_top_keys(limit=5)
        requests_by_endpoint = monitor.get_requests_by_endpoint()
        token_timeline = monitor.get_token_usage_timeline(days=7)

        return jsonify(
            {
                "stats": stats,
                "top_keys": top_keys,
                "requests_by_endpoint": requests_by_endpoint,
                "token_timeline": token_timeline,
            }
        ), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# API Keys endpoints
@dashboard_bp.route("/api/dashboard/keys", methods=["GET"])
@require_auth
def get_keys():
    """Get all API keys"""
    try:
        session = db.get_session()
        keys = session.query(APIKey).all()
        session.close()

        return jsonify([key.to_dict() for key in keys]), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@dashboard_bp.route("/api/dashboard/keys", methods=["POST"])
@require_auth
def create_key():
    """Create new API key"""
    try:
        data = request.get_json()

        if not data or "name" not in data or "api_key" not in data:
            return jsonify({"error": "Name and api_key required"}), 400

        session = db.get_session()

        # Check if key already exists
        existing = (
            session.query(APIKey).filter(APIKey.api_key == data["api_key"]).first()
        )
        if existing:
            session.close()
            return jsonify({"error": "API key already exists"}), 400

        # Create new key
        new_key = APIKey(
            name=data["name"],
            api_key=data["api_key"],
            is_active=data.get("is_active", True),
            priority=data.get("priority", 0),
        )

        session.add(new_key)
        session.commit()

        result = new_key.to_dict()
        session.close()

        # Reload keys in rotator
        rotator.load_keys()

        return jsonify(result), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@dashboard_bp.route("/api/dashboard/keys/<int:key_id>", methods=["PUT"])
@require_auth
def update_key(key_id):
    """Update API key"""
    try:
        data = request.get_json()

        session = db.get_session()
        key = session.query(APIKey).filter(APIKey.id == key_id).first()

        if not key:
            session.close()
            return jsonify({"error": "Key not found"}), 404

        # Update fields
        if "name" in data:
            key.name = data["name"]
        if "api_key" in data:
            key.api_key = data["api_key"]
        if "is_active" in data:
            key.is_active = data["is_active"]
        if "priority" in data:
            key.priority = data["priority"]

        key.updated_at = datetime.utcnow()

        session.commit()
        result = key.to_dict()
        session.close()

        # Reload keys in rotator
        rotator.load_keys()

        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@dashboard_bp.route("/api/dashboard/keys/<int:key_id>", methods=["DELETE"])
@require_auth
def delete_key(key_id):
    """Delete API key"""
    try:
        session = db.get_session()
        key = session.query(APIKey).filter(APIKey.id == key_id).first()

        if not key:
            session.close()
            return jsonify({"error": "Key not found"}), 404

        session.delete(key)
        session.commit()
        session.close()

        # Reload keys in rotator
        rotator.load_keys()

        return jsonify({"message": "Key deleted successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@dashboard_bp.route("/api/dashboard/keys/<int:key_id>/check", methods=["POST"])
@require_auth
def check_key(key_id):
    """Check if an API key is valid by sending a test request to Fireworks"""
    import httpx

    try:
        session = db.get_session()
        key = session.query(APIKey).filter(APIKey.id == key_id).first()

        if not key:
            session.close()
            return jsonify({"error": "Key not found"}), 404

        api_key = key.api_key
        key_name = key.name
        session.close()

        fireworks_url = "https://api.fireworks.ai/inference/v1/chat/completions"
        test_payload = {
            "model": "accounts/fireworks/models/kimi-k2p6",
            "messages": [{"role": "user", "content": "Hi"}],
            "max_tokens": 1,
            "stream": False,
        }

        start_time = datetime.utcnow()

        try:
            with httpx.Client(timeout=30) as client:
                response = client.post(
                    fireworks_url,
                    json=test_payload,
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                )

            latency_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)

            if response.status_code == 200:
                return jsonify(
                    {
                        "valid": True,
                        "key_name": key_name,
                        "status_code": response.status_code,
                        "latency_ms": latency_ms,
                        "message": "Key is valid and working",
                    }
                ), 200
            else:
                try:
                    error_detail = response.json()
                    error_msg = error_detail.get("error", {}).get(
                        "message", response.text[:200]
                    )
                except Exception:
                    error_msg = response.text[:200]

                return jsonify(
                    {
                        "valid": False,
                        "key_name": key_name,
                        "status_code": response.status_code,
                        "latency_ms": latency_ms,
                        "message": f"Key check failed: {error_msg}",
                    }
                ), 200

        except httpx.TimeoutException:
            return jsonify(
                {
                    "valid": False,
                    "key_name": key_name,
                    "status_code": 0,
                    "latency_ms": 0,
                    "message": "Request timed out after 30 seconds",
                }
            ), 200
        except Exception as e:
            return jsonify(
                {
                    "valid": False,
                    "key_name": key_name,
                    "status_code": 0,
                    "latency_ms": 0,
                    "message": f"Connection error: {str(e)}",
                }
            ), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@dashboard_bp.route("/api/dashboard/keys/health", methods=["GET"])
@require_auth
def get_keys_health():
    """Get health status of all keys"""
    try:
        health = rotator.get_health_status()
        return jsonify(health), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Models endpoints
@dashboard_bp.route("/api/dashboard/models", methods=["GET"])
@require_auth
def get_models():
    """Get all models"""
    try:
        session = db.get_session()
        models = session.query(Model).all()
        session.close()

        return jsonify([model.to_dict() for model in models]), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@dashboard_bp.route("/api/dashboard/models", methods=["POST"])
@require_auth
def create_model():
    """Create new model"""
    try:
        data = request.get_json()

        if not data or "name" not in data or "fireworks_model_id" not in data:
            return jsonify({"error": "Name and fireworks_model_id required"}), 400

        session = db.get_session()

        new_model = Model(
            name=data["name"],
            fireworks_model_id=data["fireworks_model_id"],
            display_name=data.get("display_name"),
            description=data.get("description"),
            is_active=data.get("is_active", True),
            model_type=data.get("model_type"),
            context_length=data.get("context_length"),
            input_price=data.get("input_price"),
            output_price=data.get("output_price"),
        )

        session.add(new_model)
        session.commit()

        result = new_model.to_dict()
        session.close()

        return jsonify(result), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@dashboard_bp.route("/api/dashboard/models/<int:model_id>", methods=["PUT"])
@require_auth
def update_model(model_id):
    """Update model"""
    try:
        data = request.get_json()

        session = db.get_session()
        model = session.query(Model).filter(Model.id == model_id).first()

        if not model:
            session.close()
            return jsonify({"error": "Model not found"}), 404

        # Update fields
        if "name" in data:
            model.name = data["name"]
        if "fireworks_model_id" in data:
            model.fireworks_model_id = data["fireworks_model_id"]
        if "display_name" in data:
            model.display_name = data["display_name"]
        if "description" in data:
            model.description = data["description"]
        if "is_active" in data:
            model.is_active = data["is_active"]
        if "model_type" in data:
            model.model_type = data["model_type"]
        if "context_length" in data:
            model.context_length = data["context_length"]
        if "input_price" in data:
            model.input_price = data["input_price"]
        if "output_price" in data:
            model.output_price = data["output_price"]

        session.commit()
        result = model.to_dict()
        session.close()

        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@dashboard_bp.route("/api/dashboard/models/<int:model_id>", methods=["DELETE"])
@require_auth
def delete_model(model_id):
    """Delete model"""
    try:
        session = db.get_session()
        model = session.query(Model).filter(Model.id == model_id).first()

        if not model:
            session.close()
            return jsonify({"error": "Model not found"}), 404

        session.delete(model)
        session.commit()
        session.close()

        return jsonify({"message": "Model deleted successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Logs endpoints
@dashboard_bp.route("/api/dashboard/logs", methods=["GET"])
@require_auth
def get_logs():
    """Get request logs"""
    try:
        limit = request.args.get("limit", 100, type=int)
        offset = request.args.get("offset", 0, type=int)

        logs = monitor.get_recent_logs(limit=limit, offset=offset)

        return jsonify(logs), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Backup endpoints
@dashboard_bp.route("/api/dashboard/backup", methods=["POST"])
@require_auth
def create_backup():
    """Create backup"""
    try:
        data = request.get_json() or {}
        include_logs = data.get("include_logs", False)

        success, message, filename = backup_service.create_backup(
            include_logs=include_logs
        )

        if success:
            return jsonify({"message": message, "filename": filename}), 200
        else:
            return jsonify({"error": message}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@dashboard_bp.route("/api/dashboard/backup/list", methods=["GET"])
@require_auth
def list_backups():
    """List all backups"""
    try:
        backups = backup_service.list_backups()
        return jsonify(backups), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@dashboard_bp.route("/api/dashboard/backup/restore", methods=["POST"])
@require_auth
def restore_backup():
    """Restore from backup"""
    try:
        data = request.get_json()

        if not data or "filename" not in data:
            return jsonify({"error": "Filename required"}), 400

        success, message = backup_service.restore_backup(data["filename"])

        if success:
            # Reload keys after restore
            rotator.load_keys()
            return jsonify({"message": message}), 200
        else:
            return jsonify({"error": message}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Config endpoints
@dashboard_bp.route("/api/dashboard/config", methods=["GET"])
@require_auth
def get_config():
    """Get configuration"""
    try:
        return jsonify(config.get_all()), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@dashboard_bp.route("/api/dashboard/config", methods=["PUT"])
@require_auth
def update_config():
    """Update configuration"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "Configuration data required"}), 400

        # Update config
        for key, value in data.items():
            config.set(key, value)

        # Save to file
        config.save()

        # Reload rate limiter config
        from backend.middleware.rate_limit_middleware import rate_limiter

        rate_limiter.load_config()

        return jsonify({"message": "Configuration updated successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
