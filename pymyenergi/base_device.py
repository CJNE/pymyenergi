from abc import ABC
from abc import abstractmethod

from pymyenergi.connection import Connection


class CT:
    def __init__(self, name, value, phase=None) -> None:
        self._name = name
        self._value = value

    @property
    def name(self):
        """Name of CT clamp"""
        return self._name

    @property
    def power(self):
        """Power reading of CT clamp in W"""
        return self._value


class BaseDevice(ABC):
    def __init__(self, connection: Connection, serialno, data={}) -> None:
        self._connection = connection
        self._serialno = serialno
        self._data = data

    @property
    @abstractmethod
    def kind(self):
        pass

    def _createCT(self, no):
        return CT(
            self._data.get(f"ectt{no}"),
            self._data.get(f"ectp{no}", 0),
            self._data.get(f"ect{no}p", None),
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
        return self._createCT(1)

    @property
    def ct2(self):
        """Current transformer 2"""
        return self._createCT(2)

    @property
    def ct3(self):
        """Current transformer 3"""
        return self._createCT(3)

    @abstractmethod
    async def getData(self):
        pass

    async def refresh(self):
        self._data = await self.getData()

    def __str__(self):
        return f"{self.kind} S/N: {self._serialno}"

    def __repr__(self):
        return f"{self.kind}-{self._serialno}"
