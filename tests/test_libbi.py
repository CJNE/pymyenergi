import pytest
from pymyenergi.libbi import Libbi

pytestmark = pytest.mark.asyncio


async def test_refresh(libbi_fetch_data_fixture):
    """Test Libbi data"""
    libbi = Libbi({}, 24047164)
    await libbi.refresh()
    assert libbi.serial_number == 24047164
