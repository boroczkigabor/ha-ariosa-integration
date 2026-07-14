from unittest.mock import AsyncMock

import pytest

from custom_components.ariosa.coordinator import AriosaDataUpdateCoordinator
from custom_components.ariosa.models import AriosaMeasurements


@pytest.mark.asyncio
async def test_update(hass):
    client = AsyncMock()

    client.read_inputs.return_value = AriosaMeasurements(
        external_temperature=23.5,
        external_humidity=65.0,
        ejection_temperature=20.0,
        ejection_humidity=40.0,
        internal_temperature=22.0,
        internal_humidity=45.0,
        flow_temperature=21.0,
        flow_humidity=44.0,
        motor_1_rpm=1000,
        motor_2_rpm=1000,
        post_treatment=10,
        machine_days=100,
        filter_hours=250,
    )

    coordinator = AriosaDataUpdateCoordinator(
        hass,
        client,
    )

    await coordinator.async_refresh()

    assert coordinator.last_update_success

    assert coordinator.data.external_temperature == 23.5
