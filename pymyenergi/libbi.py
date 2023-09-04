from pymyenergi.connection import Connection

from . import LIBBI
from .base_device import BaseDevice


class Libbi(BaseDevice):
    """Libbi Client for myenergi API."""

    def __init__(self, connection: Connection, serialno, data={}) -> None:
        super().__init__(connection, serialno, data)

    @property
    def kind(self):
        return LIBBI

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
    def ct4(self):
        """Current transformer 4"""
        return self._create_ct(4)
    
    @property
    def ct5(self):
        """Current transformer 4"""
        return self._create_ct(5)
    
    @property
    def ct6(self):
        """Current transformer 4"""
        return self._create_ct(6)
    
    @property
    def state_of_charge(self):
        """State of Charge in %"""
        return self._data.get("soc", 0)

    @property
    def battery_size(self):
        """Battery size in kwh"""
        return self._data.get("mbc", 0) /1000
    
    @property
    def inverter_size(self):
        """Inverter size in kwh"""
        return self._data.get("mic", 0) /1000
    
    @property
    def test_value(self):
        """Test value"""
        return self._data.get("ectp5", 0)

    @property
    def prefix(self):
        return "H"

    def show(self, short_format=False):
        """Returns a string with all data in human readable format"""
        ret = ""
        name = ""
        if self.name:
            name = f" {self.name}"
        ret = ret + f"Libbi S/N {self.serial_number}"
        ret = ret + f"{name}"
        if short_format:
            return ret
        ret = ret.center(80, "-") + "\n"
        ret = ret + f"Battery size: {self.battery_size}kWh\n"
        ret = ret + f"Inverter size: {self.inverter_size}kWh\n"
        ret = ret + f"State of Charge: {self.state_of_charge}%\n"
        ret = ret + f"CT 1 {self.ct1.name} {self.ct1.power}W phase {self.ct1.phase}\n"
        ret = ret + f"CT 2 {self.ct2.name} {self.ct2.power}W phase {self.ct2.phase}\n"
        ret = ret + f"CT 3 {self.ct3.name} {self.ct3.power}W phase {self.ct3.phase}\n"
        ret = ret + f"CT 4 {self.ct4.name} {self.ct4.power}W phase {self.ct4.phase}\n"
        ret = ret + f"CT 5 {self.ct5.name} {self.ct5.power}W phase {self.ct5.phase}\n"
        ret = ret + f"CT 6 {self.ct6.name} {self.ct6.power}W phase {self.ct6.phase}\n"
        ret = ret + f"\nTest Value {self.test_value}\n"

        return ret
