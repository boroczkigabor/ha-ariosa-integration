from unittest.mock import AsyncMock

import pytest

from custom_components.ariosa.coordinator import AriosaDataUpdateCoordinator
from tests.test_data import REALISTIC_MEASUREMENTS


@pytest.mark.asyncio
async def test_update(hass):
    client = AsyncMock()

    client.read_inputs.return_value = REALISTIC_MEASUREMENTS

    coordinator = AriosaDataUpdateCoordinator(
        hass,
        client,
    )

    await coordinator.async_refresh()

    assert coordinator.last_update_success

    assert coordinator.data.external_temperature == 23.5
