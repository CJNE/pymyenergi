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


class FakeConnection:
    def __init__(self, app_email=None, app_password=None):
        self.app_email = app_email
        self.app_password = app_password
        self.calls = []

    async def trpc_get(self, procedure, payload):
        self.calls.append((procedure, payload))
        return {"config": {"exportMargin": 6050, "minGreenLevel": 100}}

    async def trpc_post(self, procedure, payload):
        self.calls.append((procedure, payload))
        return {"success": True, "commandId": "abc"}


async def test_export_margin_get_and_set():
    conn = FakeConnection("a@b.c", "pw")
    zappi = Zappi(conn, 16042300)
    await zappi.refresh_extra()
    assert zappi.export_margin == 6050
    assert await zappi.set_export_margin(100)
    assert zappi.export_margin == 100
    assert conn.calls[-1] == (
        "device.userDeviceSettings.setSettings",
        {"deviceSerialNo": "16042300", "config": {"exportMargin": 100}},
    )


@pytest.mark.parametrize("value", [-50, 10050, 75])
async def test_export_margin_validation(value):
    zappi = Zappi(FakeConnection("a@b.c", "pw"), 16042300)
    with pytest.raises(ValueError):
        await zappi.set_export_margin(value)


async def test_export_margin_without_app_credentials():
    conn = FakeConnection()
    zappi = Zappi(conn, 16042300)
    await zappi.refresh_extra()
    assert zappi.export_margin is None
    assert not await zappi.set_export_margin(100)
    assert conn.calls == []
