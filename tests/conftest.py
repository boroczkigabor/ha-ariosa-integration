import pytest

pytest_plugins = ["pytest_homeassistant_custom_component.common"]


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Make custom_components/ (e.g. ariosa) loadable in every test's hass fixture."""
    yield
