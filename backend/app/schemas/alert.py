from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, Any

class AlertBase(BaseModel):
    alert_name: str
    cluster: Optional[str] = None
    pod: Optional[str] = None
    severity: Optional[str] = None
    summary: Optional[str] = None
    description: Optional[str] = None

class AlertCreate(AlertBase):
    alert_id: str
    started_at: Optional[datetime] = None
    generator_url: Optional[str] = None
    labels: Optional[Dict[str, Any]] = None
    annotations: Optional[Dict[str, Any]] = None

class AlertUpdate(BaseModel):
    grafana_status: Optional[str] = None
    jira_status: Optional[str] = None
    jira_issue_key: Optional[str] = None
    jira_issue_id: Optional[str] = None
    jira_issue_url: Optional[str] = None

class AlertResponse(AlertBase):
    id: int
    alert_id: str
    started_at: Optional[datetime]
    generator_url: Optional[str]
    grafana_status: str
    jira_status: str
    jira_issue_key: Optional[str]
    jira_issue_id: Optional[str]
    jira_issue_url: Optional[str]
    jira_assignee: Optional[str]
    jira_assignee_email: Optional[str]
    acknowledged_by: Optional[str]
    acknowledged_at: Optional[datetime]
    resolved_by: Optional[str]
    resolved_at: Optional[datetime]
    labels: Optional[Dict[str, Any]]
    annotations: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class AcknowledgeRequest(BaseModel):
    alert_ids: list[int]
    note: Optional[str] = None
    acknowledged_by: Optional[str] = "System User"

class ResolveRequest(BaseModel):
    alert_ids: list[int]
    note: Optional[str] = None
    resolved_by: Optional[str] = "System User"