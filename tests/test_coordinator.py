from unittest.mock import AsyncMock

import pytest

from custom_components.ariosa.coordinator import AriosaDataUpdateCoordinator
from tests.test_data import SUMMER_MEASUREMENTS


@pytest.mark.asyncio
async def test_update(hass):
    client = AsyncMock()

    client.read_inputs.return_value = SUMMER_MEASUREMENTS

    coordinator = AriosaDataUpdateCoordinator(
        hass,
        client,
    )

    await coordinator.async_refresh()

    assert coordinator.last_update_success

    assert coordinator.data.external_temperature == 32.5


@pytest.mark.asyncio
async def test_failed_first_setup_releases_client(hass):
    """If the unit is offline during setup, the client must be disconnected
    before HA retries with a new one - otherwise the old socket keeps the
    device's (single) Modbus connection occupied.
    """

    from unittest.mock import patch

    from homeassistant.config_entries import ConfigEntryState
    from homeassistant.const import CONF_HOST, CONF_PORT, CONF_SLAVE
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    from custom_components.ariosa.const import DOMAIN
    from custom_components.ariosa.exceptions import CannotConnect

    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: "192.168.1.10", CONF_PORT: 502, CONF_SLAVE: 1},
    )
    entry.add_to_hass(hass)

    with patch("custom_components.ariosa.AriosaClient") as client_cls:
        client = client_cls.return_value
        client.read_inputs = AsyncMock(side_effect=CannotConnect)
        client.disconnect = AsyncMock()

        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        assert entry.state is ConfigEntryState.SETUP_RETRY
        client.disconnect.assert_awaited()
