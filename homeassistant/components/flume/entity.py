"""Platform for shared base classes for sensors."""

from typing import override

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityDescription
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import (
    FlumeDeviceDataUpdateCoordinator,
    FlumeDeviceStatusUpdateCoordinator,
    FlumeNotificationDataUpdateCoordinator,
)


class FlumeEntity[
    _FlumeCoordinatorT: FlumeDeviceDataUpdateCoordinator
    | FlumeDeviceStatusUpdateCoordinator
    | FlumeNotificationDataUpdateCoordinator
](CoordinatorEntity[_FlumeCoordinatorT]):
    """Base entity class."""

    _attr_attribution = "Data provided by Flume API"
    _attr_has_entity_name = True
    _refresh_on_add = True

    def __init__(
        self,
        coordinator: _FlumeCoordinatorT,
        description: EntityDescription,
        device_id: str,
        location_name: str,
        is_bridge: bool = False,
    ) -> None:
        """Class initializer."""
        super().__init__(coordinator)
        self.entity_description = description
        self.device_id = device_id

        if is_bridge:
            name = "Flume Bridge"
        else:
            name = "Flume Sensor"

        self._attr_unique_id = f"{description.key}_{device_id}"

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device_id)},
            manufacturer="Flume, Inc.",
            model="Flume Smart Water Monitor",
            name=f"{name} {location_name}",
            configuration_url="https://portal.flumewater.com",
        )

    @override
    async def async_added_to_hass(self) -> None:
        """Request an update when added."""
        await super().async_added_to_hass()
        if self._refresh_on_add:
            # We do not ask for an update with async_add_entities()
            # because it will update disabled entities
            await self.coordinator.async_request_refresh()


class FlumeDeviceStatusEntity(FlumeEntity[FlumeDeviceStatusUpdateCoordinator]):
    """Base class for entities backed by the device status coordinator."""

    # Config entry setup already performed this coordinator's first refresh.
    _refresh_on_add = False


class FlumeBatteryEntity(FlumeDeviceStatusEntity):
    """Base class for entities backed by the device battery level."""

    @property
    def battery_level(self) -> str | None:
        """Return the reported battery level."""
        return self.coordinator.battery_levels.get(self.device_id)

    @property
    @override
    def available(self) -> bool:
        """Return whether the device reports a battery level."""
        return super().available and self.battery_level is not None
