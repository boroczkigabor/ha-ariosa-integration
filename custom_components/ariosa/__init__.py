from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant

from .const import PLATFORMS
from .coordinator import AriosaDataUpdateCoordinator
from .modbus_client import AriosaClient

type AriosaConfigEntry = ConfigEntry[AriosaDataUpdateCoordinator]


async def async_setup(
    hass: HomeAssistant,
    config: dict,
) -> bool:
    return True


async def async_setup_entry(
    hass: HomeAssistant,
    entry: AriosaConfigEntry,
) -> bool:
    """Set up config entry."""

    client = AriosaClient(
        host=entry.data[CONF_HOST],
        port=entry.data[CONF_PORT],
    )

    coordinator = AriosaDataUpdateCoordinator(
        hass,
        client,
    )

    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(
        entry,
        PLATFORMS,
    )

    return True


async def async_unload_entry(
    hass: HomeAssistant,
    entry: AriosaConfigEntry,
) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(
        entry,
        PLATFORMS,
    )

    if unload_ok:
        await entry.runtime_data.client.disconnect()

    return unload_ok