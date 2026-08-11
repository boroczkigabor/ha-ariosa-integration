from dataclasses import replace
from unittest.mock import AsyncMock, patch

import pytest
from homeassistant import config_entries
from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.const import CONF_HOST, CONF_PORT, EntityCategory
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.ariosa.binary_sensor import (
    BINARY_SENSOR_DESCRIPTIONS,
    AriosaBinarySensor,
)
from custom_components.ariosa.const import DOMAIN
from custom_components.ariosa.coordinator import AriosaDataUpdateCoordinator
from custom_components.ariosa.models import AriosaMeasurements
from tests.test_data import (
    BYPASS_MEASUREMENTS,
    SUMMER_MEASUREMENTS,
    WINTER_MEASUREMENTS,
)

# Entity IDs are derived from each entity's *translated name* (in
# translations/en.json), not its description key - kept explicit here
# rather than derived from the key at test time, so a translation edit
# that changes an entity_id shows up as a clear, intentional diff
# instead of a confusing failure.
ALARM_ENTITY_IDS: dict[str, str] = {
    "general_alarm": "binary_sensor.ariosa_ventilation_general_alarm",
    "filter_change_alarm": "binary_sensor.ariosa_ventilation_filter_change_alarm",
    "filter_clogged_alarm": "binary_sensor.ariosa_ventilation_filter_clogged_alarm",
    "frost_protection_alarm": "binary_sensor.ariosa_ventilation_frost_protection_alarm",
    "connection_alarm": "binary_sensor.ariosa_ventilation_connection_alarm",
    "motor_alarm": "binary_sensor.ariosa_ventilation_motor_alarm",
    "sensor_alarm": "binary_sensor.ariosa_ventilation_sensor_alarm",
    "motor_protection_alarm": "binary_sensor.ariosa_ventilation_motor_protection_alarm",
    "pre_heater_alarm": "binary_sensor.ariosa_ventilation_preheater_alarm",
}

PRE_HEATER_STATUS_ENTITY_ID = "binary_sensor.ariosa_ventilation_preheater_status"
BYPASS_ACTIVE_ENTITY_ID = "binary_sensor.ariosa_ventilation_bypass_active"


async def _setup_entry(hass, measurements: AriosaMeasurements) -> None:
    """Configure the integration with the given measurements and let the
    first refresh + entity creation settle.
    """

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


def _assert_state(hass, entity_id: str, expected: str) -> None:
    state = hass.states.get(entity_id)
    assert state is not None, f"{entity_id} was not created"
    assert state.state == expected, (
        f"{entity_id} expected '{expected}', got '{state.state}'"
    )


@pytest.mark.parametrize(
    ("measurements", "expected_pre_heater", "expected_bypass"),
    [
        (WINTER_MEASUREMENTS, "on", "off"),
        (BYPASS_MEASUREMENTS, "off", "on"),
    ],
)
async def test_pre_heater_and_bypass_states(
    hass, measurements, expected_pre_heater, expected_bypass
):
    """Both non-alarm binary sensors reflect their own register
    independently of one another.
    """

    await _setup_entry(hass, measurements)

    _assert_state(hass, PRE_HEATER_STATUS_ENTITY_ID, expected_pre_heater)
    _assert_state(hass, BYPASS_ACTIVE_ENTITY_ID, expected_bypass)


async def test_all_alarms_off_by_default(hass):
    """None of the sample fixtures trip an alarm - every alarm sensor
    should read 'off'.
    """

    await _setup_entry(hass, SUMMER_MEASUREMENTS)

    for entity_id in ALARM_ENTITY_IDS.values():
        _assert_state(hass, entity_id, "off")


@pytest.mark.parametrize(("field", "entity_id"), list(ALARM_ENTITY_IDS.items()))
async def test_each_alarm_turns_on_independently(hass, field, entity_id):
    """Flipping one alarm field turns on exactly that alarm's entity and
    no other - a regression test against copy-paste mistakes where one
    entity's value_fn accidentally reads a different field.
    """

    measurements = replace(SUMMER_MEASUREMENTS, **{field: True})

    await _setup_entry(hass, measurements)

    for other_field, other_entity_id in ALARM_ENTITY_IDS.items():
        expected = "on" if other_field == field else "off"
        _assert_state(hass, other_entity_id, expected)


