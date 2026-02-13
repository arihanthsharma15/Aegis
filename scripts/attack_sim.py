import asyncio
import statistics
import time
from datetime import datetime, timezone

import httpx

TARGET_URL = "http://127.0.0.1:8000/expensive-ai-call"
METRICS_URL = "http://127.0.0.1:8000/metrics/attack-simulation"
TOTAL_REQUESTS = 80
CONCURRENCY = 10


async def send_request(
    client: httpx.AsyncClient,
    i: int,
    semaphore: asyncio.Semaphore,
    latencies: list[float],
    success_latencies: list[float],
    statuses: list[int],
    errors: list[str],
) -> None:
    async with semaphore:
        start = time.perf_counter()
        try:
            response = await client.post(TARGET_URL)
            elapsed_ms = (time.perf_counter() - start) * 1000
            latencies.append(elapsed_ms)
            statuses.append(response.status_code)
            if response.status_code == 200:
                success_latencies.append(elapsed_ms)
            print(f"[{i}] Status: {response.status_code} | {elapsed_ms:.1f}ms")
        except Exception as exc:
            errors.append(repr(exc))
            print(f"[{i}] Error: {repr(exc)}")


async def attack() -> None:
    print("Attack script started")

    semaphore = asyncio.Semaphore(CONCURRENCY)
    statuses: list[int] = []
    latencies: list[float] = []
    success_latencies: list[float] = []
    errors: list[str] = []

    async with httpx.AsyncClient(timeout=10) as client:
        tasks = [
            send_request(client, i, semaphore, latencies, success_latencies, statuses, errors)
            for i in range(TOTAL_REQUESTS)
        ]
        await asyncio.gather(*tasks)

        success_count = sum(1 for status in statuses if status == 200)
        blocked_count = sum(1 for status in statuses if status == 429)
        error_count = len(errors)

        avg_latency = statistics.mean(latencies) if latencies else 0.0
        avg_success_latency = statistics.mean(success_latencies) if success_latencies else 0.0
        p95_latency = statistics.quantiles(latencies, n=20)[18] if len(latencies) >= 20 else avg_latency

        summary = {
            "total_requests": TOTAL_REQUESTS,
            "concurrency": CONCURRENCY,
            "success_count": success_count,
            "blocked_count": blocked_count,
            "error_count": error_count,
            "avg_latency_ms": round(avg_latency, 2),
            "avg_success_latency_ms": round(avg_success_latency, 2),
            "p95_latency_ms": round(p95_latency, 2),
            "run_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        }

        print("\nAttack summary:")
        for key, value in summary.items():
            print(f"- {key}: {value}")

        try:
            response = await client.post(METRICS_URL, json=summary)
            print(f"\nMetrics pushed: {response.status_code}")
        except Exception as exc:
            print(f"\nCould not push metrics: {repr(exc)}")


if __name__ == "__main__":
    asyncio.run(attack())
