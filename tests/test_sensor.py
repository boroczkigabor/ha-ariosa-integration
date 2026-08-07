from unittest.mock import AsyncMock
from unittest.mock import patch

import pytest

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT

from custom_components.ariosa.const import CONF_REFERENCE_TEMPERATURE_ENTITY, DOMAIN
from custom_components.ariosa.models import AriosaMeasurements


@pytest.fixture
def measurements() -> AriosaMeasurements:
    return AriosaMeasurements(
        external_temperature=23.5,
        external_humidity=65.4,
        ejection_temperature=20.0,
        ejection_humidity=40.0,
        internal_temperature=22.0,
        internal_humidity=45.0,
        flow_temperature=21.0,
        flow_humidity=44.0,
        motor_1_rpm=1200,
        motor_2_rpm=1190,
        post_treatment=25,
        machine_days=365,
        filter_hours=123,
    )


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
            "sensor.ariosa_ventilation_external_temperature": "23.5",
            "sensor.ariosa_ventilation_external_humidity": "65.4",
            "sensor.ariosa_ventilation_ejection_temperature": "20.0",
            "sensor.ariosa_ventilation_ejection_humidity": "40.0",
            "sensor.ariosa_ventilation_internal_temperature": "22.0",
            "sensor.ariosa_ventilation_internal_humidity": "45.0",
            "sensor.ariosa_ventilation_flow_temperature": "21.0",
            "sensor.ariosa_ventilation_flow_humidity": "44.0",
            "sensor.ariosa_ventilation_motor_1_speed": "1200",
            "sensor.ariosa_ventilation_motor_2_speed": "1190",
            "sensor.ariosa_ventilation_post_treatment": "25",
            "sensor.ariosa_ventilation_machine_days": "365",
            "sensor.ariosa_ventilation_filter_hours": "123",
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
    """internal_temperature=22.0; reference=18.5 -> waste == 3.5."""

    hass.states.async_set("sensor.room_reference", "18.5")
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
        assert state.state == "3.5"

        # Moving the reference should update the waste sensor immediately,
        # without waiting for the next coordinator poll.
        hass.states.async_set("sensor.room_reference", "20.0")
        await hass.async_block_till_done()

        assert hass.states.get(entity_id).state == "2.0"

        # An unavailable/unknown reference should yield an unknown state,
        # not a crash.
        hass.states.async_set("sensor.room_reference", "unavailable")
        await hass.async_block_till_done()

        assert hass.states.get(entity_id).state == "unknown"
