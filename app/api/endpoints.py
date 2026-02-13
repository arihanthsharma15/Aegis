import asyncio
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from app.core.config import settings
from app.services.metrics_store import metrics_store
from app.services.redis_client import get_redis

router = APIRouter()


class AttackSimulationResult(BaseModel):
    total_requests: int = Field(gt=0)
    concurrency: int = Field(gt=0)
    success_count: int = Field(ge=0)
    blocked_count: int = Field(ge=0)
    error_count: int = Field(ge=0)
    avg_latency_ms: float = Field(ge=0)
    avg_success_latency_ms: float = Field(ge=0)
    p95_latency_ms: float = Field(ge=0)
    run_at: str


@router.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/expensive-ai-call")
async def expensive_call() -> dict[str, str]:
    await asyncio.sleep(1)
    return {"message": "Expensive operation completed"}


@router.get("/dashboard")
async def dashboard() -> FileResponse:
    dashboard_file = Path(__file__).resolve().parent.parent / "static" / "dashboard.html"
    return FileResponse(dashboard_file)


@router.get("/metrics/dashboard")
async def dashboard_metrics(
    history_minutes: int = Query(default=30, ge=1, le=settings.METRICS_RETENTION_MINUTES),
) -> dict[str, Any]:
    metrics = await metrics_store.snapshot(window_minutes=history_minutes)
    metrics["redis"] = await _redis_stats()
    metrics["fastapi"] = {
        "status": "healthy",
        "uptime_seconds": metrics["uptime_seconds"],
    }
    return metrics


@router.post("/metrics/attack-simulation")
async def push_attack_simulation(result: AttackSimulationResult) -> dict[str, str]:
    await metrics_store.record_attack_result(result.model_dump())
    return {"status": "recorded"}


async def _redis_stats() -> dict[str, Any]:
    redis = await get_redis()
    info = await redis.info()

    used_memory_mb = 0.0
    if "used_memory" in info:
        used_memory_mb = round(float(info["used_memory"]) / (1024 * 1024), 2)

    return {
        "connected_clients": info.get("connected_clients", 0),
        "used_memory_mb": used_memory_mb,
        "instantaneous_ops_per_sec": info.get("instantaneous_ops_per_sec", 0),
        "keyspace_hits": info.get("keyspace_hits", 0),
        "keyspace_misses": info.get("keyspace_misses", 0),
        "uptime_in_seconds": info.get("uptime_in_seconds", 0),
    }