async def test_alarm_sensors_are_problem_class_and_diagnostic(hass):
    """Regression test: the alarm entity description's `device_class`
    and `entity_category` fields must carry real type annotations to
    take effect (an unannotated class-body assignment is silently
    ignored by @dataclass and the inherited default - None - wins
    instead). This is also what groups every alarm together in its own
    "Diagnostic" section on the device card, separate from the primary
    sensors.
    """

    await _setup_entry(hass, SUMMER_MEASUREMENTS)

    registry = er.async_get(hass)

    for entity_id in ALARM_ENTITY_IDS.values():
        state = hass.states.get(entity_id)
        assert state is not None, f"{entity_id} was not created"
        assert state.attributes.get("device_class") == BinarySensorDeviceClass.PROBLEM

        entry = registry.async_get(entity_id)
        assert entry is not None, f"{entity_id} missing from entity registry"
        assert entry.entity_category is EntityCategory.DIAGNOSTIC


async def test_non_alarm_sensors_are_not_diagnostic(hass):
    """Preheater/bypass are primary operational state, not diagnostics -
    they shouldn't get swept into the alarms' Diagnostic grouping.
    """

    await _setup_entry(hass, WINTER_MEASUREMENTS)

    registry = er.async_get(hass)

    pre_heater_entry = registry.async_get(PRE_HEATER_STATUS_ENTITY_ID)
    assert pre_heater_entry is not None
    assert pre_heater_entry.entity_category is None

    bypass_entry = registry.async_get(BYPASS_ACTIVE_ENTITY_ID)
    assert bypass_entry is not None
    assert bypass_entry.entity_category is None

    assert (
        hass.states.get(PRE_HEATER_STATUS_ENTITY_ID).attributes.get("device_class")
        == BinarySensorDeviceClass.POWER
    )
    assert (
        hass.states.get(BYPASS_ACTIVE_ENTITY_ID).attributes.get("device_class")
        == BinarySensorDeviceClass.OPENING
    )


async def test_unique_ids_are_scoped_to_the_config_entry(hass):
    """Every binary sensor's unique_id is `<entry_id>_<description key>`,
    so multiple ventilation units never collide with each other.
    """

    await _setup_entry(hass, SUMMER_MEASUREMENTS)

    registry = er.async_get(hass)
    entry = next(iter(hass.config_entries.async_entries(DOMAIN)))

    all_entity_ids = [
        PRE_HEATER_STATUS_ENTITY_ID,
        BYPASS_ACTIVE_ENTITY_ID,
        *ALARM_ENTITY_IDS.values(),
    ]

    seen_unique_ids: set[str] = set()

    for entity_id in all_entity_ids:
        registry_entry = registry.async_get(entity_id)
        assert registry_entry is not None, f"{entity_id} missing from registry"
        assert registry_entry.unique_id.startswith(f"{entry.entry_id}_")
        assert registry_entry.unique_id not in seen_unique_ids, (
            f"duplicate unique_id: {registry_entry.unique_id}"
        )
        seen_unique_ids.add(registry_entry.unique_id)

    assert len(seen_unique_ids) == len(all_entity_ids)


async def test_binary_sensor_is_on_returns_none_without_coordinator_data(hass):
    """If the coordinator hasn't successfully fetched data yet (e.g. the
    very first update failed), `is_on` should report None ('unknown')
    rather than crashing or defaulting to a specific state - checked
    directly against the entity class rather than through the full setup
    flow, since driving a genuinely-never-refreshed coordinator through
    the public config-entry API is awkward to arrange reliably.
    """

    client = AsyncMock()
    coordinator = AriosaDataUpdateCoordinator(hass, client)
    # Deliberately never refreshed - coordinator.data stays None.

    entry = MockConfigEntry(domain=DOMAIN, data={CONF_HOST: "192.168.1.10"})
    entry.add_to_hass(hass)

    description = BINARY_SENSOR_DESCRIPTIONS[0]
    entity = AriosaBinarySensor(coordinator, entry, description)

    assert entity.is_on is None
