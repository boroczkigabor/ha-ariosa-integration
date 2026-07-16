from __future__ import annotations

from functools import lru_cache

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


def bypass_likely_active(data: AriosaMeasurements) -> bool | None:
    """Best-effort guess at whether the heat exchanger bypass is engaged.

    This is inferred purely from temperature behavior — the unit's own
    bypass Modbus register isn't being read successfully yet. When bypass
    is active, incoming air passes the exchanger core largely untouched,
    so both supply-side and exhaust-side efficiency should collapse
    toward zero.

    Returns None when the outdoor/room temperature gap is too small to
    tell anything apart (efficiency itself is unknown in that case,
    bypassed or not).

    This is a heuristic, not a direct measurement: a partially-open or
    modulating bypass, a defrost cycle, or sensor drift can look similar.
    Treat it as a helpful hint, not a substitute for the real bypass
    register once that's working.
    """

    supply, exhaust = _efficiencies(data)

    if supply is None or exhaust is None:
        return None

    return (
        abs(supply) < BYPASS_EFFICIENCY_THRESHOLD
        and abs(exhaust) < BYPASS_EFFICIENCY_THRESHOLD
    )
