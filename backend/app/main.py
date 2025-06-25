from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .core.config import settings
from .core.database import engine, Base
from .api.routes import alerts, config
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global scheduler instance
global_scheduler = None

app = FastAPI(
    title="Grafana-Jira Alert Manager API",
    description="API for managing Grafana alerts with Jira Service Management integration",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(alerts.router, prefix="/api/alerts", tags=["alerts"])
app.include_router(config.router, prefix="/api/config", tags=["config"])

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    global global_scheduler
    
    try:
        # Create database tables
        logger.info("📦 Creating database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database tables created successfully")
        
        # Create default cron job if none exist
        from .core.database import SessionLocal
        from .models.config import CronConfig
        
        db = SessionLocal()
        try:
            existing_jobs = db.query(CronConfig).count()
            if existing_jobs == 0:
                default_job = CronConfig(
                    job_name="alert-sync",
                    cron_expression="*/5 * * * *",
                    is_enabled=True
                )
                db.add(default_job)
                db.commit()
                logger.info("✅ Created default alert-sync cron job")
            else:
                logger.info(f"📋 Found {existing_jobs} existing cron jobs")
        except Exception as e:
            logger.error(f"❌ Error creating default job: {e}")
        finally:
            db.close()
        
        # Initialize scheduler after tables are ready
        from .services.scheduler_service import SchedulerService
        global_scheduler = SchedulerService()
        global_scheduler.ensure_jobs_loaded()
        logger.info("✅ Scheduler service initialized")
        
        logger.info("🚀 Grafana-Jira Alert Manager API started successfully")
        logger.info(f"📋 Jira URL: {settings.JIRA_URL}")
        logger.info(f"📋 Grafana URL: {settings.GRAFANA_API_URL}")
        
    except Exception as e:
        logger.error(f"❌ Startup error: {e}")

def get_global_scheduler():
    """Get the global scheduler instance"""
    return global_scheduler

@app.get("/")
async def root():
    return {
        "message": "Grafana-Jira Alert Manager API", 
        "status": "running",
        "jira_url": settings.JIRA_URL,
        "grafana_url": settings.GRAFANA_API_URL
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "grafana-jira-alert-manager-api"}