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
    
    # Alert Matching Configuration (Updated for better matching)
    ALERT_MATCH_CONFIDENCE_THRESHOLD: float = 30.0   # Lowered for more matches (was 50.0)
    ALERT_MATCH_TIME_WINDOW_MINUTES: int = 60        # Increased time window (was 15)
    
    # Sync Configuration
    GRAFANA_SYNC_INTERVAL_SECONDS: int = 300         # Sync every 5 minutes
    JSM_SYNC_INTERVAL_SECONDS: int = 300             # Sync JSM alerts every 5 minutes
    
    # Alert Filtering (Updated for better production filtering)
    FILTER_NON_PROD_ALERTS: bool = True              # Filter out non-production alerts
    EXCLUDED_CLUSTERS: list = ["stage", "dev", "test", "staging", "development"]  # Extended list
    EXCLUDED_ENVIRONMENTS: list = ["devo-stage-eu", "staging", "development", "dev"]  # Extended list
    
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
    
    # Feature Flags (Updated)
    USE_JSM_MODE: bool = True                        # Use JSM API instead of Jira issues
    ENABLE_AUTO_CLOSE: bool = True                   # Auto-close JSM alerts when Grafana resolves
    ENABLE_MATCH_LOGGING: bool = True                # Enable detailed matching logs for debugging
    
    # Enhanced Matching Settings
    ENABLE_FUZZY_MATCHING: bool = True               # Enable fuzzy string matching
    ENABLE_TIME_PROXIMITY_MATCHING: bool = True     # Use time proximity for matching
    ENABLE_CONTENT_SIMILARITY_MATCHING: bool = True # Use content similarity for matching
    
    # Matching Weights (for fine-tuning matching algorithm)
    MATCH_WEIGHT_ALERT_NAME: int = 40               # Weight for alert name matching
    MATCH_WEIGHT_CLUSTER: int = 25                  # Weight for cluster matching
    MATCH_WEIGHT_SEVERITY: int = 15                 # Weight for severity matching
    MATCH_WEIGHT_CONTENT: int = 20                  # Weight for content similarity
    MATCH_WEIGHT_TIME_PROXIMITY: int = 10           # Weight for time proximity
    MATCH_WEIGHT_SOURCE: int = 15                   # Weight for JSM source being Grafana
    
    # Performance Settings
    MAX_ALERTS_TO_PROCESS: int = 5000               # Max alerts to process in one sync
    BATCH_SIZE_ALERTS: int = 100                    # Process alerts in batches
    
    class Config:
        env_file = ".env"

settings = Settings()