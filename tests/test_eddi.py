import pytest
from pymyenergi.eddi import Eddi

pytestmark = pytest.mark.asyncio


async def test_refresh(eddi_fetch_data_fixture):
    """Test Zappi data"""
    eddi = Eddi({}, 16042300)
    await eddi.refresh()
    assert eddi.serial_number == 10088800
    assert eddi.diverted_session == 8.2
