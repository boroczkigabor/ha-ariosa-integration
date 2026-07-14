from __future__ import annotations
from dataclasses import dataclass

from custom_components.ariosa import AriosaDataUpdateCoordinator


@dataclass
class AriosaRuntimeData:
    coordinator: AriosaDataUpdateCoordinator


@dataclass(slots=True, frozen=True)
class AriosaMeasurements:
    """Decoded measurements from the ventilation unit."""

    external_temperature: float
    external_humidity: float

    ejection_temperature: float
    ejection_humidity: float

    internal_temperature: float
    internal_humidity: float

    flow_temperature: float
    flow_humidity: float

    motor_1_rpm: int
    motor_2_rpm: int

    post_treatment: int

    machine_days: int
    filter_hours: int
