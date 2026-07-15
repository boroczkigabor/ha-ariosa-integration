from __future__ import annotations

from dataclasses import asdict
from typing import Any

from homeassistant.core import HomeAssistant

from . import AriosaConfigEntry
from .const import DOMAIN
from .coordinator import AriosaDataUpdateCoordinator


async def async_get_config_entry_diagnostics(
        hass: HomeAssistant,
        entry: AriosaConfigEntry,
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""

    coordinator: AriosaDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    return {
        "entry_data": dict(entry.data),
        "last_update_success": coordinator.last_update_success,
        "measurements": (
            asdict(coordinator.data) if coordinator.data is not None else None
        ),
    }