import os
import pytest
import pytest_asyncio
import httpx
from definitions import DATA_DIR
from main import app
from controllers.v1.jira.mock_client import MockJiraClient

@pytest.fixture(scope="session")
def dataset_path():
    path = os.path.join(DATA_DIR, "dataset.json")
    assert os.path.exists(path), f"dataset.json must exist at {path}"
    return path

@pytest.fixture(scope="session")
def mock_client(dataset_path):
    client = MockJiraClient(dataset_path)
    return client

@pytest_asyncio.fixture
async def async_client():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://testserver") as client:
        yield client
