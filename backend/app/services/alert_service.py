from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from ..models.alert import Alert
from ..schemas.alert import AlertCreate, AlertUpdate
from .grafana_service import GrafanaService
from .jira_service import JiraService
import logging

logger = logging.getLogger(__name__)

class AlertService:
    def __init__(self):
        self.grafana_service = GrafanaService()
        self.jira_service = JiraService()
    
    def _sanitize_alert_data(self, alert_data: dict) -> dict:
        """Sanitize alert data to handle None values and prevent errors"""
        sanitized = {}
        for key, value in alert_data.items():
            if value is None:
                # Set None values to empty string for string fields that might need .replace()
                if key in ['description', 'summary', 'message', 'annotations', 'labels']:
                    sanitized[key] = ""
                else:
                    sanitized[key] = None
            elif isinstance(value, str):
                # Clean up string values
                sanitized[key] = value.strip() if value else ""
            else:
                sanitized[key] = value
        return sanitized
    
    def _is_non_prod_alert(self, alert_data: dict) -> bool:
        """Check if alert is from non-production environment and should be filtered out"""
        labels = alert_data.get('labels', {})
        
        # Check cluster label for stage pattern
        cluster = labels.get('cluster', '')
        if 'stage' in cluster.lower():
            logger.debug(f"Filtering out stage cluster alert: {cluster}")
            return True
        
        # Check env label for devo-stage-eu
        env = labels.get('env', '')
        if env == 'devo-stage-eu':
            logger.debug(f"Filtering out devo-stage-eu alert: {env}")
            return True
        
        return False
    
    async def sync_alerts(self, db: Session):
        """Sync alerts from Grafana and update Jira status for existing tickets only"""
        try:
            # Get active alerts from Grafana
            grafana_alerts = await self.grafana_service.get_active_alerts()
            active_alert_ids = set()
            
            logger.info(f"Processing {len(grafana_alerts)} alerts from Grafana")
            
            # Filter out non-production alerts
            filtered_alerts = []
            for alert_data in grafana_alerts:
                if not self._is_non_prod_alert(alert_data):
                    filtered_alerts.append(alert_data)
                else:
                    logger.debug(f"Filtered out non-prod alert: {alert_data.get('alert_id')}")
            
            logger.info(f"After filtering non-prod alerts: {len(filtered_alerts)} production alerts")
            
            for i, alert_data in enumerate(filtered_alerts):
                try:
                    # Sanitize alert data to prevent None-related errors
                    alert_data = self._sanitize_alert_data(alert_data)
                    
                    alert_id = alert_data.get('alert_id')
                    if not alert_id:
                        logger.warning(f"Alert at index {i} missing alert_id, skipping")
                        continue
                        
                    active_alert_ids.add(alert_id)
                    
                    # Check if alert exists in DB
                    existing_alert = db.query(Alert).filter(Alert.alert_id == alert_id).first()
                    
                    if existing_alert:
                        # Update existing alert
                        existing_alert.grafana_status = "active"
                        existing_alert.updated_at = datetime.utcnow()
                        
                        # Update alert fields in case they changed
                        for field, value in alert_data.items():
                            if hasattr(existing_alert, field) and field not in ['id', 'created_at']:
                                try:
                                    setattr(existing_alert, field, value)
                                except Exception as e:
                                    logger.warning(f"Error setting field {field} to {value} for alert {alert_id}: {e}")
                    else:
                        # Create new alert entry (without creating Jira ticket)
                        try:
                            new_alert = Alert(**alert_data, grafana_status="active")
                            db.add(new_alert)
                            db.flush()  # Get the ID
                            logger.info(f"Created new alert entry {alert_id} (Jira ticket will be created by Grafana integration)")
                        except Exception as e:
                            logger.error(f"Error creating alert {alert_id}: {e}")
                            continue
                            
                except Exception as e:
                    logger.error(f"Error processing alert at index {i}: {e}")
                    continue
            
            # Mark resolved alerts and update corresponding Jira issues
            try:
                resolved_alerts = db.query(Alert).filter(
                    ~Alert.alert_id.in_(active_alert_ids),
                    Alert.grafana_status == "active"
                ).all()
                
                logger.info(f"Found {len(resolved_alerts)} alerts to resolve")
                
                for alert in resolved_alerts:
                    try:
                        alert.grafana_status = "resolved"
                        
                        # Update Jira issue status if it exists and not already resolved
                        if alert.jira_issue_key and alert.jira_status not in ["resolved", "closed"]:
                            # Check current status in Jira instead of auto-resolving
                            status_info = await self.jira_service.check_issue_acknowledgment_status(alert.jira_issue_key)
                            if status_info and not status_info.get('error'):
                                # Update our local status based on Jira
                                if any(keyword in status_info.get('status_name', '').lower() 
                                      for keyword in ['done', 'resolved', 'closed', 'completed']):
                                    alert.jira_status = "resolved"
                                    if not alert.resolved_by:
                                        alert.resolved_by = "Auto-resolved (Grafana)"
                                        alert.resolved_at = datetime.utcnow()
                                logger.info(f"Updated status for resolved alert {alert.alert_id}")
                    except Exception as e:
                        logger.error(f"Error updating resolved alert {alert.alert_id}: {e}")
                        continue
            except Exception as e:
                logger.error(f"Error processing resolved alerts: {e}")
            
            # Enhanced Jira status sync for existing tickets
            try:
                await self._sync_jira_status(db)
            except Exception as e:
                logger.error(f"Error in enhanced Jira status sync: {e}")
            
            db.commit()
            logger.info(f"Successfully synced {len(filtered_alerts)} production alerts from Grafana")
            
        except Exception as e:
            logger.error(f"Critical error in sync_alerts: {e}")
            db.rollback()
            raise

    async def _sync_jira_status(self, db: Session):
        """Enhanced Jira status synchronization with acknowledgment checking"""
        try:
            # Get all alerts that have Jira tickets
            alerts_with_jira = db.query(Alert).filter(
                Alert.jira_issue_key.isnot(None),
                Alert.jira_status != "resolved"
            ).all()
            
            if not alerts_with_jira:
                logger.info("No alerts with Jira tickets to sync")
                return
            
            logger.info(f"Syncing status for {len(alerts_with_jira)} alerts with Jira tickets")
            
            # Get all relevant Jira issues in batch
            jira_issues = await self.jira_service.get_issues()
            jira_issue_map = {issue.get('key'): issue for issue in jira_issues}
            
            for alert in alerts_with_jira:
                try:
                    jira_issue = jira_issue_map.get(alert.jira_issue_key)
                    if not jira_issue:
                        logger.warning(f"Jira issue {alert.jira_issue_key} not found for alert {alert.alert_id}")
                        continue
                    
                    # Get detailed acknowledgment status
                    status_info = await self.jira_service.check_issue_acknowledgment_status(alert.jira_issue_key)
                    
                    if status_info and not status_info.get('error'):
                        # Update assignee information
                        if status_info.get('assignee'):
                            alert.jira_assignee = status_info['assignee']
                        
                        # Update acknowledgment status
                        if status_info.get('acknowledged'):
                            if alert.jira_status == "open":
                                alert.jira_status = "acknowledged"
                                if status_info.get('acknowledger') and not alert.acknowledged_by:
                                    alert.acknowledged_by = status_info['acknowledger']
                                    if status_info.get('acknowledgment_date'):
                                        try:
                                            alert.acknowledged_at = datetime.fromisoformat(
                                                status_info['acknowledgment_date'].replace('Z', '+00:00')
                                            )
                                        except:
                                            alert.acknowledged_at = datetime.utcnow()
                                logger.info(f"Alert {alert.alert_id} marked as acknowledged from Jira")
                        
                        # Check if resolved in Jira
                        if any(keyword in status_info.get('status_name', '').lower() 
                              for keyword in ['done', 'resolved', 'closed', 'completed']):
                            if alert.jira_status != "resolved":
                                alert.jira_status = "resolved"
                                if not alert.resolved_by:
                                    alert.resolved_by = status_info.get('assignee', 'Jira User')
                                    alert.resolved_at = datetime.utcnow()
                                logger.info(f"Alert {alert.alert_id} marked as resolved from Jira")
                    
                except Exception as e:
                    logger.error(f"Error processing Jira issue {alert.jira_issue_key}: {e}")
                    continue
                        
        except Exception as e:
            logger.error(f"Error in enhanced Jira status sync: {e}")

    def get_alerts(self, db: Session, skip: int = 0, limit: int = 100) -> List[Alert]:
        """Get paginated alerts from database"""
        return db.query(Alert).order_by(Alert.created_at.desc()).offset(skip).limit(limit).all()
    
    def get_alert(self, db: Session, alert_id: int) -> Optional[Alert]:
        """Get single alert by ID"""
        return db.query(Alert).filter(Alert.id == alert_id).first()

    async def acknowledge_alerts(self, db: Session, alert_ids: List[int], note: str = None, acknowledged_by: str = "System User") -> bool:
        """Acknowledge alerts in Jira and update DB"""
        try:
            alerts = db.query(Alert).filter(Alert.id.in_(alert_ids)).all()
            
            for alert in alerts:
                try:
                    if alert.jira_issue_key:
                        success = await self.jira_service.acknowledge_issue(
                            alert.jira_issue_key, note
                        )
                        if success:
                            alert.jira_status = "acknowledged"
                            alert.acknowledged_by = acknowledged_by
                            alert.acknowledged_at = datetime.utcnow()
                            logger.info(f"Acknowledged Jira issue {alert.jira_issue_key} by {acknowledged_by}")
                        else:
                            logger.warning(f"Failed to acknowledge Jira issue {alert.jira_issue_key}")
                    else:
                        # No Jira ticket associated - log this case
                        logger.warning(f"Alert {alert.id} ({alert.alert_id}) has no associated Jira ticket")
                        # Still update local acknowledgment for tracking
                        alert.acknowledged_by = acknowledged_by
                        alert.acknowledged_at = datetime.utcnow()
                        
                except Exception as e:
                    logger.error(f"Error acknowledging alert {alert.id}: {e}")
                    continue
            
            db.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error acknowledging alerts: {e}")
            db.rollback()
            return False
    
    async def resolve_alerts(self, db: Session, alert_ids: List[int], note: str = None, resolved_by: str = "System User") -> bool:
        """Manually resolve alerts in Jira and update DB"""
        try:
            alerts = db.query(Alert).filter(Alert.id.in_(alert_ids)).all()
            
            for alert in alerts:
                try:
                    if alert.jira_issue_key:
                        success = await self.jira_service.resolve_issue(
                            alert.jira_issue_key, note or "Manually resolved via Alert Manager"
                        )
                        if success:
                            alert.jira_status = "resolved"
                            alert.grafana_status = "resolved"  # Also mark as resolved in our system
                            alert.resolved_by = resolved_by
                            alert.resolved_at = datetime.utcnow()
                            logger.info(f"Resolved Jira issue {alert.jira_issue_key} by {resolved_by}")
                        else:
                            logger.warning(f"Failed to resolve Jira issue {alert.jira_issue_key}")
                    else:
                        # No Jira ticket associated
                        logger.warning(f"Alert {alert.id} ({alert.alert_id}) has no associated Jira ticket")
                        # Still update local resolution for tracking
                        alert.grafana_status = "resolved"
                        alert.resolved_by = resolved_by
                        alert.resolved_at = datetime.utcnow()
                        
                except Exception as e:
                    logger.error(f"Error resolving alert {alert.id}: {e}")
                    continue
            
            db.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error resolving alerts: {e}")
            db.rollback()
            return False

    def get_alerts_for_export(self, db: Session, filters: dict = None) -> List[Alert]:
        """Get alerts for CSV export with optional filtering"""
        query = db.query(Alert)
        
        if filters:
            # Apply filters for export
            if filters.get('severity'):
                query = query.filter(Alert.severity.in_(filters['severity']))
            if filters.get('grafana_status'):
                query = query.filter(Alert.grafana_status.in_(filters['grafana_status']))
            if filters.get('jira_status'):
                query = query.filter(Alert.jira_status.in_(filters['jira_status']))
            if filters.get('cluster'):
                query = query.filter(Alert.cluster.ilike(f"%{filters['cluster']}%"))
            if filters.get('date_from'):
                query = query.filter(Alert.created_at >= filters['date_from'])
            if filters.get('date_to'):
                query = query.filter(Alert.created_at <= filters['date_to'])
        
        return query.order_by(Alert.created_at.desc()).all()