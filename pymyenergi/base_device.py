from abc import ABC
from abc import abstractmethod

from pymyenergi.connection import Connection


class CT:
    """Current Transformer class"""

    def __init__(self, name, value, phase=None) -> None:
        self._name = name
        self._value = value
        self._phase = phase

    @property
    def name(self):
        """Name of CT clamp"""
        return self._name

    @property
    def power(self):
        """Power reading of CT clamp in W"""
        return self._value

    @property
    def phase(self):
        """What phase the CT is assigned to"""
        return self._phase


class BaseDevice(ABC):
    """Base class for MyEnergi devices"""

    def __init__(self, connection: Connection, serialno, data=None) -> None:
        self._connection = connection
        self._serialno = serialno
        self._data = data or {}

    @property
    @abstractmethod
    def kind(self):
        """What kind of device"""

    def _create_ct(self, ct_number):
        """Create a CT from data"""
        return CT(
            self._data.get(f"ectt{ct_number}"),
            self._data.get(f"ectp{ct_number}", 0),
            self._data.get(f"ect{ct_number}p", None),
        )

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
    def ct3(self):
        """Current transformer 3"""
        return self._create_ct(3)

    @abstractmethod
    async def get_data(self):
        """Fetch data from MyEnergi"""

    async def refresh(self):
        """Refresh device data"""
        self._data = await self.get_data()

    def __str__(self):
        return f"{self.kind} S/N: {self._serialno}"

    def __repr__(self):
        return f"{self.kind}-{self._serialno}"
