from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import AriosaConfigEntry
from .calculations import bypass_likely_active
from .const import DOMAIN
from .coordinator import AriosaDataUpdateCoordinator
from .entity import AriosaEntity
from .models import AriosaMeasurements


@dataclass(frozen=True, kw_only=True)
class AriosaBinarySensorEntityDescription(BinarySensorEntityDescription):
    """Describes an Ariosa binary sensor entity."""

    value_fn: Callable[[AriosaMeasurements], bool | None]


BINARY_SENSOR_DESCRIPTIONS: tuple[AriosaBinarySensorEntityDescription, ...] = (
    AriosaBinarySensorEntityDescription(
        key="bypass_active",
        translation_key="bypass_active",
        device_class=BinarySensorDeviceClass.OPENING,
        value_fn=bypass_likely_active,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: AriosaConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Ariosa binary sensors from a config entry."""

    coordinator: AriosaDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(
        AriosaBinarySensor(coordinator, entry, description)
        for description in BINARY_SENSOR_DESCRIPTIONS
    )


class AriosaBinarySensor(AriosaEntity, BinarySensorEntity):
    """Representation of a derived Ariosa binary state."""

    entity_description: AriosaBinarySensorEntityDescription

    def __init__(
        self,
        coordinator: AriosaDataUpdateCoordinator,
        entry: AriosaConfigEntry,
        description: AriosaBinarySensorEntityDescription,
    ) -> None:
        super().__init__(coordinator, entry)

        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"

    @property
    def is_on(self) -> bool | None:
        """Return true if the bypass is likely active."""

        if self.coordinator.data is None:
            return None

        return self.entity_description.value_fn(self.coordinator.data)
