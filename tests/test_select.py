from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_SLAVE
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.ariosa.const import CONF_ENABLE_CONTROL, DOMAIN
from custom_components.ariosa.exceptions import WriteError
from tests.test_data import SUMMER_MEASUREMENTS

ENTITY_ID = "select.ariosa_ventilation_fan_mode"


def _entry(*, control: bool) -> MockConfigEntry:
    return MockConfigEntry(
        domain=DOMAIN,
        title="Ariosa Ventilation",
        data={CONF_HOST: "192.168.1.10", CONF_PORT: 502, CONF_SLAVE: 1},
        options={CONF_ENABLE_CONTROL: True} if control else {},
    )


async def _setup(hass, entry, client_cls, fan_mode: int | None = 2):
    client = client_cls.return_value
    client.connect = AsyncMock()
    client.disconnect = AsyncMock()
    client.read_inputs = AsyncMock(return_value=SUMMER_MEASUREMENTS)
    client.read_fan_mode = AsyncMock(return_value=fan_mode)
    client.write_fan_mode = AsyncMock()

    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    return client


async def test_select_not_created_when_control_disabled(hass):
    with patch("custom_components.ariosa.AriosaClient") as client_cls:
        await _setup(hass, _entry(control=False), client_cls)

    assert hass.states.get(ENTITY_ID) is None


async def test_select_shows_current_mode(hass):
    with patch("custom_components.ariosa.AriosaClient") as client_cls:
        await _setup(hass, _entry(control=True), client_cls, fan_mode=2)

    state = hass.states.get(ENTITY_ID)

    assert state is not None
    assert state.state == "level_1"
    assert state.attributes["options"] == [
        "off",
        "night",
        "level_1",
        "level_2",
        "level_3",
    ]


async def test_select_unknown_when_mode_unreadable(hass):
    with patch("custom_components.ariosa.AriosaClient") as client_cls:
        await _setup(hass, _entry(control=True), client_cls, fan_mode=None)

    assert hass.states.get(ENTITY_ID).state == "unknown"


@pytest.mark.parametrize(
    ("option", "value"),
    [("off", 0), ("night", 1), ("level_1", 2), ("level_2", 3), ("level_3", 4)],
)
async def test_select_option_writes_register_value(hass, option, value):
    with patch("custom_components.ariosa.AriosaClient") as client_cls:
        client = await _setup(hass, _entry(control=True), client_cls, fan_mode=1)

        await hass.services.async_call(
            "select",
            "select_option",
            {"entity_id": ENTITY_ID, "option": option},
            blocking=True,
        )

    client.write_fan_mode.assert_awaited_once_with(value)
    assert hass.states.get(ENTITY_ID).state == option


async def test_select_option_failure_is_reported(hass):
    with patch("custom_components.ariosa.AriosaClient") as client_cls:
        client = await _setup(hass, _entry(control=True), client_cls, fan_mode=1)
        client.write_fan_mode.side_effect = WriteError

        with pytest.raises(HomeAssistantError):
            await hass.services.async_call(
                "select",
                "select_option",
                {"entity_id": ENTITY_ID, "option": "level_2"},
                blocking=True,
            )

    assert hass.states.get(ENTITY_ID).state == "night"


async def test_disabling_control_removes_the_entity(hass):
    entry = _entry(control=True)

    with patch("custom_components.ariosa.AriosaClient") as client_cls:
        await _setup(hass, entry, client_cls)

        registry = er.async_get(hass)
        assert registry.async_get(ENTITY_ID) is not None

        hass.config_entries.async_update_entry(entry, options={})
        await hass.async_block_till_done()

    assert registry.async_get(ENTITY_ID) is None
    assert hass.states.get(ENTITY_ID) is None
