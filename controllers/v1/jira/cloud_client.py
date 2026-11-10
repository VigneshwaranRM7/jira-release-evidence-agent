import requests
from requests.auth import HTTPBasicAuth
from typing import List, Optional, Dict, Any
from controllers.v1.jira.base_client import BaseJiraClient
from models.v1.jira.issue import JiraIssue, JiraComment, JiraSearchResult
from utils.text_parser import parse_scenario_comment

class CloudJiraClient(BaseJiraClient):
    """
    Live Atlassian Jira Cloud REST API v3 Client.
    Connects to real Jira instances using API tokens and respects rate limits.
    """

    def __init__(self, base_url: str, user_email: str = "", api_token: str = "", email: str = "", project_key: str = "REL"):
        self.base_url = base_url.rstrip("/")
        email_to_use = user_email or email
        self.auth = HTTPBasicAuth(email_to_use, api_token)
        self.project_key = project_key
        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

    def _url(self, endpoint: str) -> str:
        return f"{self.base_url}/rest/api/3/{endpoint.lstrip('/')}"

    def search_issues(self, jql: str, max_results: int = 50) -> JiraSearchResult:
        url = self._url("search")
        params = {"jql": jql, "maxResults": max_results, "fields": "summary,description,status,labels,issuelinks,created,updated"}
        resp = requests.get(url, params=params, auth=self.auth, headers=self.headers, timeout=20)
        if resp.status_code != 200:
            return JiraSearchResult(total=0, issues=[])
        
        data = resp.json()
        issues = []
        for item in data.get("issues", []):
            fields = item.get("fields", {})
            issues.append(JiraIssue(
                id=item.get("id"),
                key=item.get("key"),
                source_id=item.get("key"),
                summary=fields.get("summary", ""),
                description=str(fields.get("description", "")),
                status=fields.get("status", {}).get("name", "Unknown"),
                kind="evidence",
                labels=fields.get("labels", []),
                comments=[],
                links=[l.get("outwardIssue", {}).get("key") for l in fields.get("issuelinks", []) if l.get("outwardIssue")]
            ))
        return JiraSearchResult(total=data.get("total", len(issues)), issues=issues)

    def get_issue(self, issue_key: str) -> Optional[JiraIssue]:
        url = self._url(f"issue/{issue_key}")
        resp = requests.get(url, auth=self.auth, headers=self.headers, timeout=15)
        if resp.status_code != 200:
            return None
        
        item = resp.json()
        fields = item.get("fields", {})
        links = []
        for l in fields.get("issuelinks", []):
            if "outwardIssue" in l:
                links.append(l["outwardIssue"]["key"])
            elif "inwardIssue" in l:
                links.append(l["inwardIssue"]["key"])
        
        comments = self.get_comments(issue_key)
        return JiraIssue(
            id=item.get("id"),
            key=item.get("key"),
            source_id=item.get("key"),
            summary=fields.get("summary", ""),
            description=str(fields.get("description", "")),
            status=fields.get("status", {}).get("name", "Unknown"),
            kind="evidence",
            labels=fields.get("labels", []),
            comments=comments,
            links=links
        )

    def get_comments(self, issue_key: str) -> List[JiraComment]:
        url = self._url(f"issue/{issue_key}/comment")
        resp = requests.get(url, auth=self.auth, headers=self.headers, timeout=15)
        if resp.status_code != 200:
            return []
        
        data = resp.json()
        comments = []
        for item in data.get("comments", []):
            body = item.get("body", "")
            # In Jira API v3, body can be Atlassian Document Format (ADF) dict or plain text
            if isinstance(body, dict):
                body_str = str(body)
            else:
                body_str = str(body)
            parsed = parse_scenario_comment(body_str)
            comments.append(JiraComment(
                id=item.get("id"),
                author=item.get("author", {}).get("displayName", "Importer"),
                created=item.get("created"),
                body=body_str,
                scenario_actor=parsed.get("actor"),
                scenario_role=parsed.get("role"),
                scenario_timestamp=parsed.get("timestamp")
            ))
        return comments

    def get_linked_issues(self, issue_key: str) -> List[str]:
        issue = self.get_issue(issue_key)
        return issue.links if issue else []

    def create_issue(self, fields: Dict[str, Any]) -> str:
        url = self._url("issue")
        payload = {
            "fields": {
                "project": {"key": self.project_key},
                "summary": fields.get("summary", "Automated Record"),
                "description": {
                    "type": "doc",
                    "version": 1,
                    "content": [
                        {"type": "paragraph", "content": [{"type": "text", "text": fields.get("description", "")}]}
                    ]
                },
                "issuetype": {"name": "Task"},
                "labels": fields.get("labels", [])
            }
        }
        resp = requests.post(url, json=payload, auth=self.auth, headers=self.headers, timeout=20)
        if resp.status_code in (200, 201):
            return resp.json().get("key", "")
        return ""

    def add_comment(self, issue_key: str, body: str) -> str:
        url = self._url(f"issue/{issue_key}/comment")
        payload = {
            "body": {
                "type": "doc",
                "version": 1,
                "content": [
                    {"type": "paragraph", "content": [{"type": "text", "text": body}]}
                ]
            }
        }
        resp = requests.post(url, json=payload, auth=self.auth, headers=self.headers, timeout=15)
        if resp.status_code in (200, 201):
            return resp.json().get("id", "")
        return ""

    def create_issue_link(self, inward_key: str, outward_key: str, link_type: str = "Relates") -> bool:
        url = self._url("issueLink")
        payload = {
            "type": {"name": link_type},
            "inwardIssue": {"key": inward_key},
            "outwardIssue": {"key": outward_key}
        }
        resp = requests.post(url, json=payload, auth=self.auth, headers=self.headers, timeout=15)
        return resp.status_code in (200, 201)

JiraCloudClient = CloudJiraClient

