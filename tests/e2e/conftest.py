"""
Pytest configuration for E2E tests.
"""
import pytest
from pathlib import Path


@pytest.fixture(scope="session")
def base_url():
    """Provide base URL for testing."""
    return "http://localhost:3000"


@pytest.fixture(scope="session")
def screenshots_dir():
    """Create directory for test screenshots."""
    screenshots_path = Path(__file__).parent / "screenshots"
    screenshots_path.mkdir(exist_ok=True)
    return screenshots_path


@pytest.fixture
def take_screenshot(browser, screenshots_dir):
    """Fixture to take screenshots on test failure."""
    def _screenshot(name):
        filepath = screenshots_dir / f"{name}.png"
        # browser.save_screenshot(str(filepath))
        return filepath
    return _screenshot


@pytest.fixture(autouse=True)
def screenshot_on_failure(request, browser, screenshots_dir):
    """Automatically take screenshot on test failure."""
    yield
    if request.node.rep_call.failed:
        test_name = request.node.name
        screenshot_path = screenshots_dir / f"{test_name}_failure.png"
        # browser.save_screenshot(str(screenshot_path))


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Make test result available to fixtures."""
    outcome = yield
    rep = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep)


@pytest.fixture(scope="function")
def browser_options():
    """Provide browser options."""
    return {
        "headless": True,
        "window_size": (1920, 1080),
        "implicit_wait": 10,
        "page_load_timeout": 30
    }


@pytest.fixture
def test_user_credentials():
    """Provide test user credentials."""
    return {
        "technician": {
            "username": "test_technician",
            "password": "test_password_123"
        },
        "manager": {
            "username": "test_manager",
            "password": "test_password_456"
        },
        "admin": {
            "username": "test_admin",
            "password": "test_password_789"
        }
    }


@pytest.fixture
def wait_for_element():
    """Provide wait for element helper."""
    def _wait(selector, timeout=10):
        # Wait for element to be visible
        pass
    return _wait


@pytest.fixture
def login_as_user(browser, base_url):
    """Helper to login as specific user."""
    def _login(username, password):
        # Navigate to login page
        # Enter credentials
        # Submit form
        # Wait for dashboard
        pass
    return _login
