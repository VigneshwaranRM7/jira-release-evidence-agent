import os
from pydantic_settings import BaseSettings

class AppSettings(BaseSettings):
    jira_base_url: str = os.getenv("JIRA_BASE_URL", "https://mock.atlassian.net")
    jira_user_email: str = os.getenv("JIRA_USER_EMAIL", "agent@mock.jira")
    jira_api_token: str = os.getenv("JIRA_API_TOKEN", "mock_token")
    jira_project_key: str = os.getenv("JIRA_PROJECT_KEY", "REL")
    use_mock_jira: bool = os.getenv("USE_MOCK_JIRA", "true").lower() in ("true", "1", "yes")
    default_dataset_label: str = os.getenv("DEFAULT_DATASET_LABEL", "tyn-release-assessment-v2")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    llm_model: str = os.getenv("LLM_MODEL", "gpt-4o")

settings = AppSettings()

