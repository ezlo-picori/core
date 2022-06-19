"""Platform for invoxia.device_tracker integration."""
from __future__ import annotations

import asyncio
from datetime import timedelta
import uuid

import gps_tracker
from gps_tracker import AsyncClient, Tracker
from gps_tracker.client.datatypes import Tracker01, TrackerStatus

from homeassistant.components.device_tracker.config_entry import TrackerEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ENTITIES
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import ATTRIBUTION, CLIENT, DOMAIN, LOGGER, MDI_ICONS

PARALLEL_UPDATES = 1
SCAN_INTERVAL = timedelta(seconds=240)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the device_tracker platform."""
    client: AsyncClient = hass.data[DOMAIN][entry.entry_id][CLIENT]
    trackers: list[Tracker] = await client.get_trackers()

    entities = [GpsTrackerEntity(client, tracker) for tracker in trackers]
    hass.data[DOMAIN][entry.entry_id][CONF_ENTITIES].extend(entities)
    async_add_entities(entities, update_before_add=True)


class GpsTrackerEntity(TrackerEntity):
    """Class for Invoxia™ GPS tracker devices."""

    _attr_attribution = ATTRIBUTION

    def __init__(self, client: AsyncClient, tracker: Tracker) -> None:
        """Store tracker main properties."""
        super().__init__()

        # Attributes for update logic
        self._client: AsyncClient = client
        self._tracker: Tracker = tracker

        # Static entity attributes
        self._attr_should_poll = True
        if isinstance(tracker, Tracker01):
            self._attr_icon = MDI_ICONS[tracker.tracker_config.icon]
            self._attr_device_info = self._form_device_info(tracker)  # type:ignore
            self._attr_name = self._tracker.name
            self._attr_unique_id = str(self._tracker.id)

        # Dynamic entity attributes
        self._attr_available: bool = True

        # Dynamic tracker-entity attributes
        self._battery: int = 0
        self._accuracy: int = 0
        self._latitude: float = 0.0
        self._longitude: float = 0.0
        self._last_uuid: uuid.UUID = uuid.uuid4()

    async def _update_location(self) -> None:
        """Update tracker location."""
        locations = await self._client.get_locations(self._tracker, max_count=1)
        if locations[0].uuid != self._last_uuid:
            self._latitude = locations[0].lat
            self._longitude = locations[0].lng
            self._accuracy = locations[0].precision

    async def _update_battery(self) -> None:
        """Update tracker battery level."""
        tracker_status: TrackerStatus = await self._client.get_tracker_status(
            self._tracker
        )
        self._battery = tracker_status.battery

    async def async_update(self) -> None:
        """Update tracker data."""
        if not self.enabled:
            return

        try:
            await asyncio.gather(self._update_location(), self._update_battery())
            if not self.available:
                LOGGER.info(
                    "Update of '{self.name}' successful, connection or API errors are resolved"
                )
                self._attr_available = True
        except gps_tracker.client.exceptions.GpsTrackerException:
            LOGGER.warning(
                "Could not update '{self.name}' due to connection or API errors"
            )
            self._attr_available = False

    @property
    def battery_level(self) -> int | None:
        """Return tracker battery level."""
        return self._battery

    @property
    def source_type(self) -> str:
        """Define source type as being GPS."""
        return "gps"

    @property
    def location_accuracy(self) -> int:
        """Return accuration of last location data."""
        return self._accuracy

    @property
    def latitude(self) -> float | None:
        """Return last device latitude."""
        return self._latitude

    @property
    def longitude(self) -> float | None:
        """Return last device longitude."""
        return self._longitude

    @staticmethod
    def _form_device_info(tracker: Tracker01) -> DeviceInfo:
        """Extract device_info from tracker instance."""
        return {
            "hw_version": tracker.tracker_config.board_name,
            "identifiers": {(DOMAIN, tracker.serial)},
            "manufacturer": "Invoxia",
            "name": tracker.name,
            "sw_version": tracker.version,
        }
