import os
import pytest
from fastapi.testclient import TestClient

# Set dummy key BEFORE importing app to avoid ChatOpenAI init crash
os.environ["OPENAI_API_KEY"] = "sk-dummy-key-for-testing-only"

from app.main import app, SYSTEM_ACTIVE

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture(autouse=True)
def reset_system_state():
    """Reset the global SYSTEM_ACTIVE flag before each test."""
    import app.main
    app.main.SYSTEM_ACTIVE = True
    yield
