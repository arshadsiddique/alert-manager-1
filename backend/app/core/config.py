from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/alertdb"
    
    # Grafana
    GRAFANA_API_URL: str = "https://grafana.observability.devo.com"
    GRAFANA_API_KEY: str = ""
    
    # Jira Service Management
    JIRA_URL: str = "https://devoinc.atlassian.net"
    JIRA_USER_EMAIL: str = ""
    JIRA_API_TOKEN: str = ""
    JIRA_PROJECT_KEY: str = "OP"
    JIRA_INCIDENT_ISSUE_TYPE: str = "Incident"
    JIRA_ACKNOWLEDGE_TRANSITION_NAME: str = "To Do"
    JIRA_RESOLVE_TRANSITION_NAME: str = "Completed"
    
    # Sync Configuration
    GRAFANA_SYNC_INTERVAL_SECONDS: int = 600
    
    # App
    DEBUG: bool = False
    SECRET_KEY: str = "your-secret-key-here"
    
    # CORS
    ALLOWED_ORIGINS: list = ["http://localhost:3000", "http://localhost:3001"]
    
    class Config:
        env_file = ".env"

settings = Settings()