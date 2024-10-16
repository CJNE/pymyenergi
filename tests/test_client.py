from unittest.mock import MagicMock

import pytest

from pymyenergi.client import MyenergiClient
from pymyenergi.eddi import Eddi
from pymyenergi.harvi import Harvi
from pymyenergi.libbi import Libbi
from pymyenergi.zappi import Zappi

# All test coroutines will be treated as marked.
pytestmark = pytest.mark.asyncio


class MockConnection:
    """Connection to myenergi API."""

    def __init__(self, app_password, app_email) -> None:
        """Initialize connection object."""
        self.app_password = app_password
        self.app_email = app_email

    async def discoverLocations(self):
        return

    def checkAndUpdateToken(self):
        return

    async def send(self, method, url, json=None, oauth=False):
        return MagicMock()

    async def get(self, url, data=None, oauth=False):
        return await self.send("GET", url, data, oauth)

    async def post(self, url, data=None, oauth=False):
        return await self.send("POST", url, data, oauth)

    async def put(self, url, data=None, oauth=False):
        return await self.send("PUT", url, data, oauth)

    async def delete(self, url, data=None, oauth=False):
        return await self.send("DELETE", url, data, oauth)


conn = MockConnection("test@test.com", "1234")


async def test_init(bypass_client_fetch_data):
    client = MyenergiClient(conn)
    await client.refresh()
    assert len(client.devices) == 0


async def test_init_error(error_on_client_fetch_data):
    client = MyenergiClient(conn)
    with pytest.raises(Exception):
        assert await client.refresh()


async def test_get_all_devices(client_fetch_data_fixture):
    client = MyenergiClient(conn)
    devices = await client.get_devices()
    assert len(devices) == 6


async def test_get_eddi_devices(client_fetch_data_fixture):
    client = MyenergiClient(conn)
    devices = await client.get_devices("eddi")
    assert len(devices) == 1
    assert isinstance(devices[0], Eddi)


async def test_get_zappi_devices(client_fetch_data_fixture):
    client = MyenergiClient(conn)
    devices = await client.get_devices("zappi")
    assert len(devices) == 2
    assert isinstance(devices[1], Zappi)


async def test_get_harvi_devices(client_fetch_data_fixture):
    client = MyenergiClient(conn)
    devices = await client.get_devices("harvi")
    assert len(devices) == 2
    assert isinstance(devices[1], Harvi)


async def test_1p_harvi_eddi_solar_battery(client_1p_zappi_harvi_solar_battery_fixture):
    client = MyenergiClient(conn)
    devices = await client.get_devices("harvi")
    assert len(devices) == 1
    assert isinstance(devices[0], Harvi)
    devices = await client.get_devices("zappi")
    assert len(devices) == 1
    assert isinstance(devices[0], Zappi)
    assert client.power_grid == 10000
    assert client.power_generation == 5000
    assert client.power_battery == 3000
    assert client.power_charging == 2000
    assert client.consumption_home == 16000


async def test_get_libbi_devices(client_fetch_data_fixture):
    client = MyenergiClient(conn)
    devices = await client.get_devices("libbi")
    assert len(devices) == 1
    assert isinstance(devices[0], Libbi)
