from unittest.mock import AsyncMock
from unittest.mock import patch

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT

from custom_components.ariosa.const import DOMAIN


async def test_config_flow_success(hass):
    with (
        patch("custom_components.ariosa.config_flow.AriosaClient") as client_cls,
        patch("custom_components.ariosa.AriosaClient", new=client_cls),
    ):
        client = client_cls.return_value

        client.connect = AsyncMock()
        client.disconnect = AsyncMock()
        client.read_inputs = AsyncMock()
        await hass.async_block_till_done()

        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
        )

        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: "192.168.1.10",
                CONF_PORT: 502,
            },
        )

        assert result2["type"] == "create_entry"

        await hass.async_block_till_done()


async def test_options_flow_sets_reference_entity(hass):
    """The reference temperature entity can be set after initial setup,
    via the options flow (the "Configure" button), and doing so reloads
    the entry.
    """

    hass.states.async_set("sensor.room_reference", "20.0")
    await hass.async_block_till_done()

    with (
        patch("custom_components.ariosa.config_flow.AriosaClient") as client_cls,
        patch("custom_components.ariosa.AriosaClient", new=client_cls),
    ):
        client = client_cls.return_value

        client.connect = AsyncMock()
        client.disconnect = AsyncMock()
        client.read_inputs = AsyncMock()
        await hass.async_block_till_done()

        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
        )

        # Set up without a reference entity - simulates an existing entry.
        await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: "192.168.1.10",
                CONF_PORT: 502,
            },
        )

        await hass.async_block_till_done()

        entry = hass.config_entries.async_entries(DOMAIN)[0]
        assert entry.options == {}
        assert (
            hass.states.get("sensor.ariosa_ventilation_temperature_waste_vs_reference")
            is None
        )

        options_result = await hass.config_entries.options.async_init(entry.entry_id)

        options_result2 = await hass.config_entries.options.async_configure(
            options_result["flow_id"],
            {"reference_temperature_entity": "sensor.room_reference"},
        )

        assert options_result2["type"] == "create_entry"

        await hass.async_block_till_done()

        assert entry.options == {
            "reference_temperature_entity": "sensor.room_reference"
        }
        assert (
            hass.states.get("sensor.ariosa_ventilation_temperature_waste_vs_reference")
            is not None
        )
