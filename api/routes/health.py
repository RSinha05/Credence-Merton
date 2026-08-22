import time
from fastapi import APIRouter
from api.schemas import HealthResponse
try:
    from config import API_VERSION
except ImportError:
    API_VERSION = "1.0.0"

router = APIRouter(tags=['Health'])
START_TIME = time.time()

@router.get('/health', response_model=HealthResponse)
async def health_check():
    """
    Check the health status of the API.
    """
    uptime = time.time() - START_TIME
    return HealthResponse(
        status='healthy',
        version=API_VERSION,
        uptime_seconds=uptime,
        database_connected=False  # Placeholder until DB is integrated
    )
