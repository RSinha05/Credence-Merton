import re
with open('api/app.py', 'r') as f:
    content = f.read()

imports_addition = """from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBasic, HTTPBasicCredentials, OAuth2PasswordBearer
import secrets"""

content = content.replace("from fastapi import FastAPI, Request\nfrom fastapi.responses import JSONResponse\nfrom fastapi.middleware.cors import CORSMiddleware", imports_addition)

auth_code = """
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
"""

content = content.replace("app.include_router(health.router)\napp.include_router(corporate.router)\napp.include_router(retail.router)\napp.include_router(multi_asset.router)", auth_code)

with open('api/app.py', 'w') as f:
    f.write(content)
