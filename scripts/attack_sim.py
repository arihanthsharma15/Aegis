import asyncio
import httpx

print(" Attack script started")

TARGET_URL = "http://127.0.0.1:8000/expensive-ai-call"
TOTAL_REQUESTS = 80
CONCURRENCY = 10   # IMPORTANT


async def send_request(client, i, semaphore):
    async with semaphore:
        try:
            response = await client.post(TARGET_URL)
            print(f"[{i}] Status: {response.status_code}")
        except Exception as e:
            print(f"[{i}] Error: {repr(e)}")


async def attack():
    semaphore = asyncio.Semaphore(CONCURRENCY)

    async with httpx.AsyncClient(timeout=10) as client:
        tasks = []
        for i in range(TOTAL_REQUESTS):
            tasks.append(send_request(client, i, semaphore))

        await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(attack())
