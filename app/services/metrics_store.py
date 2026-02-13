from __future__ import annotations

import json
import time
from typing import Any

from app.core.config import settings
from app.services.redis_client import get_redis

METRIC_PREFIX = "aegis:metrics"
REQUESTS_TOTAL_KEY = f"{METRIC_PREFIX}:total:requests"
BLOCKED_TOTAL_KEY = f"{METRIC_PREFIX}:total:blocked"
RATE_LIMIT_TOTAL_KEY = f"{METRIC_PREFIX}:total:rate_limit_hits"
ATTACK_RESULTS_KEY = f"{METRIC_PREFIX}:attack_results"


class MetricsStore:
    """Redis-backed metrics store with minute-level history retention."""

    def __init__(self) -> None:
        self.started_at = int(time.time())

    async def record_request(self) -> None:
        redis = await get_redis()
        current_minute = self._current_minute()
        minute_key = self._minute_key("requests", current_minute)

        pipeline = redis.pipeline(transaction=False)
        pipeline.incr(minute_key)
        pipeline.expire(minute_key, settings.METRICS_RETENTION_MINUTES * 60)
        pipeline.incr(REQUESTS_TOTAL_KEY)
        await pipeline.execute()

    async def record_blocked_request(self) -> None:
        redis = await get_redis()
        current_minute = self._current_minute()

        blocked_key = self._minute_key("blocked", current_minute)
        rate_limit_key = self._minute_key("rate_limit_hits", current_minute)

        pipeline = redis.pipeline(transaction=False)
        pipeline.incr(blocked_key)
        pipeline.expire(blocked_key, settings.METRICS_RETENTION_MINUTES * 60)
        pipeline.incr(rate_limit_key)
        pipeline.expire(rate_limit_key, settings.METRICS_RETENTION_MINUTES * 60)
        pipeline.incr(BLOCKED_TOTAL_KEY)
        pipeline.incr(RATE_LIMIT_TOTAL_KEY)
        await pipeline.execute()

    async def record_attack_result(self, result: dict[str, Any]) -> None:
        redis = await get_redis()

        payload = {
            **result,
            "ingested_at": int(time.time()),
        }

        pipeline = redis.pipeline(transaction=False)
        pipeline.lpush(ATTACK_RESULTS_KEY, json.dumps(payload))
        pipeline.ltrim(ATTACK_RESULTS_KEY, 0, settings.ATTACK_RESULTS_LIMIT - 1)
        await pipeline.execute()

    async def snapshot(self, window_minutes: int = 30) -> dict[str, Any]:
        redis = await get_redis()

        safe_window = max(1, min(window_minutes, settings.METRICS_RETENTION_MINUTES))
        current_minute = self._current_minute()
        start_minute = current_minute - (safe_window - 1)

        request_keys = self._minute_keys("requests", start_minute, safe_window)
        blocked_keys = self._minute_keys("blocked", start_minute, safe_window)
        rate_limit_keys = self._minute_keys("rate_limit_hits", start_minute, safe_window)

        pipeline = redis.pipeline(transaction=False)
        for key in request_keys:
            pipeline.get(key)
        for key in blocked_keys:
            pipeline.get(key)
        for key in rate_limit_keys:
            pipeline.get(key)
        pipeline.mget([REQUESTS_TOTAL_KEY, BLOCKED_TOTAL_KEY, RATE_LIMIT_TOTAL_KEY])
        pipeline.lrange(ATTACK_RESULTS_KEY, 0, settings.ATTACK_RESULTS_LIMIT - 1)
        results = await pipeline.execute()

        req_raw = results[0:safe_window]
        blocked_raw = results[safe_window : 2 * safe_window]
        rate_limit_raw = results[2 * safe_window : 3 * safe_window]
        totals_raw = results[3 * safe_window]
        attack_raw = results[3 * safe_window + 1]

        requests_values = [int(v or 0) for v in req_raw]
        blocked_values = [int(v or 0) for v in blocked_raw]
        rate_limit_values = [int(v or 0) for v in rate_limit_raw]

        labels = self._labels(start_minute, safe_window)

        requests_last_minute = requests_values[-1] if requests_values else 0
        blocked_last_minute = blocked_values[-1] if blocked_values else 0
        rate_limit_last_minute = rate_limit_values[-1] if rate_limit_values else 0

        latest_active_requests = self._latest_non_zero(requests_values)
        latest_active_blocked = self._latest_non_zero(blocked_values)
        latest_active_rate_limit = self._latest_non_zero(rate_limit_values)

        total_requests = int((totals_raw[0] if totals_raw else 0) or 0)
        total_blocked = int((totals_raw[1] if totals_raw else 0) or 0)
        total_rate_limit = int((totals_raw[2] if totals_raw else 0) or 0)

        block_ratio = (total_blocked / total_requests * 100.0) if total_requests else 0.0

        attack_results: list[dict[str, Any]] = []
        for item in attack_raw or []:
            try:
                attack_results.append(json.loads(item))
            except json.JSONDecodeError:
                continue

        return {
            "uptime_seconds": int(time.time()) - self.started_at,
            "history_window_minutes": safe_window,
            "history_retention_minutes": settings.METRICS_RETENTION_MINUTES,
            "requests_per_minute": requests_last_minute,
            "blocked_requests_per_minute": blocked_last_minute,
            "rate_limit_hits_per_minute": rate_limit_last_minute,
            "requests_per_minute_latest_active": latest_active_requests,
            "blocked_requests_per_minute_latest_active": latest_active_blocked,
            "rate_limit_hits_per_minute_latest_active": latest_active_rate_limit,
            "totals": {
                "requests": total_requests,
                "blocked": total_blocked,
                "rate_limit_hits": total_rate_limit,
            },
            "series": {
                "requests": {"labels": labels, "values": requests_values},
                "blocked": {"labels": labels, "values": blocked_values},
                "rate_limit_hits": {"labels": labels, "values": rate_limit_values},
            },
            "attack_simulation_results": attack_results,
            "stack_suggestion": self._stack_suggestion(block_ratio, latest_active_requests),
        }

    @staticmethod
    def _current_minute() -> int:
        return int(time.time() // 60)

    @staticmethod
    def _minute_key(metric: str, minute_epoch: int) -> str:
        return f"{METRIC_PREFIX}:{metric}:{minute_epoch}"

    def _minute_keys(self, metric: str, start_minute: int, minutes: int) -> list[str]:
        return [self._minute_key(metric, start_minute + i) for i in range(minutes)]

    @staticmethod
    def _labels(start_minute: int, minutes: int) -> list[str]:
        labels: list[str] = []
        time_format = "%m-%d %H:%M" if minutes > 180 else "%H:%M"

        for i in range(minutes):
            minute = start_minute + i
            labels.append(time.strftime(time_format, time.localtime(minute * 60)))

        return labels

    @staticmethod
    def _latest_non_zero(values: list[int]) -> int:
        for value in reversed(values):
            if value > 0:
                return value
        return 0

    @staticmethod
    def _stack_suggestion(block_ratio: float, rpm: int) -> dict[str, Any]:
        recommendations: list[str] = []

        if rpm > 80:
            recommendations.append("Add API gateway + autoscaling workers for burst handling.")
        if block_ratio > 20:
            recommendations.append("Add WAF rules and IP reputation checks before FastAPI.")
        if block_ratio > 35:
            recommendations.append("Introduce CAPTCHA/challenge flow for suspicious clients.")

        if not recommendations:
            recommendations = [
                "Current stack is healthy. Next upgrade: Prometheus + Grafana for long-term observability.",
            ]

        return {
            "risk_level": "high" if block_ratio > 35 else "medium" if block_ratio > 15 else "low",
            "recommendations": recommendations,
        }


metrics_store = MetricsStore()
