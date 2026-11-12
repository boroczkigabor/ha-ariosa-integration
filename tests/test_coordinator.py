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


@pytest.mark.asyncio
async def test_fan_mode_not_read_when_control_disabled(hass):
    client = AsyncMock()
    client.read_inputs.return_value = SUMMER_MEASUREMENTS

    coordinator = AriosaDataUpdateCoordinator(hass, client)
    await coordinator.async_refresh()

    client.read_fan_mode.assert_not_called()
    assert coordinator.data.fan_mode is None


@pytest.mark.asyncio
async def test_fan_mode_read_when_control_enabled(hass):
    client = AsyncMock()
    client.read_inputs.return_value = SUMMER_MEASUREMENTS
    client.read_fan_mode.return_value = 2

    coordinator = AriosaDataUpdateCoordinator(hass, client, control_enabled=True)
    await coordinator.async_refresh()

    assert coordinator.data.fan_mode == 2


@pytest.mark.asyncio
async def test_unreadable_fan_mode_falls_back_to_last_written(hass):
    """If the unit won't report the register, show what we last wrote."""

    client = AsyncMock()
    client.read_inputs.return_value = SUMMER_MEASUREMENTS
    client.read_fan_mode.return_value = None

    coordinator = AriosaDataUpdateCoordinator(hass, client, control_enabled=True)
    await coordinator.async_refresh()

    assert coordinator.data.fan_mode is None

    await coordinator.async_set_fan_mode(3)

    client.write_fan_mode.assert_awaited_once_with(3)
    assert coordinator.data.fan_mode == 3

    await coordinator.async_refresh()

    assert coordinator.data.fan_mode == 3


@pytest.mark.asyncio
async def test_failed_write_raises_homeassistant_error(hass):
    from homeassistant.exceptions import HomeAssistantError

    from custom_components.ariosa.exceptions import WriteError

    client = AsyncMock()
    client.read_inputs.return_value = SUMMER_MEASUREMENTS
    client.read_fan_mode.return_value = 1
    client.write_fan_mode.side_effect = WriteError

    coordinator = AriosaDataUpdateCoordinator(hass, client, control_enabled=True)
    await coordinator.async_refresh()

    with pytest.raises(HomeAssistantError):
        await coordinator.async_set_fan_mode(3)

    assert coordinator.data.fan_mode == 1
