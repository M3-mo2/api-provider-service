"""
Background Scheduler
Handles scheduled tasks like auto-backup and health checks
"""

from apscheduler.schedulers.background import BackgroundScheduler
from backend.services.backup_service import backup_service
from backend.services.key_rotator import rotator
from backend.config import config
import atexit


class SchedulerService:
    """Background scheduler for periodic tasks"""

    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.scheduler.start()

        # Shutdown scheduler on exit
        atexit.register(lambda: self.scheduler.shutdown())

    def start(self):
        """Start all scheduled tasks"""
        # Auto-backup task
        if config.get("database.auto_backup", True):
            interval_hours = config.get("database.backup_interval_hours", 10)
            self.scheduler.add_job(
                func=self._auto_backup,
                trigger="interval",
                hours=interval_hours,
                id="auto_backup",
                name="Automatic Database Backup",
                replace_existing=True,
            )
            print(f"✓ Auto-backup scheduled every {interval_hours} hours")

        # Health check task
        if config.get("rotation.enabled", True):
            check_interval = config.get("rotation.health_check_interval", 300)
            self.scheduler.add_job(
                func=self._health_check,
                trigger="interval",
                seconds=check_interval,
                id="health_check",
                name="API Keys Health Check",
                replace_existing=True,
            )
            print(f"✓ Health check scheduled every {check_interval} seconds")

    def _auto_backup(self):
        """Perform automatic backup"""
        try:
            success, message, filename = backup_service.create_backup(
                include_logs=False
            )
            if success:
                print(f"✓ Auto-backup completed: {filename}")
            else:
                print(f"✗ Auto-backup failed: {message}")
        except Exception as e:
            print(f"✗ Auto-backup error: {e}")

    def _health_check(self):
        """Perform health check on all API keys"""
        try:
            rotator.run_health_checks()
            print("✓ Health check completed")
        except Exception as e:
            print(f"✗ Health check error: {e}")

    def stop(self):
        """Stop the scheduler"""
        self.scheduler.shutdown()


# Global scheduler instance
scheduler_service = SchedulerService()
