from unittest.mock import AsyncMock

import pytest
from pymyenergi.eddi import Eddi

pytestmark = pytest.mark.asyncio


async def test_refresh(eddi_fetch_data_fixture):
    """Test Zappi data"""
    eddi = Eddi({}, 16042300)
    await eddi.refresh()
    assert eddi.serial_number == 10088800
    assert eddi.consumed_session == 8.2


async def test_boost(eddi_fetch_data_fixture):
    """Test Zappi data"""
    eddi = Eddi(type("", (), {})(), 16042300)
    mock_get = AsyncMock()
    eddi._connection.get = mock_get
    await eddi.manual_boost("Relay 1", 400)
    mock_get.assert_awaited_with("/cgi-eddi-boost-E16042300-10-11-400")
    await eddi.manual_boost("Heater 1", 300)
    mock_get.assert_awaited_with("/cgi-eddi-boost-E16042300-10-1-300")
    await eddi.manual_boost("heater1", 300)
    mock_get.assert_awaited_with("/cgi-eddi-boost-E16042300-10-1-300")
