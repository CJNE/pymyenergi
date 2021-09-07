import logging
from datetime import datetime
from datetime import timezone

from pymyenergi.connection import Connection

from . import CT_BATTERY
from . import CT_GENERATION
from . import CT_GRID
from . import CT_LOAD
from . import DEVICE_TYPES
from . import EDDI
from . import HARVI
from . import HOUR
from . import ZAPPI
from .eddi import Eddi
from .harvi import Harvi
from .zappi import Zappi

_LOGGER = logging.getLogger(__name__)


def device_factory(conn, kind, serial, data=None):
    """Create device instances"""
    if kind == ZAPPI:
        return Zappi(conn, serial, data)
    if kind == EDDI:
        return Eddi(conn, serial, data)
    if kind == HARVI:
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

    @property
    def serial_number(self):
        """Hub serial number"""
        return self._connection.username

    def get_energy_totals(self):
        """Get total energy"""
        devices = self.get_devices_sync()
        keys = ["generated", "grid_import", "grid_export"]
        totals = {"diverted": 0}
        for key in keys:
            totals[key] = 0
        for device in devices:
            if device.kind == HARVI:
                continue
            for key in keys:
                if totals[key] == 0:
                    totals[key] = device.history_data.get(key, 0)
            totals["diverted"] = totals.get("diverted", 0) + device.history_data.get(
                "device_diverted", 0
            )
        return totals

    def get_power_totals(self):
        """Get totals for all supported CT types"""
        devices = self.get_devices_sync()
        totals = {}
        zappi_or_eddi = None
        for device in devices:
            if device.ct1.is_assigned:
                totals[device.ct1.name] = (
                    totals.get(device.ct1.name, 0) + device.ct1.power
                )
            if device.ct2.is_assigned:
                totals[device.ct2.name] = (
                    totals.get(device.ct2.name, 0) + device.ct2.power
                )

            if device.kind in [ZAPPI, HARVI]:
                if device.ct3.is_assigned:
                    totals[device.ct3.name] = (
                        totals.get(device.ct3.name, 0) + device.ct3.power
                    )
            if device.kind == EDDI:
                zappi_or_eddi = device
            if device.kind == ZAPPI:
                zappi_or_eddi = device
                if device.kind == ZAPPI:
                    if device.ct4.is_assigned:
                        totals[device.ct4.name] = (
                            totals.get(device.ct4.name, 0) + device.ct4.power
                        )
                    if device.ct5.is_assigned:
                        totals[device.ct5.name] = (
                            totals.get(device.ct5.name, 0) + device.ct5.power
                        )
                    if device.ct6.is_assigned:
                        totals[device.ct6.name] = (
                            totals.get(device.ct6.name, 0) + device.ct6.power
                        )

        if totals.get(CT_GRID, 0) == 0 and zappi_or_eddi is not None:
            totals[CT_GRID] = zappi_or_eddi.power_grid
        if totals.get(CT_GENERATION, 0) == 0 and zappi_or_eddi is not None:
            totals[CT_GENERATION] = zappi_or_eddi.power_generated

        return totals

    @property
    def consumption_home(self):
        """Calculates home power"""
        # calculation is all generation + grid + battery - device consumption
        totals = self.get_power_totals()
        return (
            totals.get(CT_GENERATION, 0)
            + totals.get(CT_GRID, 0)
            + totals.get(CT_BATTERY, 0)
            - totals.get(CT_LOAD, 0)
        )

    @property
    def energy_imported(self):
        """Grid imported energy"""
        energy_totals = self.get_energy_totals()
        return energy_totals.get("grid_import", 0)

    @property
    def energy_exported(self):
        """Grid exported energy"""
        energy_totals = self.get_energy_totals()
        return energy_totals.get("grid_export", 0)

    @property
    def energy_generated(self):
        """Generated energy"""
        energy_totals = self.get_energy_totals()
        return energy_totals.get("generated", 0)

    @property
    def energy_diverted(self):
        """Diverted energy"""
        energy_totals = self.get_energy_totals()
        return energy_totals.get("diverted", 0)

    @property
    def power_grid(self):
        """Grid total power"""
        totals = self.get_power_totals()
        return totals.get(CT_GRID, 0)

    @property
    def power_generation(self):
        """Generation total power"""
        totals = self.get_power_totals()
        return totals.get(CT_GENERATION, 0)

    @property
    def power_charging(self):
        """Chargers total power"""
        totals = self.get_power_totals()
        return totals.get(CT_LOAD, 0)

    @property
    def power_battery(self):
        """Battery total power"""
        totals = self.get_power_totals()
        return totals.get(CT_BATTERY, 0)

    def find_device_name(self, key, default_value):
        """Find device or site name"""
        keys = list(self._keys.values())[0]
        return next((item["val"] for item in keys if item["key"] == key), default_value)

    async def refresh(self):
        """Refresh device data"""
        _LOGGER.debug("Refreshing data for all myenergi devices")
        data = await self.fetch_data()
        self._data = data["devices"]
        self._keys = data["keys"]
        for grp in self._data:
            key = list(grp.keys())[0]
            if key not in DEVICE_TYPES:
                if key != "asn":
                    _LOGGER.debug(f"Unknown device type: {key}")
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
                    _LOGGER.debug(f"Adding {device_obj.kind} {device_obj.name}")
                    self.devices[serial] = device_obj
                else:
                    _LOGGER.debug(
                        f"Updating {existing_device.kind} {existing_device.name}"
                    )
                    existing_device.data = device_data

    async def refresh_history_today(self):
        today = datetime.now(timezone.utc)
        today = today.replace(hour=0, minute=0, second=0, microsecond=0)
        return await self.refresh_history(today, 24, HOUR)

    async def refresh_history(self, from_date, how_long, resolution):
        """Refresh history data for eddi and zappi"""
        devices = await self.get_devices("all", False)
        for device in devices:
            if device.kind == HARVI:
                continue
            await device.refresh_history_data(from_date, how_long, resolution)

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
        if refresh or not self.devices:
            await self.refresh()
        return self.get_devices_sync(kind)

    def get_devices_sync(self, kind="all"):
        """Return current devices"""
        all_devices = list(self.devices.values())
        if kind == "all":
            return all_devices
        return list(filter(lambda d: (d.kind == kind), all_devices))
