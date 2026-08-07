from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_SLAVE
from typing import TYPE_CHECKING

from .const import DOMAIN, PLATFORMS
from .coordinator import AriosaDataUpdateCoordinator
from .modbus_client import AriosaClient

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

type AriosaConfigEntry = ConfigEntry


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
        slave=entry.data[CONF_SLAVE],
    )

    coord = AriosaDataUpdateCoordinator(
        hass,
        client,
    )

    await coord.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coord

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    return True


async def _async_update_listener(
    hass: HomeAssistant,
    entry: AriosaConfigEntry,
) -> None:
    """Reload the entry when its options change.

    Options (currently just the reference temperature entity) are edited
    via the "Configure" options flow after setup. Reloading picks up the
    change immediately - adding or removing the temperature waste sensor
    as needed - without requiring a Home Assistant restart.
    """

    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(
    hass: HomeAssistant,
    entry: AriosaConfigEntry,
) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(
        entry,
        PLATFORMS,
    )

    if unload_ok:
        coord = hass.data[DOMAIN].pop(entry.entry_id)
        await coord.client.disconnect()

    return unload_ok
