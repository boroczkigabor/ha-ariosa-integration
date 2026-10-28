from __future__ import annotations

import itertools
from functools import lru_cache
from typing import TYPE_CHECKING

from .const import AIR_HEAT_W_PER_M3H_K, AIRFLOW_CURVE

if TYPE_CHECKING:
    from .models import AriosaMeasurements

# Below this outdoor/room temperature gap (°C), the efficiency formulas
# become numerically unstable (dividing by a near-zero denominator), so we
# report "unknown" rather than a meaningless or wildly noisy percentage.
EFFICIENCY_MIN_TEMPERATURE_SPREAD = 0.5

# Below this absolute efficiency (%) on *both* the supply and exhaust side,
# the heat exchanger core is likely being bypassed rather than actively
# exchanging heat/coolness. This threshold is a heuristic, not a
# manufacturer-specified value.
BYPASS_EFFICIENCY_THRESHOLD = 20.0


@lru_cache(maxsize=8)
def _efficiencies(data: AriosaMeasurements) -> tuple[float | None, float | None]:
    """Compute supply- and exhaust-side efficiency once per reading.

    `AriosaMeasurements` is an immutable, hashable snapshot, so this is
    cached on the snapshot itself: every derived value below that needs
    these two numbers (imbalance, bypass detection, and the two efficiency
    sensors themselves) shares this one calculation instead of repeating
    the division from scratch for the same reading. `maxsize=8` just keeps
    a few recent readings around — old ones fall out on their own once
    newer readings replace them as cache keys.

    Works the same whether the unit is recovering heat (outdoor colder
    than indoor, winter) or recovering "coolness" (outdoor warmer than
    indoor, summer) — only the ratio matters, not which direction the
    outdoor/room temperature gap runs.
    """

    denominator = data.internal_temperature - data.external_temperature

    if abs(denominator) < EFFICIENCY_MIN_TEMPERATURE_SPREAD:
        return None, None

    supply = (data.flow_temperature - data.external_temperature) / denominator
    exhaust = (data.internal_temperature - data.ejection_temperature) / denominator

    return round(supply * 100, 1), round(exhaust * 100, 1)


def supply_side_efficiency(data: AriosaMeasurements) -> float | None:
    """Efficiency from the incoming (supply) air's point of view.

    How much of the outdoor-to-room temperature gap the supply air closed
    by the time it reaches the room, after the heat exchanger.
    """

    supply, _exhaust = _efficiencies(data)

    return supply


def exhaust_side_efficiency(data: AriosaMeasurements) -> float | None:
    """Efficiency from the outgoing (exhaust) air's point of view.

    How much of the outdoor-to-room temperature gap was actually
    transferred out of the stale air before it's expelled outside.
    """

    _supply, exhaust = _efficiencies(data)

    return exhaust


def efficiency_imbalance(data: AriosaMeasurements) -> float | None:
    """Gap between the supply-side and exhaust-side efficiency, in points.

    A healthy, sealed unit keeps this close to zero. A growing gap can
    indicate a bypass/leak, unequal supply vs. extract airflow, or sensor
    drift — but not which of those it is; it's a "go take a look" signal,
    not a diagnosis.
    """

    supply, exhaust = _efficiencies(data)

    if supply is None or exhaust is None:
        return None

    return round(supply - exhaust, 1)


def relative_temperature_waste(
    data: AriosaMeasurements, reference_temperature: float
) -> float | None:
    """Temperature waste as a percentage of the outdoor-to-reference gap.

    `|internal - reference| / |reference - outdoor| * 100`. With outdoor
    0 °C, reference 22 °C and 2.2 °C of waste that is 10 %. Returns None
    when the outdoor/reference gap is below the efficiency spread threshold,
    since the ratio would be meaningless there.
    """

    gap = abs(reference_temperature - data.external_temperature)

    if gap < EFFICIENCY_MIN_TEMPERATURE_SPREAD:
        return None

    waste = abs(data.internal_temperature - reference_temperature)

    return round(waste / gap * 100, 1)


def estimated_airflow(data: AriosaMeasurements) -> float:
    """Estimated extract airflow in m3/h from the exhaust motor's rpm.

    Motor A (the exhaust/extract fan) is the unit's first motor register,
    exposed as `motor_1_rpm`. The rpm is mapped through the calibration
    points in `AIRFLOW_CURVE` with linear interpolation, and capped at the
    unit's maximum airflow.
    """

    rpm = data.motor_1_rpm

    for (rpm_low, flow_low), (rpm_high, flow_high) in itertools.pairwise(AIRFLOW_CURVE):
        if rpm <= rpm_high:
            fraction = (rpm - rpm_low) / (rpm_high - rpm_low)
            return flow_low + fraction * (flow_high - flow_low)

    return AIRFLOW_CURVE[-1][1]


def heat_loss_power(data: AriosaMeasurements, reference_temperature: float) -> int:
    """Heat lost in the extract ducts, in watts.

    `0.34 * airflow [m3/h] * |reference - internal| [K]`, where the
    reference is the room temperature and `internal` is the temperature of
    the extracted air by the time it reaches the unit.
    """

    delta = abs(reference_temperature - data.internal_temperature)

    return round(AIR_HEAT_W_PER_M3H_K * estimated_airflow(data) * delta)
