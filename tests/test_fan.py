from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_SLAVE
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.ariosa.const import CONF_ENABLE_CONTROL, DOMAIN
from custom_components.ariosa.exceptions import WriteError
from tests.test_data import SUMMER_MEASUREMENTS

ENTITY_ID = "fan.ariosa_ventilation_fan_mode"


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


async def test_fan_not_created_when_control_disabled(hass):
    with patch("custom_components.ariosa.AriosaClient") as client_cls:
        await _setup(hass, _entry(control=False), client_cls)

    assert hass.states.get(ENTITY_ID) is None


@pytest.mark.parametrize(
    ("raw", "state", "percentage"),
    [(0, "off", 0), (1, "on", 25), (2, "on", 50), (3, "on", 75), (4, "on", 100)],
)
async def test_fan_state_and_percentage(hass, raw, state, percentage):
    with patch("custom_components.ariosa.AriosaClient") as client_cls:
        await _setup(hass, _entry(control=True), client_cls, fan_mode=raw)

    fan = hass.states.get(ENTITY_ID)

    assert fan.state == state
    assert fan.attributes["percentage"] == percentage
    assert fan.attributes["percentage_step"] == 25
    assert fan.attributes["preset_modes"] == [
        "night",
        "level_1",
        "level_2",
        "level_3",
    ]


async def test_fan_unknown_when_mode_unreadable(hass):
    with patch("custom_components.ariosa.AriosaClient") as client_cls:
        await _setup(hass, _entry(control=True), client_cls, fan_mode=None)

    assert hass.states.get(ENTITY_ID).state == "unknown"


@pytest.mark.parametrize(
    ("percentage", "value"),
    [(25, 1), (50, 2), (75, 3), (100, 4), (0, 0)],
)
async def test_set_percentage_writes_register_value(hass, percentage, value):
    with patch("custom_components.ariosa.AriosaClient") as client_cls:
        client = await _setup(hass, _entry(control=True), client_cls, fan_mode=1)

        await hass.services.async_call(
            "fan",
            "set_percentage",
            {"entity_id": ENTITY_ID, "percentage": percentage},
            blocking=True,
        )

    client.write_fan_mode.assert_awaited_once_with(value)


@pytest.mark.parametrize(
    ("preset", "value"),
    [("night", 1), ("level_1", 2), ("level_2", 3), ("level_3", 4)],
)
async def test_set_preset_mode_writes_register_value(hass, preset, value):
    with patch("custom_components.ariosa.AriosaClient") as client_cls:
        client = await _setup(hass, _entry(control=True), client_cls, fan_mode=0)

        await hass.services.async_call(
            "fan",
            "set_preset_mode",
            {"entity_id": ENTITY_ID, "preset_mode": preset},
            blocking=True,
        )

    client.write_fan_mode.assert_awaited_once_with(value)
    assert hass.states.get(ENTITY_ID).attributes["preset_mode"] == preset


async def test_preset_mode_follows_the_unit(hass):
    with patch("custom_components.ariosa.AriosaClient") as client_cls:
        await _setup(hass, _entry(control=True), client_cls, fan_mode=1)

    assert hass.states.get(ENTITY_ID).attributes["preset_mode"] == "night"


async def test_preset_mode_is_none_when_off(hass):
    with patch("custom_components.ariosa.AriosaClient") as client_cls:
        await _setup(hass, _entry(control=True), client_cls, fan_mode=0)

    assert hass.states.get(ENTITY_ID).attributes["preset_mode"] is None


async def test_turn_off_writes_zero(hass):
    with patch("custom_components.ariosa.AriosaClient") as client_cls:
        client = await _setup(hass, _entry(control=True), client_cls, fan_mode=3)

        await hass.services.async_call(
            "fan", "turn_off", {"entity_id": ENTITY_ID}, blocking=True
        )

    client.write_fan_mode.assert_awaited_once_with(0)
    assert hass.states.get(ENTITY_ID).state == "off"


async def test_turn_on_defaults_to_level_1(hass):
    with patch("custom_components.ariosa.AriosaClient") as client_cls:
        client = await _setup(hass, _entry(control=True), client_cls, fan_mode=0)

        await hass.services.async_call(
            "fan", "turn_on", {"entity_id": ENTITY_ID}, blocking=True
        )

    client.write_fan_mode.assert_awaited_once_with(2)
    assert hass.states.get(ENTITY_ID).attributes["percentage"] == 50


async def test_write_failure_is_reported(hass):
    with patch("custom_components.ariosa.AriosaClient") as client_cls:
        client = await _setup(hass, _entry(control=True), client_cls, fan_mode=1)
        client.write_fan_mode.side_effect = WriteError

        with pytest.raises(HomeAssistantError):
            await hass.services.async_call(
                "fan",
                "set_percentage",
                {"entity_id": ENTITY_ID, "percentage": 75},
                blocking=True,
            )

    assert hass.states.get(ENTITY_ID).attributes["percentage"] == 25


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


async def test_legacy_select_entity_is_removed(hass):
    """Setups that already have the earlier select entity get it cleaned up."""

    entry = _entry(control=True)
    entry.add_to_hass(hass)

    registry = er.async_get(hass)
    legacy = registry.async_get_or_create(
        "select",
        DOMAIN,
        f"{entry.entry_id}_fan_mode",
        config_entry=entry,
    )

    with patch("custom_components.ariosa.AriosaClient") as client_cls:
        await _setup(hass, entry, client_cls)

    assert registry.async_get(legacy.entity_id) is None
    assert hass.states.get(ENTITY_ID) is not None
