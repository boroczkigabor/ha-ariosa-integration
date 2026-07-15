from unittest.mock import AsyncMock

from homeassistant.const import CONF_HOST, CONF_PORT
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.ariosa.const import DOMAIN
from custom_components.ariosa.coordinator import AriosaDataUpdateCoordinator
from custom_components.ariosa.diagnostics import async_get_config_entry_diagnostics
from custom_components.ariosa.models import AriosaMeasurements


async def test_diagnostics(hass):
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

    coordinator = AriosaDataUpdateCoordinator(hass, client)
    await coordinator.async_refresh()

    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: "192.168.1.10", CONF_PORT: 502},
    )
    entry.add_to_hass(hass)

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    diagnostics = await async_get_config_entry_diagnostics(hass, entry)

    assert diagnostics["entry_data"] == {CONF_HOST: "192.168.1.10", CONF_PORT: 502}
    assert diagnostics["last_update_success"] is True
    assert diagnostics["measurements"]["external_temperature"] == 23.5
    assert diagnostics["measurements"]["filter_hours"] == 250
