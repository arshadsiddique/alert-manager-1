import requests
import logging
import base64
import hashlib
import re
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
            
            # Log sample JSM alert for debugging
            if alerts and settings.ENABLE_MATCH_LOGGING:
                sample_alert = alerts[0]
                logger.debug(f"Sample JSM alert: {sample_alert}")
            
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
    
    def extract_alert_name_from_jsm(self, jsm_alert: Dict[str, Any]) -> str:
        """Extract alert name from JSM alert using multiple strategies"""
        tags = jsm_alert.get('tags', [])
        
        # Strategy 1: Look for alertname in tags
        for tag in tags:
            if tag.startswith('alertname:'):
                return tag.split(':', 1)[1].strip()
        
        # Strategy 2: Extract from message
        message = jsm_alert.get('message', '')
        if message:
            # Look for patterns like "Alert: alertname" or similar
            patterns = [
                r'Alert:\s*([^\s\n]+)',
                r'alertname[:\s=]+([^\s\n,]+)',
                r'\*([^*]+)\*',  # Bold text in markdown
            ]
            
            for pattern in patterns:
                match = re.search(pattern, message, re.IGNORECASE)
                if match:
                    return match.group(1).strip()
        
        # Strategy 3: Use alias if available
        alias = jsm_alert.get('alias', '')
        if alias:
            return f"jsm-{alias[:20]}"
        
        # Fallback: use JSM alert ID
        return f"jsm-alert-{jsm_alert.get('tinyId', jsm_alert.get('id', 'unknown'))}"
    
    def extract_cluster_from_jsm(self, jsm_alert: Dict[str, Any]) -> Optional[str]:
        """Extract cluster information from JSM alert"""
        tags = jsm_alert.get('tags', [])
        
        # Look for cluster information in tags
        for tag in tags:
            if 'cluster' in tag.lower():
                if ':' in tag:
                    return tag.split(':', 1)[1].strip()
            if 'instance:' in tag:
                # Extract cluster from instance name
                instance = tag.split(':', 1)[1]
                # Common patterns: datanode-21-pro-cloud-shared-aws-us-east-1
                if '-cloud-' in instance:
                    parts = instance.split('-')
                    for i, part in enumerate(parts):
                        if part == 'cloud' and i > 0:
                            return '-'.join(parts[:i])
        
        # Look in message
        message = jsm_alert.get('message', '')
        cluster_patterns = [
            r'cluster[:\s=]+([^\s\n,]+)',
            r'datanode-\d+-([^-\s]+)',
            r'([^-\s]+)-cloud-',
        ]
        
        for pattern in cluster_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None
    
    def extract_severity_from_jsm(self, jsm_alert: Dict[str, Any]) -> Optional[str]:
        """Extract severity from JSM alert"""
        tags = jsm_alert.get('tags', [])
        
        # Look for severity in tags
        for tag in tags:
            if tag.startswith('severity:'):
                return tag.split(':', 1)[1].strip()
            if tag.startswith('og_priority:'):
                priority = tag.split(':', 1)[1].strip()
                # Map JSM priority to severity
                priority_map = {
                    'P1': 'critical',
                    'P2': 'warning', 
                    'P3': 'info',
                    'P4': 'info',
                    'P5': 'info'
                }
                return priority_map.get(priority, 'unknown')
        
        # Check JSM priority field
        priority = jsm_alert.get('priority', '')
        if priority:
            priority_map = {
                'P1': 'critical',
                'P2': 'warning',
                'P3': 'info',
                'P4': 'info', 
                'P5': 'info'
            }
            return priority_map.get(priority, 'unknown')
        
        return 'unknown'
    
    def create_alert_fingerprint(self, grafana_alert: Dict[str, Any]) -> str:
        """Create a consistent fingerprint for Grafana alerts"""
        # Use multiple fields to create a unique fingerprint
        alert_name = grafana_alert.get('alert_name', '')
        cluster = grafana_alert.get('cluster', '')
        severity = grafana_alert.get('severity', '')
        summary = grafana_alert.get('summary', '')
        
        # Create a normalized string
        fingerprint_data = f"{alert_name}|{cluster}|{severity}|{summary[:50]}"
        
        # Create hash
        return hashlib.sha256(fingerprint_data.encode()).hexdigest()[:16]
    
    def calculate_content_similarity_score(self, grafana_alert: Dict, jsm_alert: Dict) -> int:
        """Calculate similarity score between Grafana and JSM alerts"""
        score = 0
        
        # Extract JSM alert details
        jsm_alert_name = self.extract_alert_name_from_jsm(jsm_alert)
        jsm_cluster = self.extract_cluster_from_jsm(jsm_alert)
        jsm_severity = self.extract_severity_from_jsm(jsm_alert)
        jsm_message = jsm_alert.get('message', '').lower()
        
        # Grafana alert details
        grafana_alert_name = grafana_alert.get('alert_name', '').lower()
        grafana_cluster = grafana_alert.get('cluster', '').lower()
        grafana_severity = grafana_alert.get('severity', '').lower()
        grafana_summary = grafana_alert.get('summary', '').lower()
        
        # Alert name matching (highest weight)
        if grafana_alert_name and jsm_alert_name:
            if grafana_alert_name in jsm_alert_name.lower() or jsm_alert_name.lower() in grafana_alert_name:
                score += 40
            elif self._fuzzy_match(grafana_alert_name, jsm_alert_name.lower()):
                score += 30
        
        # Cluster matching
        if grafana_cluster and jsm_cluster:
            if grafana_cluster in jsm_cluster.lower() or jsm_cluster.lower() in grafana_cluster:
                score += 25
        
        # Severity matching
        if grafana_severity and jsm_severity:
            if grafana_severity == jsm_severity.lower():
                score += 15
        
        # Content similarity
        if grafana_summary and jsm_message:
            common_words = self._get_common_words(grafana_summary, jsm_message)
            if len(common_words) > 2:
                score += min(20, len(common_words) * 3)
        
        # Time proximity (alerts created within reasonable time)
        grafana_time = grafana_alert.get('started_at')
        jsm_time = jsm_alert.get('createdAt')
        
        if grafana_time and jsm_time:
            try:
                if isinstance(grafana_time, str):
                    grafana_dt = datetime.fromisoformat(grafana_time.replace('Z', '+00:00'))
                else:
                    grafana_dt = grafana_time
                    
                jsm_dt = datetime.fromisoformat(jsm_time.replace('Z', '+00:00'))
                
                time_diff = abs((grafana_dt - jsm_dt).total_seconds())
                
                # Bonus for alerts created close in time
                if time_diff < 300:  # 5 minutes
                    score += 10
                elif time_diff < 900:  # 15 minutes
                    score += 5
                elif time_diff < 3600:  # 1 hour
                    score += 2
            except Exception as e:
                logger.debug(f"Error parsing timestamps for matching: {e}")
        
        # Source bonus (if JSM alert is from Grafana)
        if jsm_alert.get('source') == 'Grafana' or jsm_alert.get('integrationName') == 'Grafana':
            score += 15
        
        return min(score, 100)  # Cap at 100
    
    def _fuzzy_match(self, str1: str, str2: str) -> bool:
        """Simple fuzzy matching for alert names"""
        # Remove common prefixes/suffixes and special characters
        clean1 = re.sub(r'[_-]', ' ', str1).strip()
        clean2 = re.sub(r'[_-]', ' ', str2).strip()
        
        words1 = set(clean1.split())
        words2 = set(clean2.split())
        
        if not words1 or not words2:
            return False
        
        # Check if significant portion of words match
        common = words1.intersection(words2)
        similarity = len(common) / max(len(words1), len(words2))
        
        return similarity > 0.6
    
    def _get_common_words(self, text1: str, text2: str) -> set:
        """Get common meaningful words between two texts"""
        # Skip common words
        skip_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did'}
        
        words1 = set(re.findall(r'\b\w+\b', text1.lower()))
        words2 = set(re.findall(r'\b\w+\b', text2.lower()))
        
        # Remove skip words and short words
        words1 = {w for w in words1 if len(w) > 2 and w not in skip_words}
        words2 = {w for w in words2 if len(w) > 2 and w not in skip_words}
        
        return words1.intersection(words2)
    
    def match_grafana_with_jsm(self, grafana_alerts: List[Dict], jsm_alerts: List[Dict]) -> List[Dict]:
        """Match Grafana alerts with JSM alerts using improved algorithm"""
        matched_alerts = []
        used_jsm_alerts = set()
        
        logger.info(f"Starting alert matching: {len(grafana_alerts)} Grafana alerts, {len(jsm_alerts)} JSM alerts")
        
        for grafana_alert in grafana_alerts:
            match_info = {
                'grafana_alert': grafana_alert,
                'jsm_alert': None,
                'match_type': 'none',
                'match_confidence': 0
            }
            
            best_match = None
            best_score = settings.ALERT_MATCH_CONFIDENCE_THRESHOLD
            best_match_type = 'none'
            
            # Try to match with each JSM alert
            for jsm_alert in jsm_alerts:
                if jsm_alert['id'] in used_jsm_alerts:
                    continue
                
                # Calculate similarity score
                score = self.calculate_content_similarity_score(grafana_alert, jsm_alert)
                
                if score > best_score:
                    best_score = score
                    best_match = jsm_alert
                    
                    # Determine match type based on score
                    if score >= 90:
                        best_match_type = 'high_confidence'
                    elif score >= 70:
                        best_match_type = 'content_similarity'
                    else:
                        best_match_type = 'low_confidence'
            
            # If we found a good match, use it
            if best_match:
                match_info['jsm_alert'] = best_match
                match_info['match_type'] = best_match_type
                match_info['match_confidence'] = best_score
                used_jsm_alerts.add(best_match['id'])
                
                if settings.ENABLE_MATCH_LOGGING:
                    logger.info(f"Matched alert '{grafana_alert.get('alert_name')}' with JSM alert {best_match.get('tinyId')} (score: {best_score})")
            
            matched_alerts.append(match_info)
        
        matches_found = len([m for m in matched_alerts if m['jsm_alert'] is not None])
        logger.info(f"Alert matching completed: {matches_found}/{len(matched_alerts)} alerts matched")
        
        return matched_alerts
    
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
            'source': jsm_alert.get('source'),
            'message': jsm_alert.get('message', '')
        }