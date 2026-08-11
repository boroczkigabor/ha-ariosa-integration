from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntityDescription,
)

if TYPE_CHECKING:
    from .models import AriosaMeasurements


@dataclass(frozen=True, kw_only=True)
class AriosaAlarmSensorEntityDescription(BinarySensorEntityDescription):
    """Describes an Ariosa alarm sensor entity."""

    device_class = BinarySensorDeviceClass.PROBLEM

    value_fn: Callable[[AriosaMeasurements], bool | None]
