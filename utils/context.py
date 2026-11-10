import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()

class AppSettings(BaseSettings):
    jira_base_url: str = os.getenv("JIRA_BASE_URL", "")
    jira_user_email: str = os.getenv("JIRA_USER_EMAIL", "")
    jira_api_token: str = os.getenv("JIRA_API_TOKEN", "")
    jira_project_key: str = os.getenv("JIRA_PROJECT_KEY", "KAN")
    use_mock_jira: bool = os.getenv("USE_MOCK_JIRA", "false").lower() in ("true", "1", "yes")
    default_dataset_label: str = os.getenv("DEFAULT_DATASET_LABEL", "tyn-release-assessment-v2")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    llm_model: str = os.getenv("LLM_MODEL", "gemini-2.0-flash")

settings = AppSettings()
