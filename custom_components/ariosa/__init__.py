from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from .const import DOMAIN

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
    hass.data.setdefault(DOMAIN, {})

    return True


async def async_unload_entry(
    hass: HomeAssistant,
    entry: AriosaConfigEntry,
) -> bool:
    hass.data[DOMAIN].pop(entry.entry_id)

    return True
