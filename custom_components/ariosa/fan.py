from __future__ import annotations

from typing import Any

from homeassistant.components.fan import FanEntity, FanEntityFeature
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util.percentage import (
    ordered_list_item_to_percentage,
    percentage_to_ordered_list_item,
)

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

# The speed steps, lowest first: with four steps they are 25 / 50 / 75 / 100 %.
# "Off" isn't a step; it's the fan being turned off (0 %).
SPEED_ORDER: tuple[str, ...] = ("night", "level_1", "level_2", "level_3")

# What `turn_on` without a percentage switches to.
DEFAULT_ON_MODE = "level_2"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: AriosaConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the fan control, if the user enabled it."""

    registry = er.async_get(hass)
    unique_id = f"{entry.entry_id}_{FAN_MODE_KEY}"

    # An earlier version exposed this control as a select entity; drop its
    # leftover registry entry so it doesn't linger as "no longer provided".
    if select_id := registry.async_get_entity_id("select", DOMAIN, unique_id):
        registry.async_remove(select_id)

    if not entry.options.get(CONF_ENABLE_CONTROL):
        # Not just "don't add it": if control was switched off after having
        # been on, drop the registry entry so the entity disappears instead
        # of lingering as unavailable.
        if fan_id := registry.async_get_entity_id("fan", DOMAIN, unique_id):
            registry.async_remove(fan_id)

        return

    coordinator: AriosaDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities([AriosaFan(coordinator, entry)])


class AriosaFan(AriosaEntity, FanEntity):
    """The unit's fan: off, or night / level 1 / level 2 / level 3."""

    _attr_translation_key = FAN_MODE_KEY
    _attr_icon = "mdi:fan"
    _attr_speed_count = len(SPEED_ORDER)
    # The same four modes are offered both as speed steps (25-100 %) and as
    # named presets, so the UI can show "Night" / "Level 1" ... as text.
    _attr_preset_modes = list(SPEED_ORDER)
    _attr_supported_features = (
        FanEntityFeature.SET_SPEED
        | FanEntityFeature.PRESET_MODE
        | FanEntityFeature.TURN_ON
        | FanEntityFeature.TURN_OFF
    )

    def __init__(
        self,
        coordinator: AriosaDataUpdateCoordinator,
        entry: AriosaConfigEntry,
    ) -> None:
        super().__init__(coordinator, entry)

        self._attr_unique_id = f"{entry.entry_id}_{FAN_MODE_KEY}"

    @property
    def _mode(self) -> str | None:
        """Current mode key ("off", "night", ...), or None if unknown."""

        if self.coordinator.data is None or self.coordinator.data.fan_mode is None:
            return None

        return FAN_MODE_BY_MODBUS_VALUE.get(self.coordinator.data.fan_mode)

    @property
    def is_on(self) -> bool | None:
        """Return whether the fan is running."""

        mode = self._mode

        return None if mode is None else mode != "off"

    @property
    def percentage(self) -> int | None:
        """Return the speed as a percentage of the four steps."""

        mode = self._mode

        if mode is None:
            return None

        if mode == "off":
            return 0

        return ordered_list_item_to_percentage(SPEED_ORDER, mode)

    @property
    def preset_mode(self) -> str | None:
        """Return the current mode as a named preset (None when off)."""

        mode = self._mode

        return mode if mode in SPEED_ORDER else None

    async def _async_set_mode(self, mode: str) -> None:
        await self.coordinator.async_set_fan_mode(FAN_MODE_MODBUS_VALUES[mode])

    async def async_set_percentage(self, percentage: int) -> None:
        """Set the speed; 0 % turns the fan off."""

        if percentage == 0:
            await self._async_set_mode("off")
            return

        await self._async_set_mode(
            percentage_to_ordered_list_item(SPEED_ORDER, percentage)
        )

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set the mode by name."""

        await self._async_set_mode(preset_mode)

    async def async_turn_on(
        self,
        percentage: int | None = None,
        preset_mode: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Turn the fan on, at the given preset/speed or at level 1."""

        if preset_mode is not None:
            await self.async_set_preset_mode(preset_mode)
            return

        if percentage is None:
            await self._async_set_mode(DEFAULT_ON_MODE)
            return

        await self.async_set_percentage(percentage)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the fan off."""

        await self._async_set_mode("off")
