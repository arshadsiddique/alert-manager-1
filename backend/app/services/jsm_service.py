import requests
import logging
import base64
import hashlib
from typing import List, Dict, Any, Optional
from datetime import datetime
from ..core.config import settings

logger = logging.getLogger(__name__)

class JSMService:
    def __init__(self):
        self.base_url = "https://api.atlassian.com/jsm/ops/api"
        self.tenant_url = settings.JIRA_URL  # e.g., https://devoinc.atlassian.net
        self.user_email = settings.JIRA_USER_EMAIL
        self.api_token = settings.JIRA_API_TOKEN
        self.cloud_id = None
        
        # Create basic auth header
        auth_string = f"{self.user_email}:{self.api_token}"
        auth_bytes = auth_string.encode('ascii')
        auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
        
        self.headers = {
            "Authorization": f"Basic {auth_b64}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
    
    async def get_cloud_id(self) -> Optional[str]:
        """Retrieve Atlassian Cloud ID from tenant info"""
        if self.cloud_id:
            return self.cloud_id
            
        try:
            url = f"{self.tenant_url}/_edge/tenant_info"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            data = response.json()
            self.cloud_id = data.get('cloudId')
            
            if self.cloud_id:
                logger.info(f"Retrieved Cloud ID: {self.cloud_id}")
                return self.cloud_id
            else:
                logger.error("Cloud ID not found in tenant info")
                return None
                
        except requests.RequestException as e:
            logger.error(f"Error retrieving Cloud ID: {e}")
            return None
    
    async def get_jsm_alerts(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Fetch alerts from JSM"""
        try:
            cloud_id = await self.get_cloud_id()
            if not cloud_id:
                logger.error("Cannot fetch JSM alerts without Cloud ID")
                return []
            
            url = f"{self.base_url}/{cloud_id}/v1/alerts"
            params = {
                "limit": limit,
                "offset": offset,
                "sort": "createdAt",
                "order": "desc"
            }
            
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            alerts = data.get('values', [])
            
            logger.info(f"Retrieved {len(alerts)} JSM alerts")
            return alerts
            
        except requests.RequestException as e:
            logger.error(f"Error fetching JSM alerts: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response content: {e.response.text}")
            return []
    
    async def get_jsm_alert_by_id(self, alert_id: str) -> Optional[Dict[str, Any]]:
        """Get specific JSM alert by ID"""
        try:
            cloud_id = await self.get_cloud_id()
            if not cloud_id:
                return None
            
            url = f"{self.base_url}/{cloud_id}/v1/alerts/{alert_id}"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            return response.json()
            
        except requests.RequestException as e:
            logger.error(f"Error fetching JSM alert {alert_id}: {e}")
            return None
    
    async def acknowledge_jsm_alert(self, alert_id: str, note: str = None, user: str = None) -> bool:
        """Acknowledge a JSM alert"""
        try:
            cloud_id = await self.get_cloud_id()
            if not cloud_id:
                return False
            
            url = f"{self.base_url}/{cloud_id}/v1/alerts/{alert_id}/acknowledge"
            
            payload = {}
            if note:
                payload["note"] = note
            if user:
                payload["user"] = user
            
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            
            logger.info(f"Successfully acknowledged JSM alert {alert_id}")
            return True
            
        except requests.RequestException as e:
            logger.error(f"Error acknowledging JSM alert {alert_id}: {e}")
            return False
    
    async def close_jsm_alert(self, alert_id: str, note: str = None, user: str = None) -> bool:
        """Close a JSM alert"""
        try:
            cloud_id = await self.get_cloud_id()
            if not cloud_id:
                return False
            
            url = f"{self.base_url}/{cloud_id}/v1/alerts/{alert_id}/close"
            
            payload = {}
            if note:
                payload["note"] = note
            if user:
                payload["user"] = user
            
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            
            logger.info(f"Successfully closed JSM alert {alert_id}")
            return True
            
        except requests.RequestException as e:
            logger.error(f"Error closing JSM alert {alert_id}: {e}")
            return False
    
    def create_alert_alias(self, grafana_alert: Dict[str, Any]) -> str:
        """Create an alias/hash for matching Grafana alerts with JSM alerts"""
        # Create a consistent hash based on alert characteristics
        alert_name = grafana_alert.get('alert_name', '')
        cluster = grafana_alert.get('cluster', '')
        pod = grafana_alert.get('pod', '')
        severity = grafana_alert.get('severity', '')
        
        # Create a string to hash
        hash_string = f"{alert_name}-{cluster}-{pod}-{severity}"
        
        # Create SHA256 hash
        hash_object = hashlib.sha256(hash_string.encode())
        return hash_object.hexdigest()
    
    def match_grafana_with_jsm(self, grafana_alerts: List[Dict], jsm_alerts: List[Dict]) -> List[Dict]:
        """Match Grafana alerts with JSM alerts based on alias, tags, and content"""
        matched_alerts = []
        
        # Create lookup maps for JSM alerts
        jsm_by_alias = {alert.get('alias'): alert for alert in jsm_alerts if alert.get('alias')}
        jsm_by_tags = {}
        
        # Index JSM alerts by relevant tags
        for jsm_alert in jsm_alerts:
            tags = jsm_alert.get('tags', [])
            for tag in tags:
                if tag.startswith('alertname:'):
                    alert_name = tag.split(':', 1)[1]
                    if alert_name not in jsm_by_tags:
                        jsm_by_tags[alert_name] = []
                    jsm_by_tags[alert_name].append(jsm_alert)
        
        for grafana_alert in grafana_alerts:
            match_info = {
                'grafana_alert': grafana_alert,
                'jsm_alert': None,
                'match_type': None,
                'match_confidence': 0
            }
            
            # Try to match by generated alias
            expected_alias = self.create_alert_alias(grafana_alert)
            if expected_alias in jsm_by_alias:
                match_info['jsm_alert'] = jsm_by_alias[expected_alias]
                match_info['match_type'] = 'alias'
                match_info['match_confidence'] = 95
            
            # Try to match by alert name in tags
            elif grafana_alert.get('alert_name') in jsm_by_tags:
                potential_matches = jsm_by_tags[grafana_alert.get('alert_name')]
                
                # Find best match based on additional criteria
                best_match = None
                best_score = 0
                
                for jsm_alert in potential_matches:
                    score = self._calculate_match_score(grafana_alert, jsm_alert)
                    if score > best_score:
                        best_score = score
                        best_match = jsm_alert
                
                if best_match and best_score > 50:  # Minimum confidence threshold
                    match_info['jsm_alert'] = best_match
                    match_info['match_type'] = 'tags_and_content'
                    match_info['match_confidence'] = best_score
            
            # Try to match by message content similarity
            else:
                best_match = None
                best_score = 0
                
                for jsm_alert in jsm_alerts:
                    score = self._calculate_content_similarity(grafana_alert, jsm_alert)
                    if score > best_score:
                        best_score = score
                        best_match = jsm_alert
                
                if best_match and best_score > 70:  # Higher threshold for content matching
                    match_info['jsm_alert'] = best_match
                    match_info['match_type'] = 'content_similarity'
                    match_info['match_confidence'] = best_score
            
            matched_alerts.append(match_info)
        
        return matched_alerts
    
    def _calculate_match_score(self, grafana_alert: Dict, jsm_alert: Dict) -> int:
        """Calculate match score between Grafana and JSM alerts"""
        score = 0
        
        # Check alert name match
        grafana_name = grafana_alert.get('alert_name', '').lower()
        jsm_tags = jsm_alert.get('tags', [])
        
        for tag in jsm_tags:
            if tag.startswith('alertname:') and grafana_name in tag.lower():
                score += 30
                break
        
        # Check cluster match
        grafana_cluster = grafana_alert.get('cluster', '').lower()
        if grafana_cluster:
            for tag in jsm_tags:
                if 'instance:' in tag and grafana_cluster in tag.lower():
                    score += 20
                    break
        
        # Check severity match
        grafana_severity = grafana_alert.get('severity', '').lower()
        if grafana_severity:
            for tag in jsm_tags:
                if f'severity:{grafana_severity}' in tag.lower():
                    score += 15
                    break
        
        # Check if JSM alert is from Grafana source
        if jsm_alert.get('source') == 'Grafana':
            score += 25
        
        # Check time proximity (alerts created close in time are more likely to match)
        grafana_time = grafana_alert.get('started_at')
        jsm_time = jsm_alert.get('createdAt')
        
        if grafana_time and jsm_time:
            try:
                grafana_dt = datetime.fromisoformat(grafana_time.replace('Z', '+00:00'))
                jsm_dt = datetime.fromisoformat(jsm_time.replace('Z', '+00:00'))
                
                time_diff = abs((grafana_dt - jsm_dt).total_seconds())
                
                # Give points for alerts created within reasonable time windows
                if time_diff < 300:  # 5 minutes
                    score += 10
                elif time_diff < 900:  # 15 minutes
                    score += 5
            except:
                pass
        
        return min(score, 100)  # Cap at 100
    
    def _calculate_content_similarity(self, grafana_alert: Dict, jsm_alert: Dict) -> int:
        """Calculate content similarity between alerts"""
        score = 0
        
        grafana_summary = grafana_alert.get('summary', '').lower()
        jsm_message = jsm_alert.get('message', '').lower()
        
        if not grafana_summary or not jsm_message:
            return 0
        
        # Simple keyword matching
        grafana_words = set(grafana_summary.split())
        jsm_words = set(jsm_message.split())
        
        common_words = grafana_words.intersection(jsm_words)
        if len(grafana_words) > 0:
            similarity = len(common_words) / len(grafana_words) * 100
            score = int(similarity)
        
        return min(score, 100)
    
    def get_alert_status_info(self, jsm_alert: Dict) -> Dict[str, Any]:
        """Extract status information from JSM alert"""
        return {
            'id': jsm_alert.get('id'),
            'tiny_id': jsm_alert.get('tinyId'),
            'status': jsm_alert.get('status'),  # open, acked, closed
            'acknowledged': jsm_alert.get('acknowledged', False),
            'owner': jsm_alert.get('owner'),
            'priority': jsm_alert.get('priority'),
            'created_at': jsm_alert.get('createdAt'),
            'updated_at': jsm_alert.get('updatedAt'),
            'last_occurred_at': jsm_alert.get('lastOccuredAt'),
            'count': jsm_alert.get('count', 1),
            'tags': jsm_alert.get('tags', []),
            'alias': jsm_alert.get('alias'),
            'integration_name': jsm_alert.get('integrationName'),
            'source': jsm_alert.get('source')
        }
