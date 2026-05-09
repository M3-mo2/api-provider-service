"""
Monitoring and Logging Service
Tracks requests, responses, and system metrics
"""

import uuid
import time
from datetime import datetime, date
from typing import Optional, Dict, Any
from backend.database import db, RequestLog, UsageStats
from sqlalchemy import func


class MonitorService:
    """Service for monitoring and logging requests"""

    def __init__(self):
        self.active_requests = {}  # {request_id: start_time}

    def start_request(
        self, endpoint: str, method: str, client_ip: str, user_agent: str
    ) -> str:
        """
        Start tracking a request
        Returns request_id
        """
        request_id = str(uuid.uuid4())
        self.active_requests[request_id] = {
            "start_time": time.time(),
            "endpoint": endpoint,
            "method": method,
            "client_ip": client_ip,
            "user_agent": user_agent,
        }
        return request_id

    def end_request(
        self,
        request_id: str,
        api_key_id: Optional[int],
        model: Optional[str],
        status_code: int,
        input_tokens: int = 0,
        output_tokens: int = 0,
        error_message: Optional[str] = None,
    ):
        """End tracking a request and log to database"""
        if request_id not in self.active_requests:
            return

        request_info = self.active_requests.pop(request_id)

        # Calculate latency
        latency_ms = int((time.time() - request_info["start_time"]) * 1000)

        # Create log entry
        session = db.get_session()
        try:
            log = RequestLog(
                request_id=request_id,
                api_key_id=api_key_id,
                model=model,
                endpoint=request_info["endpoint"],
                method=request_info["method"],
                status_code=status_code,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=input_tokens + output_tokens,
                latency_ms=latency_ms,
                error_message=error_message,
                client_ip=request_info["client_ip"],
                user_agent=request_info["user_agent"],
                created_at=datetime.utcnow(),
            )
            session.add(log)
            session.commit()

            # Update usage stats
            self._update_usage_stats(
                session, api_key_id, model, status_code, input_tokens, output_tokens
            )

        except Exception as e:
            session.rollback()
            print(f"Error logging request: {e}")
        finally:
            session.close()

    def _update_usage_stats(
        self,
        session,
        api_key_id: Optional[int],
        model: Optional[str],
        status_code: int,
        input_tokens: int,
        output_tokens: int,
    ):
        """Update aggregated usage statistics"""
        today = date.today()

        # Find or create usage stats entry
        stats = (
            session.query(UsageStats)
            .filter(
                UsageStats.date == today,
                UsageStats.api_key_id == api_key_id,
                UsageStats.model == model,
            )
            .first()
        )

        if not stats:
            stats = UsageStats(
                date=today,
                api_key_id=api_key_id,
                model=model,
                total_requests=0,
                successful_requests=0,
                failed_requests=0,
                total_tokens=0,
                input_tokens=0,
                output_tokens=0,
                total_cost=0.0,
            )
            session.add(stats)

        # Update stats
        stats.total_requests += 1
        if 200 <= status_code < 300:
            stats.successful_requests += 1
        else:
            stats.failed_requests += 1

        stats.input_tokens += input_tokens
        stats.output_tokens += output_tokens
        stats.total_tokens += input_tokens + output_tokens

        # Calculate cost (placeholder - would need actual pricing)
        # Assuming $0.0001 per 1K input tokens, $0.0003 per 1K output tokens
        input_cost = (input_tokens / 1000) * 0.0001
        output_cost = (output_tokens / 1000) * 0.0003
        stats.total_cost += input_cost + output_cost

        session.commit()

    def get_recent_logs(self, limit: int = 100, offset: int = 0) -> list:
        """Get recent request logs"""
        session = db.get_session()
        try:
            logs = (
                session.query(RequestLog)
                .order_by(RequestLog.created_at.desc())
                .limit(limit)
                .offset(offset)
                .all()
            )

            return [log.to_dict() for log in logs]
        finally:
            session.close()

    def get_stats_summary(self, days: int = 7) -> Dict[str, Any]:
        """Get statistics summary for the last N days"""
        session = db.get_session()
        try:
            # Total requests
            total_requests = session.query(func.count(RequestLog.id)).scalar() or 0

            # Success rate
            successful = (
                session.query(func.count(RequestLog.id))
                .filter(RequestLog.status_code >= 200, RequestLog.status_code < 300)
                .scalar()
                or 0
            )

            success_rate = (
                (successful / total_requests * 100) if total_requests > 0 else 0
            )

            # Total tokens
            total_tokens = (
                session.query(func.sum(RequestLog.total_tokens)).scalar() or 0
            )
            input_tokens = (
                session.query(func.sum(RequestLog.input_tokens)).scalar() or 0
            )
            output_tokens = (
                session.query(func.sum(RequestLog.output_tokens)).scalar() or 0
            )

            # Average latency
            avg_latency = session.query(func.avg(RequestLog.latency_ms)).scalar() or 0

            # Failed requests
            failed_requests = (
                session.query(func.count(RequestLog.id))
                .filter(RequestLog.status_code >= 400)
                .scalar()
                or 0
            )

            # Total cost (from usage stats)
            total_cost = session.query(func.sum(UsageStats.total_cost)).scalar() or 0

            # Active keys count
            from backend.database import APIKey

            active_keys = (
                session.query(func.count(APIKey.id))
                .filter(APIKey.is_active == True)
                .scalar()
                or 0
            )

            return {
                "total_requests": total_requests,
                "successful_requests": successful,
                "failed_requests": failed_requests,
                "success_rate": round(success_rate, 2),
                "total_tokens": total_tokens,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "avg_latency_ms": round(avg_latency, 2),
                "total_cost": round(total_cost, 4),
                "active_keys": active_keys,
            }
        finally:
            session.close()

    def get_top_keys(self, limit: int = 5) -> list:
        """Get top API keys by usage"""
        session = db.get_session()
        try:
            from backend.database import APIKey

            keys = (
                session.query(APIKey)
                .filter(APIKey.is_active == True)
                .order_by(APIKey.total_requests.desc())
                .limit(limit)
                .all()
            )

            return [
                {
                    "id": key.id,
                    "name": key.name,
                    "total_requests": key.total_requests,
                    "success_rate": round(key.success_rate, 2),
                }
                for key in keys
            ]
        finally:
            session.close()

    def get_requests_by_endpoint(self) -> Dict[str, int]:
        """Get request count by endpoint"""
        session = db.get_session()
        try:
            results = (
                session.query(RequestLog.endpoint, func.count(RequestLog.id))
                .group_by(RequestLog.endpoint)
                .all()
            )

            return {endpoint: count for endpoint, count in results}
        finally:
            session.close()

    def get_token_usage_timeline(self, days: int = 7) -> list:
        """Get token usage over time"""
        session = db.get_session()
        try:
            from datetime import timedelta

            start_date = date.today() - timedelta(days=days)

            results = (
                session.query(
                    UsageStats.date,
                    func.sum(UsageStats.input_tokens).label("input_tokens"),
                    func.sum(UsageStats.output_tokens).label("output_tokens"),
                    func.sum(UsageStats.total_tokens).label("total_tokens"),
                )
                .filter(UsageStats.date >= start_date)
                .group_by(UsageStats.date)
                .order_by(UsageStats.date)
                .all()
            )

            return [
                {
                    "date": str(row.date),
                    "input_tokens": row.input_tokens or 0,
                    "output_tokens": row.output_tokens or 0,
                    "total_tokens": row.total_tokens or 0,
                }
                for row in results
            ]
        finally:
            session.close()


# Global monitor instance
monitor = MonitorService()
