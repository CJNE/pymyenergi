import pytest
from pymyenergi.harvi import Harvi

pytestmark = pytest.mark.asyncio


async def test_refresh(harvi_fetch_data_fixture):
    """Test Harvi data"""
    harvi = Harvi({}, 10645200)
    await harvi.refresh()
    assert harvi.serial_number == 10645200
