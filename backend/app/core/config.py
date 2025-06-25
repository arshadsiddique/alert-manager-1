from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/alertdb"
    
    # Grafana
    GRAFANA_API_URL: str = "https://grafana.observability.devo.com"
    GRAFANA_API_KEY: str = ""
    
    # JSM (Jira Service Management) API Settings
    JIRA_URL: str = "https://devoinc.atlassian.net"  # Your Atlassian instance URL
    JIRA_USER_EMAIL: str = ""                        # Your email address
    JIRA_API_TOKEN: str = ""                         # Your Atlassian API token
    
    # JSM Cloud ID (will be auto-retrieved if not provided)
    JSM_CLOUD_ID: Optional[str] = None               # UUID format cloud ID
    
    # JSM API Configuration
    JSM_API_BASE_URL: str = "https://api.atlassian.com/jsm/ops/api"
    JSM_ALERTS_LIMIT: int = 500                      # Max alerts to fetch per request
    
    # Alert Matching Configuration
    ALERT_MATCH_CONFIDENCE_THRESHOLD: float = 50.0   # Minimum confidence for auto-matching
    ALERT_MATCH_TIME_WINDOW_MINUTES: int = 15        # Time window for matching alerts
    
    # Sync Configuration
    GRAFANA_SYNC_INTERVAL_SECONDS: int = 300         # Sync every 5 minutes (reduced from 10 minutes)
    JSM_SYNC_INTERVAL_SECONDS: int = 300             # Sync JSM alerts every 5 minutes
    
    # Alert Filtering
    FILTER_NON_PROD_ALERTS: bool = True              # Filter out non-production alerts
    EXCLUDED_CLUSTERS: list = ["stage", "dev", "test"] # Clusters to exclude
    EXCLUDED_ENVIRONMENTS: list = ["devo-stage-eu"]  # Environments to exclude
    
    # App
    DEBUG: bool = False
    SECRET_KEY: str = "your-secret-key-here"
    
    # CORS
    ALLOWED_ORIGINS: list = ["http://localhost:3000", "http://localhost:3001"]
    
    # Legacy Jira Settings (deprecated but kept for backwards compatibility)
    JIRA_PROJECT_KEY: str = "OP"                     # Not used in JSM mode
    JIRA_INCIDENT_ISSUE_TYPE: str = "Incident"      # Not used in JSM mode
    JIRA_ACKNOWLEDGE_TRANSITION_NAME: str = "To Do" # Not used in JSM mode
    JIRA_RESOLVE_TRANSITION_NAME: str = "Completed" # Not used in JSM mode
    
    # Feature Flags
    USE_JSM_MODE: bool = True                        # Use JSM API instead of Jira issues
    ENABLE_AUTO_CLOSE: bool = True                   # Auto-close JSM alerts when Grafana resolves
    ENABLE_MATCH_LOGGING: bool = False               # Log detailed matching information
    
    class Config:
        env_file = ".env"

settings = Settings()
