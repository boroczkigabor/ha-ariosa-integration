from __future__ import annotations

import logging

from homeassistant.core import HomeAssistant
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
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name="Ariosa",
            update_interval=UPDATE_INTERVAL,
        )

        self.client = client

    async def _async_update_data(self) -> AriosaMeasurements:
        """Fetch latest data."""

        try:
            return await self.client.read_inputs()

        except AriosaError as err:
            raise UpdateFailed(str(err)) from err
