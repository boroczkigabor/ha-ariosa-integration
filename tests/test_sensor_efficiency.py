from dataclasses import replace

import pytest

from custom_components.ariosa.models import AriosaMeasurements
from custom_components.ariosa.sensor import (
    _efficiency_imbalance,
    _exhaust_side_efficiency,
    _supply_side_efficiency,
)

# A physically realistic winter scenario: cold outdoor air, warm indoor air,
# and the heat exchanger recovering most of the difference on both sides.
REALISTIC_MEASUREMENTS = AriosaMeasurements(
    external_temperature=0.0,
    external_humidity=80.0,
    ejection_temperature=3.0,
    ejection_humidity=90.0,
    internal_temperature=21.0,
    internal_humidity=45.0,
    flow_temperature=18.0,
    flow_humidity=30.0,
    motor_1_rpm=1200,
    motor_2_rpm=1190,
    post_treatment=0,
    machine_days=100,
    filter_hours=50,
)


def test_supply_side_efficiency_realistic() -> None:
    # (18 - 0) / (21 - 0) * 100
    result = _supply_side_efficiency(REALISTIC_MEASUREMENTS)
    assert result == pytest.approx(85.7, abs=0.05)


def test_exhaust_side_efficiency_realistic() -> None:
    # (21 - 3) / (21 - 0) * 100
    result = _exhaust_side_efficiency(REALISTIC_MEASUREMENTS)
    assert result == pytest.approx(85.7, abs=0.05)


def test_efficiency_imbalance_realistic() -> None:
    assert _efficiency_imbalance(REALISTIC_MEASUREMENTS) == pytest.approx(0.0, abs=0.1)


def test_efficiencies_are_none_when_temperature_spread_too_small() -> None:
    """When outdoor and indoor temperatures are nearly equal, the formulas
    are numerically unstable, so all three sensors should report unknown
    rather than a noisy or meaningless percentage.
    """

    data = replace(REALISTIC_MEASUREMENTS, internal_temperature=0.1)

    assert _supply_side_efficiency(data) is None
    assert _exhaust_side_efficiency(data) is None
    assert _efficiency_imbalance(data) is None
