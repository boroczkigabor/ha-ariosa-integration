from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    PERCENTAGE,
    REVOLUTIONS_PER_MINUTE,
    UnitOfTemperature,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import AriosaConfigEntry
from .const import DOMAIN
from .coordinator import AriosaDataUpdateCoordinator
from .entity import AriosaEntity
from .models import AriosaMeasurements


@dataclass(frozen=True, kw_only=True)
class AriosaSensorEntityDescription(SensorEntityDescription):
    """Describes an Ariosa sensor entity."""

    value_fn: Callable[[AriosaMeasurements], float | int | None]


# Below this outdoor/room temperature gap (°C), the efficiency formulas
# become numerically unstable (dividing by a near-zero denominator), so we
# report "unknown" rather than a meaningless or wildly noisy percentage.
_EFFICIENCY_MIN_TEMPERATURE_SPREAD = 0.5


def _supply_side_efficiency(data: AriosaMeasurements) -> float | None:
    """Efficiency from the incoming (supply) air's point of view.

    How much of the outdoor-to-room temperature gap the supply air closed
    by the time it reaches the room, after the heat exchanger. Works the
    same whether the unit is recovering heat (outdoor colder than indoor,
    winter) or recovering "coolness" (outdoor warmer than indoor, summer)
    — only the ratio matters, not which direction the gap runs.
    """

    denominator = data.internal_temperature - data.external_temperature

    if abs(denominator) < _EFFICIENCY_MIN_TEMPERATURE_SPREAD:
        return None

    efficiency = (data.flow_temperature - data.external_temperature) / denominator

    return round(efficiency * 100, 1)


def _exhaust_side_efficiency(data: AriosaMeasurements) -> float | None:
    """Efficiency from the outgoing (exhaust) air's point of view.

    How much of the outdoor-to-room temperature gap was actually
    transferred out of the stale air before it's expelled outside. Same
    formula regardless of heating or cooling season — see
    `_supply_side_efficiency`.
    """

    denominator = data.internal_temperature - data.external_temperature

    if abs(denominator) < _EFFICIENCY_MIN_TEMPERATURE_SPREAD:
        return None

    efficiency = (data.internal_temperature - data.ejection_temperature) / denominator

    return round(efficiency * 100, 1)


def _efficiency_imbalance(data: AriosaMeasurements) -> float | None:
    """Gap between the supply-side and exhaust-side efficiency, in points.

    A healthy, sealed unit keeps this close to zero. A growing gap can
    indicate a bypass/leak, unequal supply vs. extract airflow, or sensor
    drift — but not which of those it is; it's a "go take a look" signal,
    not a diagnosis.
    """

    supply = _supply_side_efficiency(data)
    exhaust = _exhaust_side_efficiency(data)

    if supply is None or exhaust is None:
        return None

    return round(supply - exhaust, 1)


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
    ),
    AriosaSensorEntityDescription(
        key="motor_2_rpm",
        translation_key="motor_2_rpm",
        native_unit_of_measurement=REVOLUTIONS_PER_MINUTE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.motor_2_rpm,
    ),
    AriosaSensorEntityDescription(
        key="post_treatment",
        translation_key="post_treatment",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.post_treatment,
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
        key="supply_side_efficiency",
        translation_key="supply_side_efficiency",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_supply_side_efficiency,
    ),
    AriosaSensorEntityDescription(
        key="exhaust_side_efficiency",
        translation_key="exhaust_side_efficiency",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_exhaust_side_efficiency,
    ),
    AriosaSensorEntityDescription(
        key="efficiency_imbalance",
        translation_key="efficiency_imbalance",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_efficiency_imbalance,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: AriosaConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Ariosa sensors from a config entry."""

    coordinator: AriosaDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(
        AriosaSensor(coordinator, entry, description)
        for description in SENSOR_DESCRIPTIONS
    )


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
