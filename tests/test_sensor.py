from unittest.mock import AsyncMock, patch

import pytest
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT

from custom_components.ariosa.const import CONF_REFERENCE_TEMPERATURE_ENTITY, DOMAIN
from custom_components.ariosa.models import AriosaMeasurements
from tests.test_data import SUMMER_MEASUREMENTS


@pytest.fixture
def measurements() -> AriosaMeasurements:
    return SUMMER_MEASUREMENTS


async def test_sensors_created_with_correct_state(hass, measurements):
    with (
        patch("custom_components.ariosa.config_flow.AriosaClient") as client_cls,
        patch("custom_components.ariosa.AriosaClient", new=client_cls),
    ):
        client = client_cls.return_value

        client.connect = AsyncMock()
        client.disconnect = AsyncMock()
        client.read_inputs = AsyncMock(return_value=measurements)
        await hass.async_block_till_done()

        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
        )

        await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: "192.168.1.10",
                CONF_PORT: 502,
            },
        )

        await hass.async_block_till_done()

        expected_states = {
            "sensor.ariosa_ventilation_external_temperature": "32.5",
            "sensor.ariosa_ventilation_external_humidity": "55.2",
            "sensor.ariosa_ventilation_ejection_temperature": "29.4",
            "sensor.ariosa_ventilation_ejection_humidity": "50.1",
            "sensor.ariosa_ventilation_internal_temperature": "24.0",
            "sensor.ariosa_ventilation_internal_humidity": "59.1",
            "sensor.ariosa_ventilation_flow_temperature": "27.9",
            "sensor.ariosa_ventilation_flow_humidity": "55.4",
            "sensor.ariosa_ventilation_motor_1_speed": "1200",
            "sensor.ariosa_ventilation_motor_2_speed": "1190",
            "sensor.ariosa_ventilation_post_treatment": "25",
            "sensor.ariosa_ventilation_machine_days": "100",
            "sensor.ariosa_ventilation_filter_hours": "50",
            "sensor.ariosa_ventilation_supply_side_heat_recovery_efficiency": "166.7",
            "sensor.ariosa_ventilation_exhaust_side_heat_recovery_efficiency": "-133.3",
            "sensor.ariosa_ventilation_heat_recovery_efficiency_imbalance": "300.0",
        }

        for entity_id, expected_state in expected_states.items():
            state = hass.states.get(entity_id)
            assert state is not None, f"{entity_id} was not created"
            assert state.state == expected_state


async def test_temperature_waste_sensor_not_created_without_reference(
    hass, measurements
):
    """No reference entity configured -> no waste sensor at all."""

    with (
        patch("custom_components.ariosa.config_flow.AriosaClient") as client_cls,
        patch("custom_components.ariosa.AriosaClient", new=client_cls),
    ):
        client = client_cls.return_value

        client.connect = AsyncMock()
        client.disconnect = AsyncMock()
        client.read_inputs = AsyncMock(return_value=measurements)
        await hass.async_block_till_done()

        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
        )

        await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: "192.168.1.10",
                CONF_PORT: 502,
            },
        )

        await hass.async_block_till_done()

        assert (
            hass.states.get("sensor.ariosa_ventilation_temperature_waste_vs_reference")
            is None
        )


async def test_temperature_waste_sensor_tracks_reference_entity(hass, measurements):
    """internal_temperature=24.0; reference=23.5 -> waste == 0.5."""

    hass.states.async_set("sensor.room_reference", "23.5")
    await hass.async_block_till_done()

    with (
        patch("custom_components.ariosa.config_flow.AriosaClient") as client_cls,
        patch("custom_components.ariosa.AriosaClient", new=client_cls),
    ):
        client = client_cls.return_value

        client.connect = AsyncMock()
        client.disconnect = AsyncMock()
        client.read_inputs = AsyncMock(return_value=measurements)
        await hass.async_block_till_done()

        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
        )

        await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: "192.168.1.10",
                CONF_PORT: 502,
                CONF_REFERENCE_TEMPERATURE_ENTITY: "sensor.room_reference",
            },
        )

        await hass.async_block_till_done()

        entity_id = "sensor.ariosa_ventilation_temperature_waste_vs_reference"
        state = hass.states.get(entity_id)
        assert state is not None
        assert state.state == "0.5"

        # Moving the reference should update the waste sensor immediately,
        # without waiting for the next coordinator poll.
        hass.states.async_set("sensor.room_reference", "20.0")
        await hass.async_block_till_done()

        assert hass.states.get(entity_id).state == "4.0"

        # An unavailable/unknown reference should yield an unknown state,
        # not a crash.
        hass.states.async_set("sensor.room_reference", "unavailable")
        await hass.async_block_till_done()

        assert hass.states.get(entity_id).state == "unknown"
