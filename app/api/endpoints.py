from fastapi import APIRouter
import time

router = APIRouter()


@router.get("/health")
async def health_check():
    return {"status": "ok"}


@router.post("/expensive-ai-call")
async def expensive_call():
    # Simulate costly operation
    time.sleep(1)
    return {"message": "Expensive operation completed"}
