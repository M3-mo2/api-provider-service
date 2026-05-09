"""
Backup and Restore Service
Handles database backups and restoration
"""

import json
import os
import hashlib
from datetime import datetime
from typing import Optional, Dict, Any
from backend.database import db, APIKey, Model, Config, UsageStats, RequestLog


class BackupService:
    """Service for backup and restore operations"""

    def __init__(self):
        self.backup_path = "data/backups"
        os.makedirs(self.backup_path, exist_ok=True)

    def create_backup(
        self, include_logs: bool = False
    ) -> tuple[bool, str, Optional[str]]:
        """
        Create a backup of the database
        Returns: (success, message, backup_filename)
        """
        session = db.get_session()
        try:
            # Collect data
            backup_data = {
                "version": "1.0.0",
                "timestamp": datetime.utcnow().isoformat(),
                "data": {},
            }

            # Backup API keys
            api_keys = session.query(APIKey).all()
            backup_data["data"]["api_keys"] = [
                {
                    "name": key.name,
                    "api_key": key.api_key,
                    "is_active": key.is_active,
                    "priority": key.priority,
                    "created_at": key.created_at.isoformat()
                    if key.created_at
                    else None,
                    "total_requests": key.total_requests,
                    "failed_requests": key.failed_requests,
                    "success_rate": key.success_rate,
                }
                for key in api_keys
            ]

            # Backup models
            models = session.query(Model).all()
            backup_data["data"]["models"] = [
                {
                    "name": model.name,
                    "fireworks_model_id": model.fireworks_model_id,
                    "display_name": model.display_name,
                    "description": model.description,
                    "is_active": model.is_active,
                    "model_type": model.model_type,
                    "context_length": model.context_length,
                    "input_price": model.input_price,
                    "output_price": model.output_price,
                }
                for model in models
            ]

            # Backup config
            configs = session.query(Config).all()
            backup_data["data"]["config"] = [
                {"key": cfg.key, "value": cfg.value, "description": cfg.description}
                for cfg in configs
            ]

            # Backup usage stats
            usage_stats = session.query(UsageStats).all()
            backup_data["data"]["usage_stats"] = [
                {
                    "date": stat.date.isoformat() if stat.date else None,
                    "api_key_id": stat.api_key_id,
                    "model": stat.model,
                    "total_requests": stat.total_requests,
                    "successful_requests": stat.successful_requests,
                    "failed_requests": stat.failed_requests,
                    "total_tokens": stat.total_tokens,
                    "input_tokens": stat.input_tokens,
                    "output_tokens": stat.output_tokens,
                    "total_cost": stat.total_cost,
                }
                for stat in usage_stats
            ]

            # Optionally backup request logs
            if include_logs:
                logs = session.query(RequestLog).all()
                backup_data["data"]["request_logs"] = [
                    {
                        "request_id": log.request_id,
                        "api_key_id": log.api_key_id,
                        "model": log.model,
                        "endpoint": log.endpoint,
                        "method": log.method,
                        "status_code": log.status_code,
                        "input_tokens": log.input_tokens,
                        "output_tokens": log.output_tokens,
                        "total_tokens": log.total_tokens,
                        "latency_ms": log.latency_ms,
                        "error_message": log.error_message,
                        "client_ip": log.client_ip,
                        "created_at": log.created_at.isoformat()
                        if log.created_at
                        else None,
                    }
                    for log in logs
                ]

            # Calculate checksum
            data_str = json.dumps(backup_data["data"], sort_keys=True)
            checksum = hashlib.sha256(data_str.encode()).hexdigest()
            backup_data["checksum"] = checksum

            # Save to file
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"backup_{timestamp}.json"
            filepath = os.path.join(self.backup_path, filename)

            with open(filepath, "w") as f:
                json.dump(backup_data, f, indent=2)

            return True, f"Backup created successfully: {filename}", filename

        except Exception as e:
            return False, f"Backup failed: {str(e)}", None
        finally:
            session.close()

    def restore_backup(self, filename: str) -> tuple[bool, str]:
        """
        Restore database from backup file
        Returns: (success, message)
        """
        filepath = os.path.join(self.backup_path, filename)

        if not os.path.exists(filepath):
            return False, f"Backup file not found: {filename}"

        try:
            # Load backup file
            with open(filepath, "r") as f:
                backup_data = json.load(f)

            # Verify checksum
            data_str = json.dumps(backup_data["data"], sort_keys=True)
            checksum = hashlib.sha256(data_str.encode()).hexdigest()

            if checksum != backup_data.get("checksum"):
                return False, "Backup file corrupted (checksum mismatch)"

            session = db.get_session()
            try:
                # Clear existing data
                session.query(RequestLog).delete()
                session.query(UsageStats).delete()
                session.query(APIKey).delete()
                session.query(Model).delete()
                session.query(Config).delete()
                session.commit()

                # Restore API keys
                for key_data in backup_data["data"].get("api_keys", []):
                    key = APIKey(
                        name=key_data["name"],
                        api_key=key_data["api_key"],
                        is_active=key_data.get("is_active", True),
                        priority=key_data.get("priority", 0),
                        total_requests=key_data.get("total_requests", 0),
                        failed_requests=key_data.get("failed_requests", 0),
                        success_rate=key_data.get("success_rate", 100.0),
                    )
                    session.add(key)

                # Restore models
                for model_data in backup_data["data"].get("models", []):
                    model = Model(
                        name=model_data["name"],
                        fireworks_model_id=model_data["fireworks_model_id"],
                        display_name=model_data.get("display_name"),
                        description=model_data.get("description"),
                        is_active=model_data.get("is_active", True),
                        model_type=model_data.get("model_type"),
                        context_length=model_data.get("context_length"),
                        input_price=model_data.get("input_price"),
                        output_price=model_data.get("output_price"),
                    )
                    session.add(model)

                # Restore config
                for cfg_data in backup_data["data"].get("config", []):
                    cfg = Config(
                        key=cfg_data["key"],
                        value=cfg_data["value"],
                        description=cfg_data.get("description"),
                    )
                    session.add(cfg)

                # Restore usage stats
                for stat_data in backup_data["data"].get("usage_stats", []):
                    stat = UsageStats(
                        date=datetime.fromisoformat(stat_data["date"]).date()
                        if stat_data.get("date")
                        else None,
                        api_key_id=stat_data.get("api_key_id"),
                        model=stat_data.get("model"),
                        total_requests=stat_data.get("total_requests", 0),
                        successful_requests=stat_data.get("successful_requests", 0),
                        failed_requests=stat_data.get("failed_requests", 0),
                        total_tokens=stat_data.get("total_tokens", 0),
                        input_tokens=stat_data.get("input_tokens", 0),
                        output_tokens=stat_data.get("output_tokens", 0),
                        total_cost=stat_data.get("total_cost", 0.0),
                    )
                    session.add(stat)

                # Restore request logs if present
                for log_data in backup_data["data"].get("request_logs", []):
                    log = RequestLog(
                        request_id=log_data["request_id"],
                        api_key_id=log_data.get("api_key_id"),
                        model=log_data.get("model"),
                        endpoint=log_data.get("endpoint"),
                        method=log_data.get("method"),
                        status_code=log_data.get("status_code"),
                        input_tokens=log_data.get("input_tokens", 0),
                        output_tokens=log_data.get("output_tokens", 0),
                        total_tokens=log_data.get("total_tokens", 0),
                        latency_ms=log_data.get("latency_ms"),
                        error_message=log_data.get("error_message"),
                        client_ip=log_data.get("client_ip"),
                    )
                    session.add(log)

                session.commit()

                return True, f"Backup restored successfully from {filename}"

            except Exception as e:
                session.rollback()
                return False, f"Restore failed: {str(e)}"
            finally:
                session.close()

        except Exception as e:
            return False, f"Failed to read backup file: {str(e)}"

    def list_backups(self) -> list:
        """List all available backup files"""
        try:
            files = [f for f in os.listdir(self.backup_path) if f.endswith(".json")]
            backups = []

            for filename in sorted(files, reverse=True):
                filepath = os.path.join(self.backup_path, filename)
                stat = os.stat(filepath)

                backups.append(
                    {
                        "filename": filename,
                        "size": stat.st_size,
                        "created_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    }
                )

            return backups
        except Exception as e:
            print(f"Error listing backups: {e}")
            return []

    def delete_backup(self, filename: str) -> tuple[bool, str]:
        """Delete a backup file"""
        filepath = os.path.join(self.backup_path, filename)

        if not os.path.exists(filepath):
            return False, f"Backup file not found: {filename}"

        try:
            os.remove(filepath)
            return True, f"Backup deleted: {filename}"
        except Exception as e:
            return False, f"Failed to delete backup: {str(e)}"


# Global backup service instance
backup_service = BackupService()
