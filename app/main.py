import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse, HTMLResponse

from app.core.config import settings
from app.core.database import init_db, close_db
from app.core.cache import init_redis, close_redis
from app.core.logging_config import setup_logging
from app.api import auth, menu, orders, admin

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


# Lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage app startup and shutdown"""
    # Startup
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    await init_db()
    await init_redis()
    logger.info("Database and cache initialized")
    yield
    # Shutdown
    logger.info("Shutting down application")
    await close_db()
    await close_redis()


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Production-ready restaurant backend API",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Trusted hosts middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"],
)


# Exception handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "status": "error",
            "message": "Internal server error",
        },
    )


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
    }


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint"""
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "openapi": "/openapi.json",
    }


@app.get("/admin", tags=["Admin"], response_class=HTMLResponse, include_in_schema=False)
async def admin_panel():
    """Simple admin panel page for quickly accessing admin analytics endpoints."""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <title>Restaurant Admin Panel</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 2rem; background: #f7f7f7; color: #1f2937; }
            .container { max-width: 920px; margin: 0 auto; background: #fff; padding: 1.5rem; border-radius: 12px; box-shadow: 0 8px 20px rgba(0,0,0,0.08); }
            h1 { margin-top: 0; }
            .help { color: #4b5563; }
            .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 12px; margin-top: 1rem; }
            .card { border: 1px solid #e5e7eb; border-radius: 10px; padding: 1rem; background: #f9fafb; }
            .card h3 { margin: 0 0 .4rem 0; }
            code { background: #111827; color: #f9fafb; padding: .2rem .4rem; border-radius: 6px; font-size: .86rem; }
            .footer { margin-top: 1rem; color: #6b7280; font-size: .9rem; }
            ul { padding-left: 1.2rem; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Admin Panel</h1>
            <p class="help">This backend exposes admin analytics APIs. Use your <b>admin/manager JWT</b> in Swagger at <a href="/docs">/docs</a> to call endpoints securely.</p>

            <div class="grid">
                <div class="card">
                    <h3>Dashboard</h3>
                    <p>Revenue, orders and customer overview.</p>
                    <code>GET /api/admin/dashboard?restaurant_id=1</code>
                </div>
                <div class="card">
                    <h3>Daily Sales</h3>
                    <p>Sales report for a specific date.</p>
                    <code>GET /api/admin/sales/daily?restaurant_id=1&date=2026-03-27</code>
                </div>
                <div class="card">
                    <h3>Monthly Sales</h3>
                    <p>Aggregated monthly report endpoint.</p>
                    <code>GET /api/admin/sales/monthly?restaurant_id=1&year=2026&month=3</code>
                </div>
                <div class="card">
                    <h3>Active Orders</h3>
                    <p>Track current ongoing orders.</p>
                    <code>GET /api/admin/orders/active?restaurant_id=1</code>
                </div>
                <div class="card">
                    <h3>Update Order Status</h3>
                    <p>Change order state by order ID.</p>
                    <code>POST /api/admin/orders/{order_id}/status?status=preparing</code>
                </div>
            </div>

            <div class="footer">
                <ul>
                    <li>Step 1: Login via <code>POST /api/auth/login</code>.</li>
                    <li>Step 2: Authorize in Swagger with <code>Bearer &lt;access_token&gt;</code>.</li>
                    <li>Step 3: Call admin endpoints above.</li>
                </ul>
            </div>
        </div>
    </body>
    </html>
    """


# Include routers
app.include_router(auth.router)
app.include_router(menu.router)
app.include_router(orders.router)
app.include_router(admin.router)


# API documentation metadata
tags_metadata = [
    {
        "name": "Auth",
        "description": "Authentication endpoints (register, login, refresh token)",
    },
    {
        "name": "Menu",
        "description": "Menu management (products, categories)",
    },
    {
        "name": "Orders",
        "description": "Order management (create, retrieve, update status)",
    },
    {
        "name": "Admin",
        "description": "Admin panel analytics and management",
    },
    {
        "name": "Health",
        "description": "Health check endpoints",
    },
]

app.openapi_tags = tags_metadata


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )
