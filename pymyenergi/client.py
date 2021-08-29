from pymyenergi.connection import Connection

from .eddi import Eddi
from .harvi import Harvi
from .zappi import Zappi

DEVICE_TYPES = ["eddi", "zappi", "harvi"]


def device_factory(conn, kind, serial, data=None):
    """Create device instances"""
    if kind == "zappi":
        return Zappi(conn, serial, data)
    if kind == "eddi":
        return Eddi(conn, serial, data)
    if kind == "harvi":
        return Harvi(conn, serial, data)
    raise Exception(f"Unsupported device type {kind}")


class MyEnergiClient:
    """Zappi Client for MyEnergi API."""

    def __init__(
        self,
        connection: Connection,
    ) -> None:
        self._connection = connection
        self.devices = {}
        self._data = []

    async def refresh(self):
        """Refresh device data"""
        self._data = await self.fetch_data()
        for grp in self._data:
            key = list(grp.keys())[0]
            if key not in DEVICE_TYPES:
                continue
            devices = grp[key]
            for device_data in devices:
                serial = device_data.get("sno")
                existing_device = self.devices.get(serial, None)
                if existing_device is None:
                    device_obj = device_factory(
                        self._connection, key, serial, device_data
                    )
                    self.devices[serial] = device_obj
                else:
                    existing_device.data = device_data

    async def fetch_data(self):
        """Fetch data from MyEnergi"""
        data = await self._connection.get("/cgi-jstatus-*")
        return data

    async def get_devices(self, kind="all", refresh=True):
        """Fetch devices, all or of a specific kind"""
        if refresh:
            await self.refresh()
        all_devices = list(self.devices.values())
        if kind == "all":
            return all_devices
        return list(filter(lambda d: (d.kind == kind), all_devices))
