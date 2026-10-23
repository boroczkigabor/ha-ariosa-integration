from dataclasses import replace

import pytest

from custom_components.ariosa.calculations import (
    efficiency_imbalance,
    exhaust_side_efficiency,
    heat_loss_power,
    relative_temperature_waste,
    supply_side_efficiency,
)
from tests.test_data import (
    WINTER_MEASUREMENTS,
    SUMMER_MEASUREMENTS,
)


def test_supply_side_efficiency_realistic() -> None:
    # (18 - 0) / (21 - 0) * 100
    result = supply_side_efficiency(WINTER_MEASUREMENTS)
    assert result == pytest.approx(85.7, abs=0.05)


def test_exhaust_side_efficiency_realistic() -> None:
    # (21 - 3) / (21 - 0) * 100
    result = exhaust_side_efficiency(WINTER_MEASUREMENTS)
    assert result == pytest.approx(85.7, abs=0.05)


def test_efficiency_imbalance_realistic() -> None:
    assert efficiency_imbalance(WINTER_MEASUREMENTS) == pytest.approx(0.0, abs=0.1)


def test_supply_side_efficiency_summer() -> None:
    """External warmer than internal (summer) is normal, not a fault —
    the ratio math should give a sensible result either direction.
    """
    result = supply_side_efficiency(SUMMER_MEASUREMENTS)
    assert result == pytest.approx(54.1, abs=0.05)


def test_exhaust_side_efficiency_summer() -> None:
    result = exhaust_side_efficiency(SUMMER_MEASUREMENTS)
    assert result == pytest.approx(63.5, abs=0.05)


def test_efficiency_imbalance_summer() -> None:
    assert efficiency_imbalance(SUMMER_MEASUREMENTS) == pytest.approx(-9.4, abs=0.1)


def test_efficiencies_are_none_when_temperature_spread_too_small() -> None:
    """When outdoor and indoor temperatures are nearly equal, the formulas
    are numerically unstable, so all three sensors should report unknown
    rather than a noisy or meaningless percentage.
    """

    data = replace(WINTER_MEASUREMENTS, internal_temperature=0.1)

    assert supply_side_efficiency(data) is None
    assert exhaust_side_efficiency(data) is None
    assert efficiency_imbalance(data) is None


def test_relative_temperature_waste_example() -> None:
    # outdoor 0 °C, reference 22 °C, internal 24.2 °C -> 2.2 / 22 = 10 %
    data = replace(
        WINTER_MEASUREMENTS, external_temperature=0.0, internal_temperature=24.2
    )
    assert relative_temperature_waste(data, 22.0) == pytest.approx(10.0, abs=0.05)


def test_relative_temperature_waste_below_zero_outdoor() -> None:
    # outdoor -10 °C, reference 20 °C, internal 19 °C -> 1 / 30 = 3.3 %
    data = replace(
        WINTER_MEASUREMENTS, external_temperature=-10.0, internal_temperature=19.0
    )
    assert relative_temperature_waste(data, 20.0) == pytest.approx(3.3, abs=0.05)


def test_relative_temperature_waste_small_gap_is_unknown() -> None:
    data = replace(WINTER_MEASUREMENTS, external_temperature=21.8)
    assert relative_temperature_waste(data, 22.0) is None


def test_heat_loss_power() -> None:
    # 2800 rpm on both motors -> 200 m3/h; 0.34 * 200 * 2 K = 136 W
    data = replace(
        WINTER_MEASUREMENTS,
        motor_1_rpm=2800,
        motor_2_rpm=1000,  # intake motor must not matter
        internal_temperature=20.0,
    )
    assert heat_loss_power(data, 22.0) == 136


def test_heat_loss_power_scales_with_airflow() -> None:
    slow = replace(
        WINTER_MEASUREMENTS,
        motor_1_rpm=1400,
        motor_2_rpm=3000,
        internal_temperature=20.0,
    )
    assert heat_loss_power(slow, 22.0) == 68
