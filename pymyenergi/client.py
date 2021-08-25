from pymyenergi.connection import Connection

from .eddi import Eddi
from .harvi import Harvi
from .zappi import Zappi

DEVICE_TYPES = ["eddi", "zappi", "harvi"]


class MyEnergiClient:
    """Zappi Client for MyEnergi API."""

    def __init__(
        self,
        connection: Connection,
    ) -> None:
        self._connection = connection
        self.devices = {"eddi": [], "zappi": [], "harvi": []}
        self._inited = False

    async def _initDevices(self):
        if not self._inited:
            data = await self.refresh()
            self._inited = True
            for grp in data:
                key = list(grp.keys())[0]
                devices = grp[key]
                for device in devices:
                    if key == "eddi":
                        self.devices[key].append(
                            Eddi(self._connection, device["sno"], device)
                        )
                    elif key == "zappi":
                        self.devices[key].append(
                            Zappi(self._connection, device["sno"], device)
                        )
                    elif key == "harvi":
                        self.devices[key].append(
                            Harvi(self._connection, device["sno"], device)
                        )

    async def refresh(self):
        data = await self._connection.get("/cgi-jstatus-*")
        return data

    async def getDevices(self, kind="all"):
        await self._initDevices()
        if kind == "all":
            ret = []
            for k in DEVICE_TYPES:
                devices = self.devices.get(k, [])
                ret.extend(devices)
            return ret
        return self.devices.get(kind, [])
