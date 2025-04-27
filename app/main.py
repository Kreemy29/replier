import uvicorn
import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from .api import router  # Relative import within app package
from .logging_config import setup_logging

# Setup logging
logger = setup_logging()

app = FastAPI(
    title="Ava Reply Engine",
    version="1.0.0",
    description="Thread reply generation service with DeepSeek"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# register your router from app/api.py
app.include_router(router)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests and responses"""
    logger.info(f"Request: {request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"Response: {response.status_code}")
    return response

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler to log all errors"""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

if __name__ == "__main__":
    # only runs if you do `python app/main.py`
    logger.info("Starting server")
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
