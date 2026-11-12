from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import AriosaConfigEntry
from .const import (
    CONF_ENABLE_CONTROL,
    DOMAIN,
    FAN_MODE_BY_MODBUS_VALUE,
    FAN_MODE_MODBUS_VALUES,
)
from .coordinator import AriosaDataUpdateCoordinator
from .entity import AriosaEntity

FAN_MODE_KEY = "fan_mode"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: AriosaConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the fan mode control, if the user enabled it."""

    if not entry.options.get(CONF_ENABLE_CONTROL):
        # Not just "don't add it": if control was switched off after having
        # been on, drop the leftover registry entry so the entity
        # disappears instead of lingering as unavailable.
        registry = er.async_get(hass)

        if entity_id := registry.async_get_entity_id(
            "select", DOMAIN, f"{entry.entry_id}_{FAN_MODE_KEY}"
        ):
            registry.async_remove(entity_id)

        return

    coordinator: AriosaDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities([AriosaFanModeSelect(coordinator, entry)])


class AriosaFanModeSelect(AriosaEntity, SelectEntity):
    """Fan mode of the unit: off, night, or level 1-3."""

    _attr_translation_key = FAN_MODE_KEY
    _attr_options = list(FAN_MODE_MODBUS_VALUES)
    _attr_icon = "mdi:fan"

    def __init__(
        self,
        coordinator: AriosaDataUpdateCoordinator,
        entry: AriosaConfigEntry,
    ) -> None:
        super().__init__(coordinator, entry)

        self._attr_unique_id = f"{entry.entry_id}_{FAN_MODE_KEY}"

    @property
    def current_option(self) -> str | None:
        """Return the current fan mode, or None if it isn't known."""

        if self.coordinator.data is None or self.coordinator.data.fan_mode is None:
            return None

        return FAN_MODE_BY_MODBUS_VALUE.get(self.coordinator.data.fan_mode)

    async def async_select_option(self, option: str) -> None:
        """Change the fan mode."""

        await self.coordinator.async_set_fan_mode(FAN_MODE_MODBUS_VALUES[option])
