import logging
from abc import ABC
from abc import abstractmethod
from datetime import datetime
from datetime import timedelta
from datetime import timezone

from pymyenergi.connection import Connection

from . import HOUR
from . import MINUTE

_LOGGER = logging.getLogger(__name__)


class CT:
    """Current Transformer class"""

    def __init__(self, name, value=0, phase=None) -> None:
        self._name = name
        self._value = value
        self._phase = phase

    @property
    def name(self):
        """Name of CT clamp"""
        return self._name

    @property
    def name_as_key(self):
        """Snake case version of name"""
        return "ct_" + self._name.replace(" ", "_").lower()

    @property
    def power(self):
        """Power reading of CT clamp in W"""
        return self._value

    @property
    def phase(self):
        """What phase the CT is assigned to"""
        return self._phase

    @property
    def is_assigned(self):
        """Is the CT assigned?"""
        return self.name != "None"

    @property
    def is_generation(self):
        return "generation" in self._name.lower()

    @property
    def is_grid(self):
        return "grid" in self._name.lower()


class BaseDevice(ABC):
    """Base class for myenergi devices"""

    def __init__(self, connection: Connection, serialno, data=None) -> None:
        self._connection = connection
        self._serialno = serialno
        self._data = data or {}
        self._name = None

    @property
    @abstractmethod
    def kind(self):
        """What kind of device"""

    @property
    @abstractmethod
    def prefix(self):
        """Device prefix used in api calls"""

    def _create_ct(self, ct_number):
        """Create a CT from data"""
        return CT(
            self._data.get(f"ectt{ct_number}", "None"),
            self._data.get(f"ectp{ct_number}", 0),
            self._data.get(f"ect{ct_number}p", None),
        )

    async def fetch_data(self):
        """Fetch data from myenergi"""
        response = await self._connection.get(
            f"/cgi-jstatus-{self.prefix}{self._serialno}"
        )
        data = response[self.kind][0]
        return data

    async def energy_today(self):
        today = datetime.now(timezone.utc)
        today = today.replace(hour=0, minute=0, second=0, microsecond=0)
        # return await self.history_energy_minutes(today, 1440)
        return await self.history_energy_hours(today, 24)

    async def history_energy_minutes(self, date_from, how_long=1440):
        if date_from is None:
            date_from = datetime.now(timezone.utc) - timedelta(minutes=how_long)
        return await self.fetch_history_data(date_from, how_long, MINUTE)

    async def history_energy_hours(self, date_from, how_long=24):
        if date_from is None:
            date_from = datetime.now(timezone.utc) - timedelta(hours=how_long)
        return await self.fetch_history_data(date_from, how_long, HOUR)

    async def fetch_history_data(self, date_from, how_long, resolution):
        energy_wh = {
            "gep": 0,
            "gen": 0,
            "imp": 0,
            "exp": 0,
            "h1d": 0,
            "h1b": 0,
            "h2d": 0,
            "h2b": 0,
            "h3d": 0,
            "h3b": 0,
            "ct1": 0,
            "ct2": 0,
            "ct3": 0,
            "ct4": 0,
            "ct5": 0,
            "ct6": 0,
        }
        if resolution == MINUTE:
            url = f"/cgi-jday-{self.prefix}{self._serialno}-{date_from.year}-{date_from.month}-{date_from.day}-{date_from.hour}-0-{how_long}"
        else:
            url = f"/cgi-jdayhour-{self.prefix}{self._serialno}-{date_from.year}-{date_from.month}-{date_from.day}-{date_from.hour}-{how_long}"
        _LOGGER.debug(f"Fetching {resolution} history data for {self.kind}")
        data = await self._connection.get(url)
        data = data[f"U{self.serial_number}"]

        for row in data:
            for key in energy_wh:
                if key in ["ct1", "ct2", "ct3", "ct4", "ct5", "ct6"]:
                    watt_hours = (
                        row.get(f"pe{key}", 0) / 3600 - row.get(f"ne{key}", 0) / 3600
                    )
                else:
                    watt_hours = row.get(key, 0) / 3600
                energy_wh[key] = energy_wh[key] + watt_hours
        return_data = {
            "generated": round(energy_wh["gep"]),
            "grid_import": round(energy_wh["imp"]),
            "grid_export": round(energy_wh["exp"]),
            "device_total": round(
                energy_wh["h1b"] + energy_wh["h2b"] + energy_wh["h3b"]
            ),
            "device_diverted": round(
                energy_wh["h1d"] + energy_wh["h2d"] + energy_wh["h3d"]
            ),
        }
        for i in range(6):
            key = f"ct{i+1}"
            if hasattr(self, key):
                ct_key = getattr(self, key).name_as_key
                if ct_key != "ct_none":
                    return_data[ct_key] = round(
                        return_data.get(ct_key, 0) + energy_wh[f"ct{i+1}"]
                    )
        return return_data

    @property
    def name(self):
        """Name of device"""
        return self._name

    @name.setter
    def name(self, value):
        self._name = value

    @property
    def serial_number(self):
        """Serial Number"""
        return self._data.get("sno", None)

    @property
    def firmware_version(self):
        """Firmware version"""
        return self._data.get("fwv", None)

    @property
    def date(self):
        """Device date"""
        return self._data.get("dat")

    @property
    def time(self):
        """Device time"""
        return self._data.get("tim")

    @property
    def ct1(self):
        """Current transformer 1"""
        return self._create_ct(1)

    @property
    def ct2(self):
        """Current transformer 2"""
        return self._create_ct(2)

    @property
    def data(self):
        """All device data"""
        return self._data

    @data.setter
    def data(self, value):
        """Set all device data"""
        self._data = value

    async def refresh_history_data(self, from_date, how_long, resolution):
        """Refresh device history data"""
        self.history_data = await self.fetch_history_data(
            from_date, how_long, resolution
        )

    async def refresh(self):
        """Refresh device data"""
        self.data = await self.fetch_data()

    def __str__(self):
        return f"{self.kind} S/N: {self._serialno}"

    def __repr__(self):
        return f"{self.kind}-{self._serialno}"
