from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session
from sqlalchemy.exc import ProgrammingError
from ..core.database import SessionLocal
from ..models.config import CronConfig
from .alert_service import AlertService
import logging

logger = logging.getLogger(__name__)

class SchedulerService:
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.alert_service = AlertService()
        self.scheduler.start()
        # Don't load jobs immediately - wait for tables to be created
        self._jobs_loaded = False
        logger.info("📅 Scheduler service initialized (jobs will be loaded later)")
    
    def ensure_jobs_loaded(self):
        """Lazy loading of jobs - only load when needed and tables exist"""
        if not self._jobs_loaded:
            try:
                self._load_jobs()
                self._jobs_loaded = True
            except Exception as e:
                logger.warning(f"Could not load jobs yet: {e}")
    
    def _load_jobs(self):
        """Load cron jobs from database"""
        db = SessionLocal()
        try:
            configs = db.query(CronConfig).filter(CronConfig.is_enabled == True).all()
            for config in configs:
                self._add_job(config)
            logger.info(f"✅ Loaded {len(configs)} cron jobs into scheduler")
        except ProgrammingError as e:
            logger.warning(f"⚠️  Tables not ready yet: {e}")
            raise  # Re-raise so caller knows it failed
        except Exception as e:
            logger.error(f"❌ Error loading jobs: {e}")
            raise
        finally:
            db.close()
    
    def _add_job(self, config: CronConfig):
        """Add a cron job to scheduler"""
        try:
            trigger = CronTrigger.from_crontab(config.cron_expression)
            self.scheduler.add_job(
                func=self._sync_alerts_job,
                trigger=trigger,
                id=f"job_{config.job_name}",
                replace_existing=True
            )
            logger.info(f"➕ Added job {config.job_name} with expression {config.cron_expression}")
        except Exception as e:
            logger.error(f"❌ Error adding job {config.job_name}: {e}")
    
    async def _sync_alerts_job(self):
        """Job function to sync alerts"""
        db = SessionLocal()
        try:
            logger.info("🔄 Running scheduled alert sync...")
            await self.alert_service.sync_alerts(db)
            logger.info("✅ Scheduled alert sync completed")
        except Exception as e:
            logger.error(f"❌ Error in scheduled alert sync: {e}")
        finally:
            db.close()
    
    def update_job(self, job_name: str, cron_expression: str):
        """Update a cron job"""
        try:
            trigger = CronTrigger.from_crontab(cron_expression)
            self.scheduler.modify_job(
                job_id=f"job_{job_name}",
                trigger=trigger
            )
            logger.info(f"🔄 Updated job {job_name} with expression {cron_expression}")
        except Exception as e:
            logger.error(f"❌ Error updating job {job_name}: {e}")
    
    def remove_job(self, job_name: str):
        """Remove a cron job"""
        try:
            self.scheduler.remove_job(f"job_{job_name}")
            logger.info(f"🗑️  Removed job {job_name}")
        except Exception as e:
            logger.error(f"❌ Error removing job {job_name}: {e}")