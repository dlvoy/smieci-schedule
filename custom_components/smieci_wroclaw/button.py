"""Button entity: force a refresh via POST /api/ha/v1/refresh, then re-poll the coordinator."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api import SmieciApiError
from .const import DOMAIN
from .entity import SmieciEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    data = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([RefreshButton(data["coordinator"], entry.entry_id, data["client"])])


class RefreshButton(SmieciEntity, ButtonEntity):
    _attr_name = "Odswiez harmonogram"
    _attr_entity_category = "config"

    def __init__(self, coordinator, entry_id: str, client) -> None:
        super().__init__(coordinator, entry_id)
        self._client = client
        self._attr_unique_id = f"{entry_id}_refresh"

    async def async_press(self) -> None:
        try:
            await self._client.refresh()
        except SmieciApiError:
            # The refresh call itself may 429/502 if a check just ran or Splash is down — either
            # way, still re-poll so the button reflects whatever the server's current state is.
            pass
        await self.coordinator.async_request_refresh()
