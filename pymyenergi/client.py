from pymyenergi.connection import Connection
from .harvi import Harvi
from .zappi import Zappi
from .eddi import Eddi

DEVICE_TYPES = ['eddi', 'zappi', 'harvi']
class MyEnergiClient:
    """Zappi Client for MyEnergi API."""

    def __init__(
        self,
        connection: Connection,
    ) -> None:
        self._connection = connection
        self.devices = None

    async def _initDevices(self):
        if self.devices is None:
            self.devices = {}
            data = await self.getStatus()
            for grp in data:
                key = list(grp.keys())[0]
                devices = grp[key]
                self.devices[key] = []
                for device in devices:
                    if key == 'eddi':
                        self.devices[key].append(Eddi(self._connection, device['sno'], device))
                    elif key == 'zappi':
                        self.devices[key].append(Zappi(self._connection, device['sno'], device))
                    elif key == 'harvi':
                        self.devices[key].append(Harvi(self._connection, device['sno'], device))

    async def getStatus(self):
        data = await self._connection.get("/cgi-jstatus-*")
        return data

    async def getDevices(self, kind='all'):
        await self._initDevices()
        if(kind == 'all'):
            ret = []
            for k in DEVICE_TYPES:
                devices = self.devices.get(k, [])
                ret.extend(devices)
            return ret
        return self.devices.get(kind, [])
