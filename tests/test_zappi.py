import pytest

from pymyenergi.zappi import Zappi

pytestmark = pytest.mark.asyncio


async def test_refresh(zappi_fetch_data_fixture, zappi_fetch_boost_data_fixture):
    """Test Zappi data"""
    zappi = Zappi({}, 16042300)
    await zappi.refresh()
    assert zappi.serial_number == 16042300
    assert zappi.charge_mode == "Fast"
    assert zappi.charge_added == 4.2


async def test_power_charging(zappi_fetch_data_fixture, zappi_fetch_boost_data_fixture):
    """Test that power_charging sums only Internal Load CTs"""
    zappi = Zappi({}, 16042300)
    await zappi.refresh()
    assert zappi.power_charging == 800 + 750 + 700  # ct1 + ct2 + ct3
