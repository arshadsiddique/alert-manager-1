from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime
from ..models.alert import Alert
from ..schemas.alert import AlertCreate, AlertUpdate
from .grafana_service import GrafanaService
from .jsm_service import JSMService
import logging

logger = logging.getLogger(__name__)

class AlertService:
    def __init__(self):
        self.grafana_service = GrafanaService()
        self.jsm_service = JSMService()
    
    def _sanitize_alert_data(self, alert_data: dict) -> dict:
        """Sanitize alert data to handle None values and prevent errors"""
        sanitized = {}
        for key, value in alert_data.items():
            if value is None:
                if key in ['description', 'summary', 'message', 'annotations', 'labels']:
                    sanitized[key] = ""
                else:
                    sanitized[key] = None
            elif isinstance(value, str):
                sanitized[key] = value.strip() if value else ""
            else:
                sanitized[key] = value
        return sanitized
    
    def _is_non_prod_alert(self, alert_data: dict) -> bool:
        """Check if alert is from non-production environment and should be filtered out"""
        labels = alert_data.get('labels', {})
        
        cluster = labels.get('cluster', '')
        if 'stage' in cluster.lower():
            logger.debug(f"Filtering out stage cluster alert: {cluster}")
            return True
        
        env = labels.get('env', '')
        if env == 'devo-stage-eu':
            logger.debug(f"Filtering out devo-stage-eu alert: {env}")
            return True
        
        return False
    
    async def sync_alerts(self, db: Session):
        """Sync alerts from Grafana and JSM, then match them"""
        try:
            logger.info("Starting alert synchronization with Grafana and JSM")
            
            # Fetch alerts from both systems
            grafana_alerts = await self.grafana_service.get_active_alerts()
            jsm_alerts = await self.jsm_service.get_jsm_alerts(limit=500)
            
            logger.info(f"Retrieved {len(grafana_alerts)} Grafana alerts and {len(jsm_alerts)} JSM alerts")
            
            # Filter out non-production alerts from Grafana
            filtered_grafana_alerts = []
            for alert_data in grafana_alerts:
                if not self._is_non_prod_alert(alert_data):
                    filtered_grafana_alerts.append(alert_data)
            
            logger.info(f"After filtering: {len(filtered_grafana_alerts)} production Grafana alerts")
            
            # Match Grafana alerts with JSM alerts
            matched_alerts = self.jsm_service.match_grafana_with_jsm(
                filtered_grafana_alerts, jsm_alerts
            )
            
            logger.info(f"Matched {len(matched_alerts)} alert pairs")
            
            # Track active Grafana alert IDs
            active_grafana_alert_ids = set()
            
            # Process matched alerts
            for match_info in matched_alerts:
                try:
                    grafana_alert = self._sanitize_alert_data(match_info['grafana_alert'])
                    jsm_alert = match_info.get('jsm_alert')
                    
                    alert_id = grafana_alert.get('alert_id')
                    if not alert_id:
                        continue
                    
                    active_grafana_alert_ids.add(alert_id)
                    
                    # Check if alert exists in DB
                    existing_alert = db.query(Alert).filter(Alert.alert_id == alert_id).first()
                    
                    if existing_alert:
                        # Update existing alert
                        self._update_existing_alert(existing_alert, grafana_alert, jsm_alert, match_info)
                    else:
                        # Create new alert
                        self._create_new_alert(db, grafana_alert, jsm_alert, match_info)
                        
                except Exception as e:
                    logger.error(f"Error processing matched alert: {e}")
                    continue
            
            # Mark resolved alerts (Grafana alerts no longer active)
            await self._mark_resolved_alerts(db, active_grafana_alert_ids)
            
            # Update JSM status for existing alerts without current matches
            await self._update_orphaned_jsm_alerts(db, jsm_alerts)
            
            db.commit()
            logger.info("Alert synchronization completed successfully")
            
        except Exception as e:
            logger.error(f"Critical error in sync_alerts: {e}")
            db.rollback()
            raise
    
    def _update_existing_alert(self, alert: Alert, grafana_data: Dict, jsm_data: Optional[Dict], match_info: Dict):
        """Update existing alert with latest data"""
        # Update Grafana fields
        alert.grafana_status = "active"
        alert.updated_at = datetime.utcnow()
        
        # Update basic Grafana fields
        for field, value in grafana_data.items():
            if hasattr(alert, field) and field not in ['id', 'created_at']:
                try:
                    setattr(alert, field, value)
                except Exception as e:
                    logger.warning(f"Error setting field {field}: {e}")
        
        # Update JSM fields if we have a match
        if jsm_data:
            self._update_jsm_fields(alert, jsm_data, match_info)
        else:
            # Clear JSM fields if no match found
            alert.jsm_alert_id = None
            alert.jsm_status = None
            alert.match_type = 'none'
            alert.match_confidence = 0
        
        logger.debug(f"Updated alert {alert.alert_id}")
    
    def _create_new_alert(self, db: Session, grafana_data: Dict, jsm_data: Optional[Dict], match_info: Dict):
        """Create new alert in database"""
        try:
            # Create base alert from Grafana data
            new_alert = Alert(**grafana_data, grafana_status="active")
            
            # Add JSM fields if we have a match
            if jsm_data:
                self._update_jsm_fields(new_alert, jsm_data, match_info)
            else:
                new_alert.match_type = 'none'
                new_alert.match_confidence = 0
            
            db.add(new_alert)
            db.flush()  # Get the ID
            
            logger.info(f"Created new alert {new_alert.alert_id} with JSM match: {bool(jsm_data)}")
            
        except Exception as e:
            logger.error(f"Error creating new alert: {e}")
    
    def _update_jsm_fields(self, alert: Alert, jsm_data: Dict, match_info: Dict):
        """Update alert with JSM data"""
        jsm_status_info = self.jsm_service.get_alert_status_info(jsm_data)
        
        alert.jsm_alert_id = jsm_status_info['id']
        alert.jsm_tiny_id = jsm_status_info['tiny_id']
        alert.jsm_status = jsm_status_info['status']
        alert.jsm_acknowledged = jsm_status_info['acknowledged']
        alert.jsm_owner = jsm_status_info['owner']
        alert.jsm_priority = jsm_status_info['priority']
        alert.jsm_alias = jsm_status_info['alias']
        alert.jsm_integration_name = jsm_status_info['integration_name']
        alert.jsm_source = jsm_status_info['source']
        alert.jsm_count = jsm_status_info['count']
        alert.jsm_tags = jsm_status_info['tags']
        alert.match_type = match_info['match_type']
        alert.match_confidence = match_info['match_confidence']
        
        # Parse JSM timestamps
        try:
            if jsm_status_info['created_at']:
                alert.jsm_created_at = datetime.fromisoformat(
                    jsm_status_info['created_at'].replace('Z', '+00:00')
                )
            if jsm_status_info['updated_at']:
                alert.jsm_updated_at = datetime.fromisoformat(
                    jsm_status_info['updated_at'].replace('Z', '+00:00')
                )
            if jsm_status_info['last_occurred_at']:
                alert.jsm_last_occurred_at = datetime.fromisoformat(
                    jsm_status_info['last_occurred_at'].replace('Z', '+00:00')
                )
        except Exception as e:
            logger.warning(f"Error parsing JSM timestamps: {e}")
        
        # Update legacy fields for backwards compatibility
        alert.jira_status = self._map_jsm_to_jira_status(jsm_status_info['status'])
        alert.jira_assignee = jsm_status_info['owner']
        
        # Set acknowledgment if JSM shows it's acknowledged
        if jsm_status_info['acknowledged'] and not alert.acknowledged_by:
            alert.acknowledged_by = jsm_status_info['owner'] or "JSM User"
            alert.acknowledged_at = alert.jsm_updated_at or datetime.utcnow()
    
    def _map_jsm_to_jira_status(self, jsm_status: str) -> str:
        """Map JSM status to legacy Jira status for backwards compatibility"""
        mapping = {
            'open': 'open',
            'acked': 'acknowledged', 
            'closed': 'resolved'
        }
        return mapping.get(jsm_status, 'open')
    
    async def _mark_resolved_alerts(self, db: Session, active_alert_ids: set):
        """Mark alerts as resolved if they're no longer active in Grafana"""
        try:
            resolved_alerts = db.query(Alert).filter(
                ~Alert.alert_id.in_(active_alert_ids),
                Alert.grafana_status == "active"
            ).all()
            
            logger.info(f"Found {len(resolved_alerts)} alerts to mark as resolved")
            
            for alert in resolved_alerts:
                alert.grafana_status = "resolved"
                
                # If it has a JSM alert and it's not already closed, try to close it
                if alert.jsm_alert_id and alert.jsm_status != 'closed':
                    try:
                        success = await self.jsm_service.close_jsm_alert(
                            alert.jsm_alert_id, 
                            "Alert resolved in Grafana",
                            "Alert Manager"
                        )
                        if success:
                            alert.jsm_status = 'closed'
                            if not alert.resolved_by:
                                alert.resolved_by = "Auto-resolved (Grafana)"
                                alert.resolved_at = datetime.utcnow()
                    except Exception as e:
                        logger.error(f"Error closing JSM alert {alert.jsm_alert_id}: {e}")
                
                logger.debug(f"Marked alert {alert.alert_id} as resolved")
                
        except Exception as e:
            logger.error(f"Error marking resolved alerts: {e}")
    
    async def _update_orphaned_jsm_alerts(self, db: Session, jsm_alerts: List[Dict]):
        """Update alerts that have JSM IDs but may have status changes"""
        try:
            jsm_alerts_by_id = {alert['id']: alert for alert in jsm_alerts}
            
            # Find alerts with JSM IDs
            alerts_with_jsm = db.query(Alert).filter(
                Alert.jsm_alert_id.isnot(None)
            ).all()
            
            for alert in alerts_with_jsm:
                if alert.jsm_alert_id in jsm_alerts_by_id:
                    jsm_data = jsm_alerts_by_id[alert.jsm_alert_id]
                    match_info = {'match_type': alert.match_type, 'match_confidence': alert.match_confidence}
                    self._update_jsm_fields(alert, jsm_data, match_info)
                    logger.debug(f"Updated JSM status for alert {alert.alert_id}")
                    
        except Exception as e:
            logger.error(f"Error updating orphaned JSM alerts: {e}")
    
    def get_alerts(self, db: Session, skip: int = 0, limit: int = 100) -> List[Alert]:
        """Get paginated alerts from database"""
        return db.query(Alert).order_by(Alert.created_at.desc()).offset(skip).limit(limit).all()
    
    def get_alert(self, db: Session, alert_id: int) -> Optional[Alert]:
        """Get single alert by ID"""
        return db.query(Alert).filter(Alert.id == alert_id).first()
    
    async def acknowledge_alerts(self, db: Session, alert_ids: List[int], note: str = None, acknowledged_by: str = "System User") -> bool:
        """Acknowledge alerts in JSM and update DB"""
        try:
            alerts = db.query(Alert).filter(Alert.id.in_(alert_ids)).all()
            
            for alert in alerts:
                try:
                    success = False
                    
                    # Try to acknowledge in JSM if we have JSM alert ID
                    if alert.jsm_alert_id:
                        success = await self.jsm_service.acknowledge_jsm_alert(
                            alert.jsm_alert_id, note, acknowledged_by
                        )
                        if success:
                            alert.jsm_status = "acked"
                            alert.jsm_acknowledged = True
                            logger.info(f"Acknowledged JSM alert {alert.jsm_alert_id}")
                    
                    # Update local acknowledgment tracking regardless
                    alert.acknowledged_by = acknowledged_by
                    alert.acknowledged_at = datetime.utcnow()
                    alert.jira_status = "acknowledged"  # Legacy compatibility
                    
                    if not alert.jsm_alert_id:
                        logger.warning(f"Alert {alert.id} has no JSM alert ID - only updated locally")
                        
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
        """Manually resolve alerts in JSM and update DB"""
        try:
            alerts = db.query(Alert).filter(Alert.id.in_(alert_ids)).all()
            
            for alert in alerts:
                try:
                    success = False
                    
                    # Try to close in JSM if we have JSM alert ID
                    if alert.jsm_alert_id:
                        success = await self.jsm_service.close_jsm_alert(
                            alert.jsm_alert_id, 
                            note or "Manually resolved via Alert Manager",
                            resolved_by
                        )
                        if success:
                            alert.jsm_status = "closed"
                            logger.info(f"Closed JSM alert {alert.jsm_alert_id}")
                    
                    # Update local resolution tracking
                    alert.grafana_status = "resolved"
                    alert.resolved_by = resolved_by
                    alert.resolved_at = datetime.utcnow()
                    alert.jira_status = "resolved"  # Legacy compatibility
                    
                    if not alert.jsm_alert_id:
                        logger.warning(f"Alert {alert.id} has no JSM alert ID - only updated locally")
                        
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
            if filters.get('severity'):
                query = query.filter(Alert.severity.in_(filters['severity']))
            if filters.get('grafana_status'):
                query = query.filter(Alert.grafana_status.in_(filters['grafana_status']))
            if filters.get('jsm_status'):
                query = query.filter(Alert.jsm_status.in_(filters['jsm_status']))
            if filters.get('cluster'):
                query = query.filter(Alert.cluster.ilike(f"%{filters['cluster']}%"))
            if filters.get('date_from'):
                query = query.filter(Alert.created_at >= filters['date_from'])
            if filters.get('date_to'):
                query = query.filter(Alert.created_at <= filters['date_to'])
        
        return query.order_by(Alert.created_at.desc()).all()
    
    def get_sync_summary(self, db: Session) -> Dict[str, Any]:
        """Get synchronization summary statistics"""
        total_alerts = db.query(Alert).count()
        
        # Count by matching status
        matched_alerts = db.query(Alert).filter(Alert.jsm_alert_id.isnot(None)).count()
        unmatched_alerts = total_alerts - matched_alerts
        
        # Count by JSM status
        jsm_open = db.query(Alert).filter(Alert.jsm_status == 'open').count()
        jsm_acked = db.query(Alert).filter(Alert.jsm_status == 'acked').count()
        jsm_closed = db.query(Alert).filter(Alert.jsm_status == 'closed').count()
        
        # Count by match type
        match_types = {}
        match_results = db.query(Alert.match_type, Alert).filter(Alert.match_type.isnot(None)).all()
        for match_type, _ in match_results:
            match_types[match_type] = match_types.get(match_type, 0) + 1
        
        return {
            'total_alerts': total_alerts,
            'matched_alerts': matched_alerts,
            'unmatched_alerts': unmatched_alerts,
            'jsm_status_counts': {
                'open': jsm_open,
                'acked': jsm_acked,
                'closed': jsm_closed
            },
            'match_type_counts': match_types,
            'last_sync': datetime.utcnow().isoformat()
        }