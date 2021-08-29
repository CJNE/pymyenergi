import pytest
from pymyenergi.zappi import Zappi

pytestmark = pytest.mark.asyncio

conn = {}


async def test_refresh(zappi_fetch_data_fixture):
    """Test Zappi data"""
    zappi = Zappi(conn, 16042300)
    await zappi.refresh()
    assert zappi.serial_number == 16042300
    assert zappi.charge_mode == "Fast"
    assert zappi.charge_added == 4.2
