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
        self._inited = False

    async def _initDevices(self):
        if not self._inited:
            data = await self.getData()
            self._inited = True
            for grp in data:
                key = list(grp.keys())[0]
                if key not in DEVICE_TYPES:
                    continue
                devices = grp[key]
                for device in devices:
                    serial = device.get("sno")
                    device_obj = device_factory(self._connection, key, serial, device)
                    self.devices[serial] = device_obj

    async def refresh(self):
        self._data = await self.getData()

    async def getData(self):
        data = await self._connection.get("/cgi-jstatus-*")
        return data

    async def getDevices(self, kind="all"):
        await self._initDevices()
        allDevices = list(self.devices.values())
        if kind == "all":
            return allDevices
        return list(filter(lambda d: (d.kind == kind), allDevices))
