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
from .ariosa_alarm_entity import AriosaAlarmSensorEntityDescription
from .const import DOMAIN
from .coordinator import AriosaDataUpdateCoordinator
from .entity import AriosaEntity
from .models import AriosaMeasurements


@dataclass(frozen=True, kw_only=True)
class AriosaBinarySensorEntityDescription(BinarySensorEntityDescription):
    """Describes an Ariosa binary sensor entity."""

    value_fn: Callable[[AriosaMeasurements], bool | None]


BINARY_SENSOR_DESCRIPTIONS: tuple[BinarySensorEntityDescription, ...] = (
    AriosaBinarySensorEntityDescription(
        key="preheater_status",
        translation_key="preheater_status",
        device_class=BinarySensorDeviceClass.POWER,
        value_fn=lambda data: data.preheater_status,
    ),
    AriosaBinarySensorEntityDescription(
        key="bypass_active",
        translation_key="bypass_active",
        device_class=BinarySensorDeviceClass.OPENING,
        value_fn=lambda data: data.bypass_open,
    ),
    AriosaAlarmSensorEntityDescription(
        key="general_alarm",
        translation_key="general_alarm",
        value_fn=lambda data: data.general_alarm,
    ),
    AriosaAlarmSensorEntityDescription(
        key="filter_change_alarm",
        translation_key="filter_change_alarm",
        value_fn=lambda data: data.filter_change_alarm,
    ),
    AriosaAlarmSensorEntityDescription(
        key="filter_clogged_alarm",
        translation_key="filter_clogged_alarm",
        value_fn=lambda data: data.filter_clogged_alarm,
    ),
    AriosaAlarmSensorEntityDescription(
        key="frost_protection_alarm",
        translation_key="frost_protection_alarm",
        value_fn=lambda data: data.frost_protection_alarm,
    ),
    AriosaAlarmSensorEntityDescription(
        key="connection_alarm",
        translation_key="connection_alarm",
        value_fn=lambda data: data.connection_alarm,
    ),
    AriosaAlarmSensorEntityDescription(
        key="motor_alarm",
        translation_key="motor_alarm",
        value_fn=lambda data: data.motor_alarm,
    ),
    AriosaAlarmSensorEntityDescription(
        key="sensor_alarm",
        translation_key="sensor_alarm",
        value_fn=lambda data: data.sensor_alarm,
    ),
    AriosaAlarmSensorEntityDescription(
        key="motor_protection_alarm",
        translation_key="motor_protection_alarm",
        value_fn=lambda data: data.motor_protection_alarm,
    ),
    AriosaAlarmSensorEntityDescription(
        key="preheater_alarm",
        translation_key="preheater_alarm",
        value_fn=lambda data: data.preheater_alarm,
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
