"""Test the flume sensor."""

from typing import Any
from unittest.mock import patch

import pytest
from requests_mock.mocker import Mocker
from syrupy.assertion import SnapshotAssertion

from homeassistant.components.flume.const import DOMAIN
from homeassistant.const import STATE_UNAVAILABLE, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.util.unit_system import US_CUSTOMARY_SYSTEM

from .conftest import (
    BRIDGE_DEVICE,
    DEVICE_LIST_URL,
    SENSOR_DEVICE,
    SENSOR_DEVICE_WITHOUT_BATTERY,
)

from tests.common import MockConfigEntry, snapshot_platform


@pytest.fixture(autouse=True)
def platforms_fixture():
    """Return the platforms to be loaded for this test."""
    with patch("homeassistant.components.flume.PLATFORMS", [Platform.SENSOR]):
        yield


@pytest.mark.usefixtures("access_token", "device_list")
async def test_sensors(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    entity_registry: er.EntityRegistry,
    snapshot: SnapshotAssertion,
) -> None:
    """Test sensors."""
    hass.config.units = US_CUSTOMARY_SYSTEM

    flume_values = {
        "current_interval": 1.23,
        "month_to_date": 100.1,
        "week_to_date": 50.5,
        "today": 10.2,
        "last_60_min": 5.5,
        "last_24_hrs": 20.4,
        "last_30_days": 150.8,
    }

    with patch("homeassistant.components.flume.sensor.FlumeData") as mock_flume_data:
        mock_flume_data.return_value.values = flume_values

        assert await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

    await snapshot_platform(hass, entity_registry, snapshot, config_entry.entry_id)


@pytest.mark.usefixtures("access_token")
@pytest.mark.parametrize(
    ("sensor_device", "expected_state"),
    [
        pytest.param({**SENSOR_DEVICE, "battery_level": "low"}, "low", id="low"),
        pytest.param(
            {**SENSOR_DEVICE, "battery_level": "medium"}, "medium", id="medium"
        ),
        pytest.param({**SENSOR_DEVICE, "battery_level": "high"}, "high", id="high"),
        pytest.param(
            {**SENSOR_DEVICE, "battery_level": None}, STATE_UNAVAILABLE, id="null"
        ),
        pytest.param(
            SENSOR_DEVICE_WITHOUT_BATTERY, STATE_UNAVAILABLE, id="not_reported"
        ),
    ],
)
async def test_battery_level(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    entity_registry: er.EntityRegistry,
    requests_mock: Mocker,
    sensor_device: dict[str, Any],
    expected_state: str,
) -> None:
    """Test the battery levels reported by the devices API."""
    requests_mock.get(
        DEVICE_LIST_URL,
        json={"data": [BRIDGE_DEVICE, sensor_device]},
    )

    with patch("homeassistant.components.flume.sensor.FlumeData") as mock_flume_data:
        mock_flume_data.return_value.values = {}

        assert await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

    entity_id = entity_registry.async_get_entity_id(
        Platform.SENSOR, DOMAIN, "battery_level_1234"
    )
    assert entity_id is not None
    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state == expected_state
