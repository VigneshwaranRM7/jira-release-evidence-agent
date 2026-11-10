import requests
from requests.auth import HTTPBasicAuth
from typing import List, Optional, Dict, Any
from controllers.v1.jira.base_client import BaseJiraClient
from models.v1.jira.issue import JiraIssue, JiraComment, JiraSearchResult
from utils.text_parser import parse_scenario_comment

def extract_adf_text(content: Any) -> str:
    """Extract plain text recursively from Atlassian Document Format (ADF) or strings."""
    if not content:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, dict):
        text_val = content.get("text")
        if text_val is not None:
            return str(text_val)
        inner = []
        if "content" in content and isinstance(content["content"], list):
            for child in content["content"]:
                t = extract_adf_text(child)
                if t:
                    inner.append(t)
        else:
            for v in content.values():
                if isinstance(v, (dict, list)):
                    t = extract_adf_text(v)
                    if t:
                        inner.append(t)
        return " ".join(inner) if inner else ""
    if isinstance(content, list):
        items = [extract_adf_text(item) for item in content]
        return "\n".join([i for i in items if i])
    return str(content)

class CloudJiraClient(BaseJiraClient):
    """
    Live Atlassian Jira Cloud REST API v3 Client.
    Connects to real Jira Cloud instances with API token basic auth.
    Supports both /rest/api/3/search/jql and legacy /rest/api/3/search.
    """

    def __init__(self, base_url: str, user_email: str = "", api_token: str = "", email: str = "", project_key: str = "KAN"):
        self.base_url = base_url.rstrip("/")
        email_to_use = user_email or email
        self.auth = HTTPBasicAuth(email_to_use, api_token)
        self.project_key = project_key or "KAN"
        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

    def _url(self, endpoint: str) -> str:
        return f"{self.base_url}/rest/api/3/{endpoint.lstrip('/')}"

    def search_issues(self, jql: str, max_results: int = 50) -> JiraSearchResult:
        fields = ["summary", "description", "status", "labels", "issuelinks", "created", "updated"]
        
        # 1. Try modern Jira Cloud search endpoint: POST /rest/api/3/search/jql
        try:
            url = self._url("search/jql")
            resp = requests.post(
                url,
                json={"jql": jql, "maxResults": max_results, "fields": fields},
                auth=self.auth,
                headers=self.headers,
                timeout=20
            )
            if resp.status_code == 200:
                return self._parse_search_response(resp.json())
        except Exception:
            pass

        # 2. Try GET /rest/api/3/search/jql
        try:
            url = self._url("search/jql")
            params = {"jql": jql, "maxResults": max_results, "fields": ",".join(fields)}
            resp = requests.get(url, params=params, auth=self.auth, headers=self.headers, timeout=20)
            if resp.status_code == 200:
                return self._parse_search_response(resp.json())
        except Exception:
            pass

        # 3. Fallback to legacy GET /rest/api/3/search
        try:
            url = self._url("search")
            params = {"jql": jql, "maxResults": max_results, "fields": ",".join(fields)}
            resp = requests.get(url, params=params, auth=self.auth, headers=self.headers, timeout=20)
            if resp.status_code == 200:
                return self._parse_search_response(resp.json())
        except Exception:
            pass

        return JiraSearchResult(total=0, issues=[])

    def _parse_search_response(self, data: Dict[str, Any]) -> JiraSearchResult:
        issues = []
        for item in data.get("issues", []):
            fields = item.get("fields", {})
            desc_raw = fields.get("description", "")
            desc_text = extract_adf_text(desc_raw)
            links = []
            for l in fields.get("issuelinks", []):
                if "outwardIssue" in l:
                    links.append(l["outwardIssue"].get("key"))
                elif "inwardIssue" in l:
                    links.append(l["inwardIssue"].get("key"))
            
            issues.append(JiraIssue(
                id=item.get("id"),
                key=item.get("key"),
                source_id=item.get("key"),
                summary=fields.get("summary", ""),
                description=desc_text,
                status=fields.get("status", {}).get("name", "Unknown"),
                kind="evidence",
                labels=fields.get("labels", []),
                comments=[],
                links=[lk for lk in links if lk]
            ))
        return JiraSearchResult(total=data.get("total", len(issues)), issues=issues)

    def get_issue(self, issue_key: str) -> Optional[JiraIssue]:
        url = self._url(f"issue/{issue_key}")
        try:
            resp = requests.get(url, auth=self.auth, headers=self.headers, timeout=15)
            if resp.status_code != 200:
                return None
            
            item = resp.json()
            fields = item.get("fields", {})
            desc_text = extract_adf_text(fields.get("description", ""))
            
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
                description=desc_text,
                status=fields.get("status", {}).get("name", "Unknown"),
                kind="evidence",
                labels=fields.get("labels", []),
                comments=comments,
                links=links
            )
        except Exception:
            return None

    def get_comments(self, issue_key: str) -> List[JiraComment]:
        url = self._url(f"issue/{issue_key}/comment")
        try:
            resp = requests.get(url, auth=self.auth, headers=self.headers, timeout=15)
            if resp.status_code != 200:
                return []
            
            data = resp.json()
            comments = []
            for item in data.get("comments", []):
                body_raw = item.get("body", "")
                body_str = extract_adf_text(body_raw)
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
        except Exception:
            return []

    def get_linked_issues(self, issue_key: str) -> List[str]:
        issue = self.get_issue(issue_key)
        return issue.links if issue else []

    def create_issue(self, fields: Dict[str, Any]) -> str:
        url = self._url("issue")
        desc_text = fields.get("description", "")
        payload = {
            "fields": {
                "project": {"key": self.project_key},
                "summary": fields.get("summary", "Automated Record"),
                "description": {
                    "type": "doc",
                    "version": 1,
                    "content": [
                        {"type": "paragraph", "content": [{"type": "text", "text": desc_text}]}
                    ]
                },
                "issuetype": {"name": "Task"},
                "labels": fields.get("labels", [])
            }
        }
        try:
            resp = requests.post(url, json=payload, auth=self.auth, headers=self.headers, timeout=20)
            if resp.status_code in (200, 201):
                return resp.json().get("key", "")
            else:
                print(f"[Jira API Error creating issue] Status {resp.status_code}: {resp.text}")
                return ""
        except Exception as e:
            print(f"[Exception creating issue]: {e}")
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
        try:
            resp = requests.post(url, json=payload, auth=self.auth, headers=self.headers, timeout=15)
            if resp.status_code in (200, 201):
                return resp.json().get("id", "")
            else:
                print(f"[Jira API Error adding comment to {issue_key}] Status {resp.status_code}: {resp.text}")
                return ""
        except Exception as e:
            print(f"[Exception adding comment]: {e}")
            return ""

    def create_issue_link(self, inward_key: str, outward_key: str, link_type: str = "Relates") -> bool:
        url = self._url("issueLink")
        payload = {
            "type": {"name": link_type},
            "inwardIssue": {"key": inward_key},
            "outwardIssue": {"key": outward_key}
        }
        try:
            resp = requests.post(url, json=payload, auth=self.auth, headers=self.headers, timeout=15)
            if resp.status_code not in (200, 201):
                print(f"[Jira API Error creating link {inward_key} -> {outward_key}] Status {resp.status_code}: {resp.text}")
            return resp.status_code in (200, 201)
        except Exception as e:
            print(f"[Exception creating link]: {e}")
            return False

JiraCloudClient = CloudJiraClient
