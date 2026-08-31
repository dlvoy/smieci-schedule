"""Config flow for smieci_wroclaw.

Step 1 (user): base URL + PAT, validated against GET /api/ha/v1/health before the entry is
created. Options flow manages the repeatable list of notification targets (notify entity, time,
which events, which fractions) — see const.py for the stored shape.
"""

from __future__ import annotations

import uuid
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers import selector

from .api import SmieciApiError, SmieciAuthError, SmieciClient
from .const import (
    CONF_BASE_URL,
    CONF_TOKEN,
    DEFAULT_BASE_URL,
    DOMAIN,
    EVENT_CHOICES,
    EVENT_LABELS_PL,
    FRACTIONS,
    OPT_TARGETS,
    TARGET_ENABLED,
    TARGET_EVENTS,
    TARGET_FRACTIONS,
    TARGET_HOUR,
    TARGET_ID,
    TARGET_MINUTE,
    TARGET_NOTIFY_SERVICE,
)

STEP_USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_BASE_URL, default=DEFAULT_BASE_URL): str,
        vol.Required(CONF_TOKEN): str,
    }
)


class SmieciConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle the initial setup."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        errors: dict[str, str] = {}

        if user_input is not None:
            base_url = user_input[CONF_BASE_URL].rstrip("/")
            token = user_input[CONF_TOKEN]

            session = async_get_clientsession(self.hass)
            client = SmieciClient(session, base_url, token)
            try:
                await client.get_health()
            except SmieciAuthError:
                errors["base"] = "invalid_auth"
            except SmieciApiError:
                errors["base"] = "cannot_connect"
            else:
                await self.async_set_unique_id(base_url)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title="Harmonogram odpadow",
                    data={CONF_BASE_URL: base_url, CONF_TOKEN: token},
                )

        return self.async_show_form(step_id="user", data_schema=STEP_USER_SCHEMA, errors=errors)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry) -> SmieciOptionsFlow:
        return SmieciOptionsFlow(config_entry)


class SmieciOptionsFlow(config_entries.OptionsFlow):
    """Manage the list of notification targets."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self._entry = config_entry
        self._editing_id: str | None = None

    def _targets(self) -> list[dict[str, Any]]:
        return list(self._entry.options.get(OPT_TARGETS, []))

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        return self.async_show_menu(
            step_id="init",
            menu_options=["add_target", "remove_target"] if self._targets() else ["add_target"],
        )

    async def async_step_add_target(self, user_input: dict[str, Any] | None = None):
        errors: dict[str, str] = {}

        if user_input is not None:
            targets = self._targets()
            targets.append(
                {
                    TARGET_ID: str(uuid.uuid4()),
                    TARGET_NOTIFY_SERVICE: user_input[TARGET_NOTIFY_SERVICE],
                    TARGET_HOUR: user_input[TARGET_HOUR],
                    TARGET_MINUTE: user_input[TARGET_MINUTE],
                    TARGET_EVENTS: user_input[TARGET_EVENTS],
                    TARGET_FRACTIONS: user_input.get(TARGET_FRACTIONS, []),
                    TARGET_ENABLED: user_input[TARGET_ENABLED],
                }
            )
            return self.async_create_entry(title="", data={OPT_TARGETS: targets})

        schema = vol.Schema(
            {
                vol.Required(TARGET_NOTIFY_SERVICE): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="notify")
                ),
                vol.Required(TARGET_HOUR, default=19): vol.All(vol.Coerce(int), vol.Range(min=0, max=23)),
                vol.Required(TARGET_MINUTE, default=0): vol.All(vol.Coerce(int), vol.Range(min=0, max=59)),
                vol.Required(TARGET_EVENTS, default=EVENT_CHOICES): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[
                            selector.SelectOptionDict(value=v, label=EVENT_LABELS_PL[v])
                            for v in EVENT_CHOICES
                        ],
                        multiple=True,
                        mode=selector.SelectSelectorMode.LIST,
                    )
                ),
                vol.Optional(TARGET_FRACTIONS, default=[]): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[
                            selector.SelectOptionDict(value=f["key"], label=f["label_pl"])
                            for f in FRACTIONS
                        ],
                        multiple=True,
                        mode=selector.SelectSelectorMode.LIST,
                    )
                ),
                vol.Required(TARGET_ENABLED, default=True): selector.BooleanSelector(),
            }
        )
        return self.async_show_form(step_id="add_target", data_schema=schema, errors=errors)

    async def async_step_remove_target(self, user_input: dict[str, Any] | None = None):
        targets = self._targets()

        if user_input is not None:
            remaining = [t for t in targets if t[TARGET_ID] != user_input["target_id"]]
            return self.async_create_entry(title="", data={OPT_TARGETS: remaining})

        def describe(t: dict[str, Any]) -> str:
            fractions = t.get(TARGET_FRACTIONS) or []
            fraction_label = "wszystkie frakcje" if not fractions else ", ".join(fractions)
            return (
                f"{t[TARGET_NOTIFY_SERVICE]} o {t[TARGET_HOUR]:02d}:{t[TARGET_MINUTE]:02d} "
                f"({', '.join(t[TARGET_EVENTS])}, {fraction_label})"
                f"{'' if t[TARGET_ENABLED] else ' [wylaczony]'}"
            )

        schema = vol.Schema(
            {
                vol.Required("target_id"): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[
                            selector.SelectOptionDict(value=t[TARGET_ID], label=describe(t))
                            for t in targets
                        ],
                        mode=selector.SelectSelectorMode.LIST,
                    )
                ),
            }
        )
        return self.async_show_form(step_id="remove_target", data_schema=schema)
