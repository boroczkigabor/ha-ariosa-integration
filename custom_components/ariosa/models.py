from __future__ import annotations

from dataclasses import dataclass


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

    # Drive states

    pre_heater_status: bool
    bypass_open: bool
    season_status: int

    # Alarm statuses

    general_alarm: bool = False
    filter_change_alarm: bool = False
    filter_clogged_alarm: bool = False
    frost_protection_alarm: bool = False
    connection_alarm: bool = False
    motor_alarm: bool = False
    sensor_alarm: bool = False
    motor_protection_alarm: bool = False
    pre_heater_alarm: bool = False
