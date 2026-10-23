from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_SLAVE
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import (
    CONF_REFERENCE_TEMPERATURE_ENTITY,
    DEFAULT_NAME,
    DEFAULT_PORT,
    DEFAULT_SLAVE,
    DOMAIN,
)
from .exceptions import AriosaError
from .modbus_client import AriosaClient

_LOGGER = logging.getLogger(__name__)


# Shared so the config step and the options step can't drift apart on what
# counts as a valid reference entity.
REFERENCE_TEMPERATURE_ENTITY_SELECTOR = selector.EntitySelector(
    selector.EntitySelectorConfig(domain="sensor", device_class="temperature")
)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Optional(CONF_PORT, default=DEFAULT_PORT): int,
        vol.Optional(CONF_SLAVE, default=DEFAULT_SLAVE): int,
        vol.Optional(
            CONF_REFERENCE_TEMPERATURE_ENTITY
        ): REFERENCE_TEMPERATURE_ENTITY_SELECTOR,
    }
)

# Connection settings only; editable via "Reconfigure" (e.g. new IP address).
RECONFIGURE_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_PORT): int,
        vol.Required(CONF_SLAVE): int,
    }
)

# Reused by the options flow both to render the form (with the current
# value pre-filled via add_suggested_values_to_schema) and, implicitly, to
# document what key user_input carries on submit.
OPTIONS_SCHEMA = vol.Schema(
    {
        vol.Optional(
            CONF_REFERENCE_TEMPERATURE_ENTITY
        ): REFERENCE_TEMPERATURE_ENTITY_SELECTOR,
    }
)


async def _async_test_connection(data: dict[str, Any]) -> str | None:
    """Try to read from the device; return an error key, or None on success."""

    client = AriosaClient(
        host=data[CONF_HOST],
        port=data[CONF_PORT],
        slave=data[CONF_SLAVE],
    )

    try:
        await client.connect()
        await client.read_inputs()

    except AriosaError:
        return "cannot_connect"

    except Exception:  # pragma: no cover
        _LOGGER.exception("Unexpected exception")
        return "unknown"

    finally:
        await client.disconnect()

    return None


class AriosaConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow."""

    VERSION = 1

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Handle the initial step."""

        errors: dict[str, str] = {}

        if user_input is not None:
            # The entity selector can submit an empty string when the
            # optional field is left blank; normalize that to "not set".
            # The reference entity is a *setting*, not connection info, so
            # it's split out into options rather than kept in `data` -
            # that's also what makes it editable later via the options
            # flow (Configure) without re-adding the whole device.
            reference_entity_id = (
                user_input.pop(CONF_REFERENCE_TEMPERATURE_ENTITY, None) or None
            )

            await self.async_set_unique_id(user_input[CONF_HOST])
            self._abort_if_unique_id_configured()

            error = await _async_test_connection(user_input)

            if error:
                errors["base"] = error

            else:
                return self.async_create_entry(
                    title=DEFAULT_NAME,
                    data=user_input,
                    options={
                        CONF_REFERENCE_TEMPERATURE_ENTITY: reference_entity_id,
                    }
                    if reference_entity_id
                    else {},
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    async def async_step_reconfigure(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Change the connection settings (e.g. a new IP address).

        Works even while the entry is failing to set up, which is exactly
        when the address usually needs fixing.
        """

        entry = self._get_reconfigure_entry()
        errors: dict[str, str] = {}

        if user_input is not None:
            new_host = user_input[CONF_HOST]

            # The host doubles as the entry's unique id, so refuse to move
            # onto an address another entry already uses.
            if any(
                other.entry_id != entry.entry_id and other.unique_id == new_host
                for other in self._async_current_entries(include_ignore=False)
            ):
                return self.async_abort(reason="already_configured")

            error = await _async_test_connection(user_input)

            if error:
                errors["base"] = error

            else:
                # The entry's update listener reloads it when something
                # changed; only reload by hand if nothing did, so a
                # "reconfigure" with the same values still retries setup.
                changed = self.hass.config_entries.async_update_entry(
                    entry,
                    unique_id=new_host,
                    data={**entry.data, **user_input},
                )

                if not changed:
                    self.hass.config_entries.async_schedule_reload(entry.entry_id)

                return self.async_abort(reason="reconfigure_successful")

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=self.add_suggested_values_to_schema(
                RECONFIGURE_SCHEMA, user_input or entry.data
            ),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> AriosaOptionsFlow:
        """Get the options flow for this handler."""

        return AriosaOptionsFlow()


class AriosaOptionsFlow(OptionsFlow):
    """Handle Ariosa options - settings editable after initial setup.

    `self.config_entry` is provided by the base `OptionsFlow` class; it
    must not be set explicitly here (that pattern is deprecated as of HA
    2024.12 and removed in 2025.12).
    """

    async def async_step_init(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Manage the options."""

        if user_input is not None:
            reference_entity_id = (
                user_input.pop(CONF_REFERENCE_TEMPERATURE_ENTITY, None) or None
            )

            # `title` is unused by the frontend for options entries (unlike
            # config entries, where it names the device) - "" is the
            # standard convention.
            return self.async_create_entry(
                title="",
                data={
                    CONF_REFERENCE_TEMPERATURE_ENTITY: reference_entity_id,
                }
                if reference_entity_id
                else {},
            )

        return self.async_show_form(
            step_id="init",
            data_schema=self.add_suggested_values_to_schema(
                OPTIONS_SCHEMA, self.config_entry.options
            ),
        )
