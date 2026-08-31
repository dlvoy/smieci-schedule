"""DataUpdateCoordinator polling GET /api/ha/v1/schedule."""

from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import SmieciApiError, SmieciClient
from .const import UPDATE_INTERVAL_MINUTES

_LOGGER = logging.getLogger(__name__)


class SmieciCoordinator(DataUpdateCoordinator[dict]):
    """Fetches /api/ha/v1/schedule on a fixed interval.

    Status (unknown/scheduled/tomorrow/today) is computed server-side by smieci.example.com in
    Europe/Warsaw, not recomputed here — this keeps the website and Home Assistant from ever
    disagreeing about "is it today" around midnight.
    """

    def __init__(self, hass: HomeAssistant, client: SmieciClient) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name="smieci_wroclaw",
            update_interval=timedelta(minutes=UPDATE_INTERVAL_MINUTES),
        )
        self.client = client

    async def _async_update_data(self) -> dict:
        try:
            return await self.client.get_schedule()
        except SmieciApiError as err:
            raise UpdateFailed(str(err)) from err
