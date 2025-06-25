from sqlalchemy import Column, Integer, String, Boolean, Text, JSON, Float
from sqlalchemy.types import DateTime
from sqlalchemy.sql import func
from ..core.database import Base

class Alert(Base):
    __tablename__ = "alerts"
    
    # Core alert fields from Grafana
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
    grafana_status = Column(String, default="active")  # active, resolved
    labels = Column(JSON)
    annotations = Column(JSON)
    
    # JSM Alert Integration Fields
    jsm_alert_id = Column(String, nullable=True, index=True)  # JSM alert ID
    jsm_tiny_id = Column(String, nullable=True)   # JSM tiny ID (human readable)
    jsm_status = Column(String, nullable=True, index=True)    # open, acked, closed
    jsm_acknowledged = Column(Boolean, default=False, index=True)
    jsm_owner = Column(String, nullable=True)     # Who owns the alert in JSM
    jsm_priority = Column(String, nullable=True)  # P1, P2, P3, etc.
    jsm_alias = Column(String, nullable=True)     # JSM alert alias/hash
    jsm_integration_name = Column(String, nullable=True)  # Integration that created alert
    jsm_source = Column(String, nullable=True)    # Source system (e.g., Grafana)
    jsm_count = Column(Integer, default=1)        # Number of occurrences
    jsm_tags = Column(JSON, nullable=True)        # JSM alert tags
    jsm_last_occurred_at = Column(DateTime, nullable=True)
    jsm_created_at = Column(DateTime, nullable=True)
    jsm_updated_at = Column(DateTime, nullable=True)
    
    # Matching Information
    match_type = Column(String, nullable=True, index=True)    # alias, tags_and_content, content_similarity, none
    match_confidence = Column(Float, nullable=True)  # 0-100 confidence score
    
    # Manual Actions (for tracking manual interventions)
    acknowledged_by = Column(String, nullable=True)  # Who acknowledged via our system
    acknowledged_at = Column(DateTime, nullable=True)  # When acknowledged via our system
    resolved_by = Column(String, nullable=True)     # Who resolved via our system
    resolved_at = Column(DateTime, nullable=True)   # When resolved via our system
    
    # Legacy Jira fields (keeping for backwards compatibility)
    jira_status = Column(String, default="open")    # Legacy field - maps to jsm_status
    jira_issue_key = Column(String, nullable=True)  # Legacy field - not used in JSM mode
    jira_issue_id = Column(String, nullable=True)   # Legacy field - not used in JSM mode
    jira_issue_url = Column(String, nullable=True)  # Legacy field - not used in JSM mode
    jira_assignee = Column(String, nullable=True)   # Legacy field - maps to jsm_owner
    jira_assignee_email = Column(String, nullable=True)  # Legacy field
    
    # System fields
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    @property
    def effective_status(self):
        """Get the effective status (prioritize JSM over legacy Jira)"""
        if self.jsm_status:
            return self.jsm_status
        return self.jira_status or "open"
    
    @property
    def effective_assignee(self):
        """Get the effective assignee (prioritize JSM over legacy Jira)"""
        return self.jsm_owner or self.jira_assignee
    
    @property
    def is_acknowledged(self):
        """Check if alert is acknowledged in any system"""
        return (
            self.jsm_acknowledged or 
            self.acknowledged_by is not None or
            self.effective_status in ['acked', 'acknowledged']
        )
    
    @property
    def is_resolved(self):
        """Check if alert is resolved/closed"""
        return (
            self.grafana_status == 'resolved' or
            self.effective_status in ['closed', 'resolved']
        )
    
    @property
    def jsm_url(self):
        """Generate JSM alert URL if we have JSM alert info"""
        if self.jsm_alert_id and hasattr(self, '_jsm_base_url'):
            return f"{self._jsm_base_url}/alert/detail/{self.jsm_alert_id}/details"
        return None
    
    def to_dict(self):
        """Convert alert to dictionary for API responses"""
        return {
            'id': self.id,
            'alert_id': self.alert_id,
            'alert_name': self.alert_name,
            'cluster': self.cluster,
            'pod': self.pod,
            'severity': self.severity,
            'summary': self.summary,
            'description': self.description,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'generator_url': self.generator_url,
            'grafana_status': self.grafana_status,
            'labels': self.labels,
            'annotations': self.annotations,
            
            # JSM fields
            'jsm_alert_id': self.jsm_alert_id,
            'jsm_tiny_id': self.jsm_tiny_id,
            'jsm_status': self.jsm_status,
            'jsm_acknowledged': self.jsm_acknowledged,
            'jsm_owner': self.jsm_owner,
            'jsm_priority': self.jsm_priority,
            'jsm_alias': self.jsm_alias,
            'jsm_integration_name': self.jsm_integration_name,
            'jsm_source': self.jsm_source,
            'jsm_count': self.jsm_count,
            'jsm_tags': self.jsm_tags,
            'jsm_last_occurred_at': self.jsm_last_occurred_at.isoformat() if self.jsm_last_occurred_at else None,
            'jsm_created_at': self.jsm_created_at.isoformat() if self.jsm_created_at else None,
            'jsm_updated_at': self.jsm_updated_at.isoformat() if self.jsm_updated_at else None,
            
            # Matching info
            'match_type': self.match_type,
            'match_confidence': self.match_confidence,
            
            # Manual actions
            'acknowledged_by': self.acknowledged_by,
            'acknowledged_at': self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            'resolved_by': self.resolved_by,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            
            # Legacy fields (for backwards compatibility)
            'jira_status': self.jira_status,
            'jira_issue_key': self.jira_issue_key,
            'jira_assignee': self.jira_assignee,
            'jira_assignee_email': self.jira_assignee_email,
            
            # Computed properties
            'effective_status': self.effective_status,
            'effective_assignee': self.effective_assignee,
            'is_acknowledged': self.is_acknowledged,
            'is_resolved': self.is_resolved,
            'jsm_url': self.jsm_url,
            
            # System fields
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
