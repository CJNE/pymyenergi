import pytest
from pymyenergi.client import MyEnergiClient
from pymyenergi.eddi import Eddi
from pymyenergi.harvi import Harvi
from pymyenergi.zappi import Zappi


conn = {}


async def test_init(bypass_client_refresh):
    client = MyEnergiClient(conn)
    await client.refresh()
    assert len(client.devices) == 3
    assert len(client.devices["zappi"]) == 0
    assert len(client.devices["eddi"]) == 0
    assert len(client.devices["harvi"]) == 0


async def test_init_error(error_on_client_refresh):
    client = MyEnergiClient(conn)
    with pytest.raises(Exception):
        assert await client.refresh()


async def test_get_all_devices(client_refresh_fixture):
    client = MyEnergiClient(conn)
    devices = await client.getDevices()
    assert len(devices) == 5


async def test_get_eddi_devices(client_refresh_fixture):
    client = MyEnergiClient(conn)
    devices = await client.getDevices("eddi")
    assert len(devices) == 1
    assert isinstance(devices[0], Eddi)


async def test_get_zappi_devices(client_refresh_fixture):
    client = MyEnergiClient(conn)
    devices = await client.getDevices("zappi")
    assert len(devices) == 2
    assert isinstance(devices[1], Zappi)


async def test_get_harvi_devices(client_refresh_fixture):
    client = MyEnergiClient(conn)
    devices = await client.getDevices("harvi")
    assert len(devices) == 2
    assert isinstance(devices[1], Harvi)
