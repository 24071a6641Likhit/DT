"""Main FastAPI application with lifespan management"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.config.settings import settings
from app.config.database import get_session_factory
from app.services.orchestrator import Orchestrator
from app.services.background_tasks import BackgroundTaskScheduler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Global instances
orchestrator: Orchestrator = None
background_scheduler: BackgroundTaskScheduler = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown."""
    global orchestrator, background_scheduler
    
    # Startup
    logger.info("Starting Smart Energy Monitoring System...")
    
    try:
        session_factory = get_session_factory()
        
        # Initialize and start orchestrator
        orchestrator = Orchestrator(session_factory)
        await orchestrator.initialize()
        orchestrator.start()
        logger.info("✓ Orchestrator started (polling every 5 seconds)")
        
        # Start background task scheduler
        background_scheduler = BackgroundTaskScheduler(session_factory)
        background_scheduler.start()
        logger.info("✓ Background scheduler started (hourly/daily summaries)")
        
        logger.info("✓ System startup complete - ready to serve requests")
        
    except Exception as e:
        logger.error(f"✗ Failed to start system: {e}", exc_info=True)
        raise
        
    yield
    
    # Shutdown
    logger.info("Shutting down...")
    
    if orchestrator:
        orchestrator.stop()
        logger.info("✓ Orchestrator stopped")
        
    if background_scheduler:
        background_scheduler.shutdown()
        logger.info("✓ Background scheduler stopped")
        
    logger.info("✓ Shutdown complete")


# Create FastAPI app with lifespan
app = FastAPI(
    title="Smart Energy Monitoring System",
    description="API for monitoring energy consumption in institutional buildings",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware (allow frontend to connect)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React/Vite dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "Smart Energy Monitoring System API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint with service status"""
    from app.services.sse_broadcaster import broadcaster
    
    return {
        "status": "healthy",
        "services": {
            "polling": orchestrator.polling_service.is_running() if orchestrator else False,
            "sse_clients": broadcaster.get_client_count()
        }
    }


# Import and register routers
from app.api.routes import dashboard, devices, alerts, billing, settings as settings_routes, historical, stream

app.include_router(dashboard.router, prefix="/api", tags=["dashboard"])
app.include_router(devices.router, prefix="/api", tags=["devices"])
app.include_router(alerts.router, prefix="/api", tags=["alerts"])
app.include_router(billing.router, prefix="/api", tags=["billing"])
app.include_router(settings_routes.router, prefix="/api", tags=["settings"])
app.include_router(historical.router, prefix="/api", tags=["historical"])
app.include_router(stream.router, tags=["stream"])

logger.info("FastAPI application initialized with all routes")
