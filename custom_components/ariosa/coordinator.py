from __future__ import annotations

import logging
from dataclasses import replace

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import UPDATE_INTERVAL
from .exceptions import AriosaError
from .modbus_client import AriosaClient
from .models import AriosaMeasurements

_LOGGER = logging.getLogger(__name__)


class AriosaDataUpdateCoordinator(
    DataUpdateCoordinator[AriosaMeasurements],
):
    """Coordinator for Ariosa."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: AriosaClient,
        *,
        control_enabled: bool = False,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name="Ariosa",
            update_interval=UPDATE_INTERVAL,
        )

        self.client = client
        self.control_enabled = control_enabled

        # Last known fan mode, used when the unit doesn't let us read the
        # control register back: we then show what we last wrote.
        self._fan_mode: int | None = None

    async def _async_update_data(self) -> AriosaMeasurements:
        """Fetch latest data."""

        try:
            data = await self.client.read_inputs()

            if self.control_enabled:
                mode = await self.client.read_fan_mode()

                if mode is None:
                    mode = self._fan_mode
                else:
                    self._fan_mode = mode

                data = replace(data, fan_mode=mode)

        except AriosaError as err:
            raise UpdateFailed(str(err)) from err

        return data

    async def async_set_fan_mode(self, value: int) -> None:
        """Write the fan mode and reflect it immediately in the entities."""

        try:
            await self.client.write_fan_mode(value)

        except AriosaError as err:
            msg = f"Could not set the fan mode: {err}"
            raise HomeAssistantError(msg) from err

        self._fan_mode = value

        if self.data is not None:
            self.async_set_updated_data(replace(self.data, fan_mode=value))
