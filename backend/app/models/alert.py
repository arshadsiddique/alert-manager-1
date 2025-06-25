from sqlalchemy import Column, Integer, String, Boolean, Text, JSON
from sqlalchemy.types import DateTime
from sqlalchemy.sql import func
from ..core.database import Base

class Alert(Base):
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    alert_id = Column(String, unique=True, index=True)
    alert_name = Column(String, index=True)
    cluster = Column(String)
    pod = Column(String)
    severity = Column(String)
    summary = Column(Text)
    description = Column(Text)
    started_at = Column(DateTime)
    generator_url = Column(String)
    grafana_status = Column(String, default="active")
    jira_status = Column(String, default="open")
    jira_issue_key = Column(String, nullable=True)  # e.g., "OP-123"
    jira_issue_id = Column(String, nullable=True)   # Jira internal ID
    jira_issue_url = Column(String, nullable=True)  # Direct link to Jira issue
    jira_assignee = Column(String, nullable=True)   # Who is assigned in Jira
    jira_assignee_email = Column(String, nullable=True)  # Assignee email from Jira
    acknowledged_by = Column(String, nullable=True)  # Who acknowledged via our system
    acknowledged_at = Column(DateTime, nullable=True)  # When acknowledged via our system
    resolved_by = Column(String, nullable=True)     # Who resolved via our system
    resolved_at = Column(DateTime, nullable=True)   # When resolved via our system
    labels = Column(JSON)
    annotations = Column(JSON)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())