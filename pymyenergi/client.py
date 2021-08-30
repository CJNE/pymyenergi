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


class MyenergiClient:
    """Zappi Client for myenergi API."""

    def __init__(
        self,
        connection: Connection,
    ) -> None:
        self._connection = connection
        self.devices = {}
        self._data = []
        self._keys = None

    @property
    def site_name(self):
        """myenergi API site name"""
        return self.find_device_name("siteName", f"Hub_{self._connection.username}")

    def find_device_name(self, key, default_value):
        """Find device or site name"""
        keys = list(self._keys.values())[0]
        return next((item["val"] for item in keys if item["key"] == key), default_value)

    async def refresh(self):
        """Refresh device data"""
        data = await self.fetch_data()
        self._data = data["devices"]
        self._keys = data["keys"]
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
                    serial_key = device_obj.prefix + str(device_obj.serial_number)
                    device_obj.name = self.find_device_name(
                        serial_key, f"{device_obj.kind}-{device_obj.serial_number}"
                    )
                    self.devices[serial] = device_obj
                else:
                    existing_device.data = device_data

    async def fetch_data(self):
        """Fetch data from myenergi"""
        keys = self._keys
        if keys is None:
            keys = await self._connection.get("/cgi-get-app-key-")
        devices = await self._connection.get("/cgi-jstatus-*")
        data = {"devices": devices, "keys": keys}
        return data

    async def get_devices(self, kind="all", refresh=True):
        """Fetch devices, all or of a specific kind"""
        if refresh:
            await self.refresh()
        all_devices = list(self.devices.values())
        if kind == "all":
            return all_devices
        return list(filter(lambda d: (d.kind == kind), all_devices))
