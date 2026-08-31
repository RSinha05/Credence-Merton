import sys
import os
import logging

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBasic, HTTPBasicCredentials, OAuth2PasswordBearer
import secrets
try:
    from config import API_TITLE, API_VERSION, API_DESCRIPTION
except ImportError:
    API_TITLE = "Credence-MertonX API"
    API_VERSION = "1.0.0"
    API_DESCRIPTION = "API for Credit Risk Engine"

from api.routes import health, corporate, retail, multi_asset, private_equity, analytics, news

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(
    title=API_TITLE,
    version=API_VERSION,
    description=API_DESCRIPTION
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


security = HTTPBasic()

def verify_credentials(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = secrets.compare_digest(credentials.username, "credence")
    correct_password = secrets.compare_digest(credentials.password, "mertonx_api_secret")
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

app.include_router(health.router)
app.include_router(corporate.router, dependencies=[Depends(verify_credentials)])
app.include_router(retail.router, dependencies=[Depends(verify_credentials)])
app.include_router(multi_asset.router, dependencies=[Depends(verify_credentials)])
app.include_router(private_equity.router, dependencies=[Depends(verify_credentials)])
app.include_router(analytics.router, dependencies=[Depends(verify_credentials)])
app.include_router(news.router, dependencies=[Depends(verify_credentials)])


@app.on_event("startup")
async def startup_event():
    """Log banner on startup."""
    logger.info(f"--- Starting {API_TITLE} v{API_VERSION} ---")

@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """Custom handler for ValueErrors."""
    logger.error(f"ValueError on {request.url}: {exc}")
    from api.schemas import ErrorResponse
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc), "error_code": "VALUE_ERROR"},
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """Custom handler for unexpected exceptions."""
    logger.exception(f"Unhandled exception on {request.url}: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error_code": "INTERNAL_ERROR"},
    )

if __name__ == '__main__':
    import uvicorn
    uvicorn.run('api.app:app', host='0.0.0.0', port=8000, reload=True)
