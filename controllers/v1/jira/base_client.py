from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from models.v1.jira.issue import JiraIssue, JiraComment, JiraSearchResult

class BaseJiraClient(ABC):
    """Abstract interface defining required Jira Cloud API operations for the Agent."""

    @abstractmethod
    def search_issues(self, jql: str, max_results: int = 50) -> JiraSearchResult:
        """Search issues using Jira Query Language (JQL)."""
        pass

    @abstractmethod
    def get_issue(self, issue_key: str) -> Optional[JiraIssue]:
        """Fetch details of an issue by key or source_id."""
        pass

    @abstractmethod
    def get_comments(self, issue_key: str) -> List[JiraComment]:
        """Fetch all comments on an issue with parsed scenario metadata."""
        pass

    @abstractmethod
    def get_linked_issues(self, issue_key: str) -> List[str]:
        """Fetch keys/IDs of all linked issues (inward and outward dependencies)."""
        pass

    @abstractmethod
    def create_issue(self, fields: Dict[str, Any]) -> str:
        """Create a new issue in Jira and return its assigned key."""
        pass

    @abstractmethod
    def add_comment(self, issue_key: str, body: str) -> str:
        """Add a comment to an issue and return comment ID."""
        pass

    @abstractmethod
    def create_issue_link(self, inward_key: str, outward_key: str, link_type: str = "Relates") -> bool:
        """Create a link between two Jira issues."""
        pass

