import time
import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from routes.v1.api_router import api_v1_router
from definitions import ROOT_DIR

def create_app() -> FastAPI:
    """Application factory for Jira Release Evidence Agent Backend API."""
    app = FastAPI(
        title="Jira Release Evidence Agent API",
        description="Tool-using AI Agent backend that audits Jira evidence to determine software release readiness.",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # 1. Configure CORS Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 2. Add Request Timing & Correlation Middleware
    @app.middleware("http")
    async def add_process_time_header(request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = f"{process_time:.4f}s"
        return response

    # 3. Register Presentation Layer Routers (v1)
    app.include_router(api_v1_router)

    # 4. Root Welcome / Status Endpoint
    @app.get("/", tags=["System"])
    async def root():
        return {
            "service": "Jira Release Evidence Agent Backend",
            "version": "1.0.0",
            "documentation": "/docs",
            "status": "operational",
        }

    # 5. Global Exception Handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=500,
            content={"error": "InternalServerError", "detail": str(exc)},
        )

    return app

app = create_app()

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )

