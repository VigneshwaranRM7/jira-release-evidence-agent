import json
import re
from typing import List, Optional, Dict, Any
from controllers.v1.jira.base_client import BaseJiraClient
from models.v1.jira.issue import JiraIssue, JiraComment, JiraSearchResult
from utils.text_parser import parse_scenario_comment
from definitions import DATASET_PATH

class MockJiraClient(BaseJiraClient):
    """
    In-memory Mock Jira Cloud Provider.
    Implements full Jira REST API v3 semantics for offline testing, CI evaluation, and reproducible testing.
    """

    def __init__(self, dataset_path: Optional[str] = None):
        self.issues: Dict[str, JiraIssue] = {}
        self.source_id_to_key: Dict[str, str] = {}
        self.key_counter = 1000
        path = dataset_path or str(DATASET_PATH)
        self.load_from_dataset(path)

    def load_from_dataset(self, file_path: str):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            return

        dataset_label = data.get("dataset_label", "tyn-release-assessment-v2")
        records = data.get("records", [])

        # Pass 1: Create all issues
        for rec in records:
            source_id = rec.get("source_id")
            jira_key = f"REL-{self.key_counter}"
            self.key_counter += 1
            self.source_id_to_key[source_id] = jira_key

            comments = []
            for c_str in rec.get("comments", []):
                parsed = parse_scenario_comment(c_str)
                comments.append(JiraComment(
                    id=f"comm-{len(comments)+1}",
                    author="importer-bot",
                    created="2026-11-10T00:00:00Z",
                    body=c_str,
                    scenario_actor=parsed.get("actor"),
                    scenario_role=parsed.get("role"),
                    scenario_timestamp=parsed.get("timestamp")
                ))

            issue = JiraIssue(
                id=str(self.key_counter),
                key=jira_key,
                source_id=source_id,
                summary=rec.get("summary", ""),
                description=rec.get("description", ""),
                status=rec.get("recorded_status", "Done"),
                kind=rec.get("kind", "evidence"),
                release=rec.get("release"),
                labels=[dataset_label, f"kind-{rec.get('kind', 'evidence')}"],
                comments=comments,
                links=[],  # Will populate in Pass 2
                created="2026-11-01T00:00:00Z",
                updated="2026-11-08T00:00:00Z"
            )
            self.issues[jira_key] = issue
            # Also index by source_id for flexible direct lookup
            self.issues[source_id] = issue

        # Pass 2: Link issues
        for rec in records:
            source_id = rec.get("source_id")
            jira_key = self.source_id_to_key.get(source_id)
            if not jira_key:
                continue
            
            resolved_links = []
            for target_source_id in rec.get("links", []):
                target_key = self.source_id_to_key.get(target_source_id, target_source_id)
                resolved_links.append(target_key)
            
            # Store links on both the key and the source_id references
            self.issues[jira_key].links = resolved_links
            if source_id in self.issues:
                self.issues[source_id].links = resolved_links

    load_from_json = load_from_dataset


    def search_issues(self, jql: str, max_results: int = 50) -> JiraSearchResult:
        """Simulate JQL search with label, summary, and text filtering."""
        results = []
        jql_lower = jql.lower()

        # Extract label filter if present (e.g. labels = "tyn-release-assessment-v2")
        label_match = re.search(r'labels?\s*=\s*["\']?([^"\'\s]+)["\']?', jql_lower)
        target_label = label_match.group(1) if label_match else None

        # Extract summary / text filter if present
        text_match = re.search(r'(?:summary|text)\s*~\s*["\']([^"\']+)["\']', jql_lower)
        search_text = text_match.group(1).lower() if text_match else None

        seen_keys = set()
        for issue in self.issues.values():
            if issue.key in seen_keys:
                continue
            seen_keys.add(issue.key)

            # Check label scoping
            if target_label:
                issue_labels = [l.lower() for l in issue.labels]
                if target_label not in issue_labels:
                    continue

            # Check text query (searches summary, description, source_id, and comments, matching Jira text search)
            if search_text:
                comments_text = " ".join(c.body for c in issue.comments)
                full_content = (issue.summary + " " + issue.description + " " + issue.source_id + " " + comments_text).lower()
                if search_text not in full_content:
                    continue

            results.append(issue)
            if len(results) >= max_results:
                break

        return JiraSearchResult(total=len(results), issues=results)

    def get_issue(self, issue_key: str) -> Optional[JiraIssue]:
        return self.issues.get(issue_key)

    def get_comments(self, issue_key: str) -> List[JiraComment]:
        issue = self.get_issue(issue_key)
        return issue.comments if issue else []

    def get_linked_issues(self, issue_key: str) -> List[str]:
        issue = self.get_issue(issue_key)
        return issue.links if issue else []

    def create_issue(self, fields: Dict[str, Any]) -> str:
        key = f"REL-{self.key_counter}"
        self.key_counter += 1
        source_id = fields.get("source_id", key)
        new_issue = JiraIssue(
            id=str(self.key_counter),
            key=key,
            source_id=source_id,
            summary=fields.get("summary", ""),
            description=fields.get("description", ""),
            status=fields.get("status", "To Do"),
            kind=fields.get("kind", "evidence"),
            release=fields.get("release"),
            labels=fields.get("labels", []),
            comments=[],
            links=[]
        )
        self.issues[key] = new_issue
        self.issues[source_id] = new_issue
        self.source_id_to_key[source_id] = key
        return key

    def add_comment(self, issue_key: str, body: str) -> str:
        issue = self.get_issue(issue_key)
        if not issue:
            return ""
        parsed = parse_scenario_comment(body)
        c_id = f"comm-{len(issue.comments)+1}"
        comment = JiraComment(
            id=c_id,
            author="importer-bot",
            created="2026-11-10T00:00:00Z",
            body=body,
            scenario_actor=parsed.get("actor"),
            scenario_role=parsed.get("role"),
            scenario_timestamp=parsed.get("timestamp")
        )
        issue.comments.append(comment)
        return c_id

    def create_issue_link(self, inward_key: str, outward_key: str, link_type: str = "Relates") -> bool:
        inward = self.get_issue(inward_key)
        if inward and outward_key not in inward.links:
            inward.links.append(outward_key)
            return True
        return False
