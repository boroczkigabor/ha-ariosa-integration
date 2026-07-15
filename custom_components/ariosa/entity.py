from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import AriosaConfigEntry
from .const import DOMAIN, MANUFACTURER
from .coordinator import AriosaDataUpdateCoordinator

# No Modbus register currently exposes the unit's model or firmware version,
# so these are static placeholders rather than device-reported values.
DEVICE_MODEL = "Ventilation Unit"


class AriosaEntity(CoordinatorEntity[AriosaDataUpdateCoordinator]):
    """Base entity providing shared Ariosa device info."""

    _attr_has_entity_name = True

    def __init__(
            self,
            coordinator: AriosaDataUpdateCoordinator,
            entry: AriosaConfigEntry,
    ) -> None:
        super().__init__(coordinator)

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer=MANUFACTURER,
            model=DEVICE_MODEL,
        )
