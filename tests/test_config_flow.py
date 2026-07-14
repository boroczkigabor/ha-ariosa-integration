from unittest.mock import AsyncMock
from unittest.mock import patch

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT

from custom_components.ariosa.const import DOMAIN


async def test_config_flow_success(hass):
    with patch("custom_components.ariosa.config_flow.AriosaClient") as client_cls:
        client = client_cls.return_value

        client.connect = AsyncMock()
        client.disconnect = AsyncMock()
        client.read_inputs = AsyncMock()

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
