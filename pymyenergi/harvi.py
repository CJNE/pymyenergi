from pymyenergi.connection import Connection

from . import HARVI
from .base_device import BaseDevice


class Harvi(BaseDevice):
    """Zappi Client for myenergi API."""

    def __init__(self, connection: Connection, serialno, data={}) -> None:
        super().__init__(connection, serialno, data)

    @property
    def kind(self):
        return HARVI

    @property
    def ct_keys(self):
        """Return CT key names that are not none"""
        keys = {}
        for i in range(3):
            ct = getattr(self, f"ct{i+1}")
            if ct.name_as_key == "ct_none":
                continue
            keys[ct.name_as_key] = keys.get(ct.name_as_key, 0) + 1
        return keys

    @property
    def ct3(self):
        """Current transformer 3"""
        return self._create_ct(3)

    @property
    def prefix(self):
        return "H"

    def show(self):
        """Returns a string with all data in human readable format"""
        ret = ""
        name = ""
        if self.name:
            name = f" {self.name}"
        ret = ret + f"Harvi{name} "
        ret = ret + f"S/N {self.serial_number} version {self.firmware_version}\n\n"
        ret = ret + f"CT 1 {self.ct1.name} {self.ct1.power}W phase {self.ct1.phase}\n"
        ret = ret + f"CT 2 {self.ct2.name} {self.ct2.power}W phase {self.ct2.phase}\n"
        ret = ret + f"CT 3 {self.ct3.name} {self.ct3.power}W phase {self.ct3.phase}\n"
        return ret
