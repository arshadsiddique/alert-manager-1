import requests
import logging
import base64
from typing import List, Dict, Any, Optional
from ..core.config import settings

logger = logging.getLogger(__name__)

class JiraService:
    def __init__(self):
        self.base_url = settings.JIRA_URL
        self.user_email = settings.JIRA_USER_EMAIL
        self.api_token = settings.JIRA_API_TOKEN
        self.project_key = settings.JIRA_PROJECT_KEY
        self.incident_issue_type = settings.JIRA_INCIDENT_ISSUE_TYPE
        self.acknowledge_transition = settings.JIRA_ACKNOWLEDGE_TRANSITION_NAME
        self.resolve_transition = settings.JIRA_RESOLVE_TRANSITION_NAME
        
        # Create basic auth header
        auth_string = f"{self.user_email}:{self.api_token}"
        auth_bytes = auth_string.encode('ascii')
        auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
        
        self.headers = {
            "Authorization": f"Basic {auth_b64}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    async def create_issue(self, alert_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new incident issue in Jira"""
        try:
            # Build Jira issue payload
            issue_payload = {
                "fields": {
                    "project": {"key": self.project_key},
                    "issuetype": {"name": self.incident_issue_type},
                    "summary": f"[ALERT] {alert_data.get('alert_name', 'Unknown Alert')} - {alert_data.get('cluster', 'Unknown Cluster')}",
                    "description": {
                        "type": "doc",
                        "version": 1,
                        "content": [
                            {
                                "type": "paragraph",
                                "content": [
                                    {
                                        "type": "text",
                                        "text": f"Alert: {alert_data.get('alert_name', 'Unknown')}\n"
                                    }
                                ]
                            },
                            {
                                "type": "paragraph",
                                "content": [
                                    {
                                        "type": "text",
                                        "text": f"Cluster: {alert_data.get('cluster', 'Unknown')}\n"
                                    }
                                ]
                            },
                            {
                                "type": "paragraph",
                                "content": [
                                    {
                                        "type": "text",
                                        "text": f"Pod: {alert_data.get('pod', 'Unknown')}\n"
                                    }
                                ]
                            },
                            {
                                "type": "paragraph",
                                "content": [
                                    {
                                        "type": "text",
                                        "text": f"Severity: {alert_data.get('severity', 'Unknown')}\n"
                                    }
                                ]
                            },
                            {
                                "type": "paragraph",
                                "content": [
                                    {
                                        "type": "text",
                                        "text": f"Summary: {alert_data.get('summary', 'No summary available')}\n"
                                    }
                                ]
                            },
                            {
                                "type": "paragraph",
                                "content": [
                                    {
                                        "type": "text",
                                        "text": f"Description: {alert_data.get('description', 'No description available')}\n"
                                    }
                                ]
                            }
                        ]
                    },
                    "priority": {"name": self._get_jira_priority(alert_data.get('severity'))},
                    "labels": [
                        "grafana-alert",
                        f"cluster-{alert_data.get('cluster', 'unknown').replace(' ', '-').lower()}",
                        f"severity-{alert_data.get('severity', 'unknown').lower()}"
                    ]
                }
            }
            
            url = f"{self.base_url}/rest/api/3/issue"
            response = requests.post(url, headers=self.headers, json=issue_payload)
            response.raise_for_status()
            
            issue_data = response.json()
            logger.info(f"Created Jira issue: {issue_data['key']}")
            
            return {
                "issue_key": issue_data["key"],
                "issue_id": issue_data["id"],
                "issue_url": f"{self.base_url}/browse/{issue_data['key']}"
            }
            
        except requests.RequestException as e:
            logger.error(f"Error creating Jira issue: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response content: {e.response.text}")
            return None
    
    async def get_issues(self, project_key: str = None) -> List[Dict[str, Any]]:
        """Fetch issues from Jira project with enhanced details"""
        try:
            if not project_key:
                project_key = self.project_key
                
            jql = f"project = {project_key} AND labels = grafana-alert ORDER BY created DESC"
            
            url = f"{self.base_url}/rest/api/3/search"
            response = requests.get(
                url,
                headers=self.headers,
                params={
                    "jql": jql,
                    "maxResults": 100,
                    "fields": "key,id,status,summary,created,updated,priority,assignee,resolution,resolutiondate"
                }
            )
            response.raise_for_status()
            
            data = response.json()
            issues = data.get('issues', [])
            
            # Parse assignee and resolution information
            for issue in issues:
                fields = issue.get('fields', {})
                assignee = fields.get('assignee')
                if assignee:
                    issue['assignee_name'] = assignee.get('displayName')
                    issue['assignee_email'] = assignee.get('emailAddress')
                else:
                    issue['assignee_name'] = None
                    issue['assignee_email'] = None
                
                # Add resolution information
                resolution = fields.get('resolution')
                if resolution:
                    issue['resolution_name'] = resolution.get('name')
                    issue['resolution_date'] = fields.get('resolutiondate')
                else:
                    issue['resolution_name'] = None
                    issue['resolution_date'] = None
            
            return issues
            
        except requests.RequestException as e:
            logger.error(f"Error fetching Jira issues: {e}")
            return []

    async def get_issue_details(self, issue_key: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific Jira issue"""
        try:
            url = f"{self.base_url}/rest/api/3/issue/{issue_key}"
            response = requests.get(
                url,
                headers=self.headers,
                params={
                    "fields": "key,id,status,summary,created,updated,priority,assignee,resolution,resolutiondate,description,comment"
                }
            )
            response.raise_for_status()
            
            issue_data = response.json()
            logger.debug(f"Retrieved details for issue: {issue_key}")
            
            return issue_data
            
        except requests.RequestException as e:
            logger.error(f"Error fetching issue details for {issue_key}: {e}")
            return None

    async def get_issue_comments(self, issue_key: str) -> List[Dict[str, Any]]:
        """Get comments from a Jira issue"""
        try:
            url = f"{self.base_url}/rest/api/3/issue/{issue_key}/comment"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            data = response.json()
            comments = data.get('comments', [])
            
            # Parse comment data
            parsed_comments = []
            for comment in comments:
                parsed_comment = {
                    'id': comment.get('id'),
                    'body': self._extract_comment_text(comment.get('body', {})),
                    'created': comment.get('created'),
                    'updated': comment.get('updated'),
                    'author': {
                        'displayName': comment.get('author', {}).get('displayName'),
                        'emailAddress': comment.get('author', {}).get('emailAddress')
                    }
                }
                parsed_comments.append(parsed_comment)
            
            return parsed_comments
            
        except requests.RequestException as e:
            logger.error(f"Error fetching comments for issue {issue_key}: {e}")
            return []

    def _extract_comment_text(self, comment_body: dict) -> str:
        """Extract plain text from Jira comment body structure"""
        if isinstance(comment_body, str):
            return comment_body
        
        if isinstance(comment_body, dict):
            content = comment_body.get('content', [])
            text_parts = []
            
            for item in content:
                if item.get('type') == 'paragraph':
                    paragraph_content = item.get('content', [])
                    for text_item in paragraph_content:
                        if text_item.get('type') == 'text':
                            text_parts.append(text_item.get('text', ''))
            
            return ' '.join(text_parts)
        
        return str(comment_body)

    async def check_issue_acknowledgment_status(self, issue_key: str) -> Dict[str, Any]:
        """Check detailed acknowledgment status of a Jira issue"""
        try:
            issue_details = await self.get_issue_details(issue_key)
            if not issue_details:
                return {'acknowledged': False, 'error': 'Issue not found'}
            
            fields = issue_details.get('fields', {})
            status = fields.get('status', {})
            status_name = status.get('name', '').lower()
            status_category = status.get('statusCategory', {}).get('name', '').lower()
            
            # Check assignee
            assignee = fields.get('assignee')
            is_assigned = assignee is not None
            
            # Check for acknowledgment in comments
            comments = await self.get_issue_comments(issue_key)
            acknowledgment_found = False
            acknowledger = None
            acknowledgment_date = None
            
            ack_keywords = ['acknowledged', 'investigating', 'looking into', 'working on', 'assigned', 'taking over']
            
            for comment in comments:
                comment_body = comment.get('body', '').lower()
                if any(keyword in comment_body for keyword in ack_keywords):
                    acknowledgment_found = True
                    acknowledger = comment.get('author', {}).get('displayName')
                    acknowledgment_date = comment.get('created')
                    break
            
            # Determine acknowledgment status
            is_acknowledged = (
                status_name in ['in progress', 'acknowledged', 'investigating', 'working'] or
                status_category == 'indeterminate' or
                is_assigned or
                acknowledgment_found
            )
            
            return {
                'acknowledged': is_acknowledged,
                'status_name': status_name,
                'status_category': status_category,
                'is_assigned': is_assigned,
                'assignee': assignee.get('displayName') if assignee else None,
                'acknowledgment_in_comments': acknowledgment_found,
                'acknowledger': acknowledger,
                'acknowledgment_date': acknowledgment_date,
                'issue_url': f"{self.base_url}/browse/{issue_key}"
            }
            
        except Exception as e:
            logger.error(f"Error checking acknowledgment status for {issue_key}: {e}")
            return {'acknowledged': False, 'error': str(e)}
    
    async def transition_issue(self, issue_key: str, transition_name: str, comment: str = None) -> bool:
        """Transition a Jira issue to a different status"""
        try:
            # First, get available transitions
            transitions_url = f"{self.base_url}/rest/api/3/issue/{issue_key}/transitions"
            transitions_response = requests.get(transitions_url, headers=self.headers)
            transitions_response.raise_for_status()
            
            transitions_data = transitions_response.json()
            transitions = transitions_data.get('transitions', [])
            
            # Find the transition ID by name
            transition_id = None
            for transition in transitions:
                if transition['name'].lower() == transition_name.lower():
                    transition_id = transition['id']
                    break
            
            if not transition_id:
                logger.warning(f"Transition '{transition_name}' not found for issue {issue_key}")
                available_transitions = [t['name'] for t in transitions]
                logger.info(f"Available transitions: {', '.join(available_transitions)}")
                return False
            
            # Build transition payload
            transition_payload = {
                "transition": {"id": transition_id}
            }
            
            # Add comment if provided
            if comment:
                transition_payload["update"] = {
                    "comment": [
                        {
                            "add": {
                                "body": {
                                    "type": "doc",
                                    "version": 1,
                                    "content": [
                                        {
                                            "type": "paragraph",
                                            "content": [
                                                {
                                                    "type": "text",
                                                    "text": comment
                                                }
                                            ]
                                        }
                                    ]
                                }
                            }
                        }
                    ]
                }
            
            # Execute transition
            url = f"{self.base_url}/rest/api/3/issue/{issue_key}/transitions"
            response = requests.post(url, headers=self.headers, json=transition_payload)
            response.raise_for_status()
            
            logger.info(f"Transitioned issue {issue_key} to {transition_name}")
            return True
            
        except requests.RequestException as e:
            logger.error(f"Error transitioning issue {issue_key}: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response content: {e.response.text}")
            return False
    
    async def acknowledge_issue(self, issue_key: str, comment: str = None) -> bool:
        """Acknowledge a Jira issue"""
        acknowledge_comment = f"Issue acknowledged via Alert Manager. {comment if comment else ''}".strip()
        return await self.transition_issue(issue_key, self.acknowledge_transition, acknowledge_comment)
    
    async def resolve_issue(self, issue_key: str, comment: str = None) -> bool:
        """Resolve a Jira issue"""
        resolve_comment = f"Issue resolved - alert no longer active in Grafana. {comment if comment else ''}".strip()
        return await self.transition_issue(issue_key, self.resolve_transition, resolve_comment)
    
    async def add_comment(self, issue_key: str, comment: str) -> bool:
        """Add a comment to a Jira issue"""
        try:
            comment_payload = {
                "body": {
                    "type": "doc",
                    "version": 1,
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [
                                {
                                    "type": "text",
                                    "text": comment
                                }
                            ]
                        }
                    ]
                }
            }
            
            url = f"{self.base_url}/rest/api/3/issue/{issue_key}/comment"
            response = requests.post(url, headers=self.headers, json=comment_payload)
            response.raise_for_status()
            
            return True
            
        except requests.RequestException as e:
            logger.error(f"Error adding comment to issue {issue_key}: {e}")
            return False
    
    def _get_jira_priority(self, severity: str) -> str:
        """Map Grafana alert severity to Jira priority"""
        severity_mapping = {
            "critical": "Highest",
            "warning": "High",
            "info": "Medium",
            "unknown": "Low"
        }
        return severity_mapping.get(severity.lower() if severity else "unknown", "Medium")