from dataclasses import replace

import pytest

from custom_components.ariosa.sensor import (
    efficiency_imbalance,
    exhaust_side_efficiency,
    supply_side_efficiency,
)
from tests.test_data import (
    REALISTIC_MEASUREMENTS,
    SUMMER_MEASUREMENTS,
)


def test_supply_side_efficiency_realistic() -> None:
    # (18 - 0) / (21 - 0) * 100
    result = supply_side_efficiency(REALISTIC_MEASUREMENTS)
    assert result == pytest.approx(85.7, abs=0.05)


def test_exhaust_side_efficiency_realistic() -> None:
    # (21 - 3) / (21 - 0) * 100
    result = exhaust_side_efficiency(REALISTIC_MEASUREMENTS)
    assert result == pytest.approx(85.7, abs=0.05)


def test_efficiency_imbalance_realistic() -> None:
    assert efficiency_imbalance(REALISTIC_MEASUREMENTS) == pytest.approx(0.0, abs=0.1)


def test_supply_side_efficiency_summer() -> None:
    """External warmer than internal (summer) is normal, not a fault —
    the ratio math should give a sensible result either direction.
    """
    # (27 - 32) / (24 - 32) * 100
    result = supply_side_efficiency(SUMMER_MEASUREMENTS)
    assert result == pytest.approx(62.5, abs=0.05)


def test_exhaust_side_efficiency_summer() -> None:
    # (24 - 29) / (24 - 32) * 100
    result = exhaust_side_efficiency(SUMMER_MEASUREMENTS)
    assert result == pytest.approx(62.5, abs=0.05)


def test_efficiency_imbalance_summer() -> None:
    assert efficiency_imbalance(SUMMER_MEASUREMENTS) == pytest.approx(0.0, abs=0.1)


def test_efficiencies_are_none_when_temperature_spread_too_small() -> None:
    """When outdoor and indoor temperatures are nearly equal, the formulas
    are numerically unstable, so all three sensors should report unknown
    rather than a noisy or meaningless percentage.
    """

    data = replace(REALISTIC_MEASUREMENTS, internal_temperature=0.1)

    assert supply_side_efficiency(data) is None
    assert exhaust_side_efficiency(data) is None
    assert efficiency_imbalance(data) is None
