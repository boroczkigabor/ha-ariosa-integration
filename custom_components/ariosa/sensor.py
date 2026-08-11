from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from unittest import case

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    PERCENTAGE,
    REVOLUTIONS_PER_MINUTE,
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
    UnitOfTemperature,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event

from . import AriosaConfigEntry
from .calculations import (
    efficiency_imbalance,
    exhaust_side_efficiency,
    supply_side_efficiency,
)
from .const import CONF_REFERENCE_TEMPERATURE_ENTITY, DOMAIN, SEASON_MODBUS_VALUES
from .coordinator import AriosaDataUpdateCoordinator
from .entity import AriosaEntity
from .models import AriosaMeasurements


@dataclass(frozen=True, kw_only=True)
class AriosaSensorEntityDescription(SensorEntityDescription):
    """Describes an Ariosa sensor entity."""

    value_fn: Callable[[AriosaMeasurements], float | int | str | None]


SENSOR_DESCRIPTIONS: tuple[AriosaSensorEntityDescription, ...] = (
    AriosaSensorEntityDescription(
        key="external_temperature",
        translation_key="external_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.external_temperature,
    ),
    AriosaSensorEntityDescription(
        key="external_humidity",
        translation_key="external_humidity",
        device_class=SensorDeviceClass.HUMIDITY,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.external_humidity,
    ),
    AriosaSensorEntityDescription(
        key="ejection_temperature",
        translation_key="ejection_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.ejection_temperature,
    ),
    AriosaSensorEntityDescription(
        key="ejection_humidity",
        translation_key="ejection_humidity",
        device_class=SensorDeviceClass.HUMIDITY,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.ejection_humidity,
    ),
    AriosaSensorEntityDescription(
        key="internal_temperature",
        translation_key="internal_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.internal_temperature,
    ),
    AriosaSensorEntityDescription(
        key="internal_humidity",
        translation_key="internal_humidity",
        device_class=SensorDeviceClass.HUMIDITY,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.internal_humidity,
    ),
    AriosaSensorEntityDescription(
        key="flow_temperature",
        translation_key="flow_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.flow_temperature,
    ),
    AriosaSensorEntityDescription(
        key="flow_humidity",
        translation_key="flow_humidity",
        device_class=SensorDeviceClass.HUMIDITY,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.flow_humidity,
    ),
    AriosaSensorEntityDescription(
        key="motor_1_rpm",
        translation_key="motor_1_rpm",
        native_unit_of_measurement=REVOLUTIONS_PER_MINUTE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.motor_1_rpm,
        icon="mdi:car-turbocharger",
    ),
    AriosaSensorEntityDescription(
        key="motor_2_rpm",
        translation_key="motor_2_rpm",
        native_unit_of_measurement=REVOLUTIONS_PER_MINUTE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.motor_2_rpm,
        icon="mdi:car-turbocharger",
    ),
    AriosaSensorEntityDescription(
        key="post_treatment",
        translation_key="post_treatment",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.post_treatment,
        icon="mdi:valve",
    ),
    AriosaSensorEntityDescription(
        key="machine_days",
        translation_key="machine_days",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.DAYS,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda data: data.machine_days,
    ),
    AriosaSensorEntityDescription(
        key="filter_hours",
        translation_key="filter_hours",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.HOURS,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda data: data.filter_hours,
    ),
    AriosaSensorEntityDescription(
        key="season",
        translation_key="season",
        device_class=SensorDeviceClass.ENUM,
        options=list(SEASON_MODBUS_VALUES.values()),
        value_fn=lambda data: SEASON_MODBUS_VALUES.get(data.season_status),
        icon="mdi:sun-snowflake-variant",
    ),
    AriosaSensorEntityDescription(
        key="supply_side_efficiency",
        translation_key="supply_side_efficiency",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=supply_side_efficiency,
        icon="mdi:gauge",
    ),
    AriosaSensorEntityDescription(
        key="exhaust_side_efficiency",
        translation_key="exhaust_side_efficiency",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=exhaust_side_efficiency,
        icon="mdi:gauge",
    ),
    AriosaSensorEntityDescription(
        key="efficiency_imbalance",
        translation_key="efficiency_imbalance",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=efficiency_imbalance,
        icon="mdi:scale-unbalanced",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: AriosaConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Ariosa sensors from a config entry."""

    coordinator: AriosaDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[AriosaEntity] = [
        AriosaSensor(coordinator, entry, description)
        for description in SENSOR_DESCRIPTIONS
    ]

    # Options is where a user-editable setting like this belongs; `data`
    # is only checked as a fallback for entries created by the earlier
    # version of this integration, which stored it in `data` because the
    # options flow didn't exist yet.
    reference_entity_id = entry.options.get(
        CONF_REFERENCE_TEMPERATURE_ENTITY
    ) or entry.data.get(CONF_REFERENCE_TEMPERATURE_ENTITY)
    if reference_entity_id:
        entities.append(
            AriosaTemperatureWasteSensor(coordinator, entry, reference_entity_id)
        )

    async_add_entities(entities)


class AriosaSensor(AriosaEntity, SensorEntity):
    """Representation of a single Ariosa measurement."""

    entity_description: AriosaSensorEntityDescription

    def __init__(
        self,
        coordinator: AriosaDataUpdateCoordinator,
        entry: AriosaConfigEntry,
        description: AriosaSensorEntityDescription,
    ) -> None:
        super().__init__(coordinator, entry)

        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"

    @property
    def native_value(self) -> float | int | None:
        """Return the current value of the sensor."""

        if self.coordinator.data is None:
            return None

        return self.entity_description.value_fn(self.coordinator.data)


class AriosaTemperatureWasteSensor(AriosaEntity, SensorEntity):
    """Absolute gap between internal temperature and a reference entity.

    Unlike the other sensors, this one isn't a pure function of
    `AriosaMeasurements` — it also depends on a user-chosen HA entity (e.g.
    a room thermostat's current value, or an indoor reference sensor), so it
    can't fit the `value_fn` description pattern used above.

    Represents how much temperature is being "wasted" in the air pipes
    relative to that reference: the bigger the gap, the more the air
    reaching the device deviates from the reference the user cares about.
    """

    _attr_translation_key = "temperature_waste"
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:vector-difference"

    def __init__(
        self,
        coordinator: AriosaDataUpdateCoordinator,
        entry: AriosaConfigEntry,
        reference_entity_id: str,
    ) -> None:
        super().__init__(coordinator, entry)

        self._reference_entity_id = reference_entity_id
        self._attr_unique_id = f"{entry.entry_id}_temperature_waste"

    async def async_added_to_hass(self) -> None:
        """Also update when the reference entity changes, not just on poll."""

        await super().async_added_to_hass()

        self.async_on_remove(
            async_track_state_change_event(
                self.hass,
                [self._reference_entity_id],
                self._handle_reference_state_change,
            )
        )

    @callback
    def _handle_reference_state_change(self, _event: object) -> None:
        self.async_write_ha_state()

    @property
    def native_value(self) -> float | None:
        """Return |internal temperature - reference temperature|."""

        if self.coordinator.data is None:
            return None

        reference_state = self.hass.states.get(self._reference_entity_id)

        if reference_state is None or reference_state.state in (
            STATE_UNKNOWN,
            STATE_UNAVAILABLE,
        ):
            return None

        try:
            reference_temperature = float(reference_state.state)
        except ValueError:
            return None

        return round(
            abs(self.coordinator.data.internal_temperature - reference_temperature),
            1,
        )
