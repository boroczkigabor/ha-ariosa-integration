from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntityDescription,
)
from homeassistant.const import EntityCategory

if TYPE_CHECKING:
    from .models import AriosaMeasurements


@dataclass(frozen=True, kw_only=True)
class AriosaAlarmSensorEntityDescription(BinarySensorEntityDescription):
    """Describes an Ariosa alarm sensor entity."""

    # Both need a type annotation to actually override the inherited
    # dataclass field defaults - an unannotated assignment here is just a
    # shadowed class attribute that the generated __init__ never reads.
    device_class: BinarySensorDeviceClass | None = BinarySensorDeviceClass.PROBLEM
    # Diagnostic groups all alarms together in their own collapsible
    # section on the device's card, separate from the main sensors -
    # this is what HA uses for "read-only, not the main function, but
    # worth surfacing" entities like these.
    entity_category: EntityCategory | None = EntityCategory.DIAGNOSTIC

    value_fn: Callable[[AriosaMeasurements], bool | None]
