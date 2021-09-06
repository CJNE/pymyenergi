from pymyenergi.connection import Connection

from . import ZAPPI
from .base_device import BaseDevice

CHARGE_MODES = ["None", "Fast", "Eco", "Eco+", "Stopped"]
STATES = ["Unkn0", "Paused", "Unkn2", "Charging", "Boosting", "Completed"]
PLUG_STATES = {
    "A": "EV Disconnected",
    "B1": "EV Connected",
    "B2": "Waiting for EV",
    "C1": "EV ready to charge",
    "C2": "Charging",
    "F": "Fault",
}


class Zappi(BaseDevice):
    """Zappi Client for myenergi API."""

    def __init__(self, connection: Connection, serialno, data=None) -> None:
        self.history_data = {}
        super().__init__(connection, serialno, data)

    @property
    def kind(self):
        return ZAPPI

    @property
    def prefix(self):
        return "Z"

    @property
    def charge_mode(self):
        """Charge mode, one of Fast, Eco, Eco+ and Stopped"""
        return CHARGE_MODES[self._data.get("zmo", 0)]

    @property
    def charge_added(self):
        """Charge added this session in kWh"""
        return self._data.get("che")

    @property
    def is_dst(self):
        """Is DST in use"""
        return self._data.get("dat") == 1

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
        """Current transformer 5"""
        return self._create_ct(5)

    @property
    def ct6(self):
        """Current transformer 6"""
        return self._create_ct(6)

    @property
    def supply_frequency(self):
        """Supply frequency in Hz"""
        return self._data.get("frq")

    @property
    def supply_voltage(self):
        """Supply voltage in V"""
        return self._data.get("vol")

    @property
    def power_grid(self):
        """Grid power in W"""
        return self._data.get("grd", 0)

    @property
    def power_generated(self):
        """Generated power in W"""
        return self._data.get("gen", 0)

    @property
    def status(self):
        """Current status, one of Paused, Charging or Completed"""
        return STATES[self._data.get("sta", 1)]

    @property
    def plug_status(self):
        """Plug status, one of EV Disconnected, EV Connected, Waiting for EV, EV Ready to charge, Charging or Fault"""
        return PLUG_STATES.get(self._data.get("pst"), "")

    @property
    def priority(self):
        """Charger priority"""
        return self._data.get("pri", 0)

    @property
    def l1_phase(self):
        """What phase L1 is connected to"""
        return self._data.get("pha", 0)

    @property
    def locked(self):
        """Lock status"""
        return self._data.get("lck", 0) >> 1 & 1 == 1

    @property
    def lock_when_pluggedin(self):
        """Lock when plugged in status"""
        return self._data.get("lck", 0) >> 2 & 1 == 1

    @property
    def lock_when_unplugged(self):
        """Lock when unplugged status"""
        return self._data.get("lck", 0) >> 3 & 1 == 1

    @property
    def charge_when_locked(self):
        """Charge when locked enabled"""
        return self._data.get("lck", 0) >> 4 & 1 == 1

    @property
    def charge_session_allowed(self):
        """Allow charge override"""
        return self._data.get("lck", 0) >> 5 & 1 == 1

    @property
    def minimum_green_level(self):
        """Minimum green level"""
        return self._data.get("mgl", -1)

    @property
    def smart_boost_start_hour(self):
        """Smart boost starting at hour"""
        return self._data.get("sbh", -1)

    @property
    def smart_boost_start_minute(self):
        """Smart boost starting at minute"""
        return self._data.get("sbm", -1)

    @property
    def smart_boost_amount(self):
        """Smart boost amount of energy to add"""
        return self._data.get("sbk", -1)

    # @property
    # def boost_start_hour(self):
    #     """Boost starting at hour ??"""
    #     return self._data.get("tbh", -1)

    # @property
    # def boost_start_minute(self):
    #     """Boost starting at minute ??"""
    #     return self._data.get("tbm", -1)

    @property
    def boost_amount(self):
        """Boost amount of energy to add"""
        return self._data.get("tbk", -1)

    def show(self):
        """Returns a string with all data in human readable format"""
        ret = ""
        name = ""
        if self.name:
            name = f" {self.name}"
        ret = ret + f"Zappi{name} "
        ret = ret + f"S/N {self.serial_number} version {self.firmware_version}\n\n"
        ret = ret + f"Status: {self.status}\n"
        ret = ret + f"Plug status: {self.plug_status}\n"
        ret = ret + f"Locked: {self.locked}\n"
        ret = ret + f"Charge added: {self.charge_added}\n"
        ret = ret + f"Priority: {self.priority}\n"
        ret = ret + f"Charge mode: {self.charge_mode}\n"
        ret = ret + "\n"
        ret = ret + f"Lock when plugged in   : {self.lock_when_pluggedin}\n"
        ret = ret + f"Lock when unplugged    : {self.lock_when_unplugged}\n"
        ret = ret + f"Charge when locked     : {self.charge_when_locked}\n"
        ret = ret + f"Charge session allowed : {self.charge_session_allowed}\n"
        ret = ret + "\n"
        ret = ret + f"CT 1 {self.ct1.name} {self.ct1.power}W\n"
        ret = ret + f"CT 2 {self.ct2.name} {self.ct2.power}W\n"
        ret = ret + f"CT 3 {self.ct3.name} {self.ct3.power}W\n"
        if self.ct4.name != "None":
            ret = ret + f"CT 4 {self.ct4.name} {self.ct4.power}W\n"
        if self.ct5.name != "None":
            ret = ret + f"CT 5 {self.ct5.name} {self.ct5.power}W\n"
        if self.ct6.name != "None":
            ret = ret + f"CT 6 {self.ct6.name} {self.ct6.power}W\n"
        ret = ret + "\n"
        ret = ret + f"Supply voltage: {self.supply_voltage}V\n"
        ret = ret + f"Line frequency: {self.supply_frequency}Hz\n"
        ret = ret + f"L1 phase: {self.l1_phase}\n"
        ret = ret + "Power:\n"
        ret = ret + f"  Grid      : {self.power_grid}W\n"
        ret = ret + f"  Generated : {self.power_generated}W\n"
        ret = ret + "\n"
        ret = ret + f"Boost with {self.boost_amount}kWh\n"
        ret = ret + "Smart Boost start at"
        ret = ret + f" {self.smart_boost_start_hour}:{self.smart_boost_start_minute}"
        ret = ret + f" add {self.smart_boost_amount}kWh\n"
        ret = ret + f"Minimum green level: {self.minimum_green_level}%"
        return ret

    async def stop_charge(self):
        """Stop charge"""
        await self._connection.get(f"/cgi-zappi-mode-Z{self._serialno}-4-0-0-0000")
        return True

    async def set_charge_mode(self, mode):
        """Set charge mode, one of Fast, Eco, Eco+ or Stopped"""
        mode_int = CHARGE_MODES.index(mode.capitalize())
        await self._connection.get(
            f"/cgi-zappi-mode-Z{self._serialno}-{mode_int}-0-0-0000"
        )
        # Set local data if successful
        self._data["zmo"] = mode_int
        return True

    async def set_minimum_green_level(self, level):
        """Set minimum green level 0-100"""
        await self._connection.get(f"/cgi-set-min-green-Z{self._serialno}-{level}")
        # Set local data if successful
        self._data["mgl"] = level
        return True

    async def start_boost(self, amount):
        """Start boost"""
        await self._connection.get(
            f"/cgi-zappi-mode-Z{self._serialno}-0-10-{int(amount)}-0000"
        )
        return True

    async def start_smart_boost(self, amount, complete_by):
        """Start smart boost"""
        time = complete_by.replace(":", "")
        await self._connection.get(
            f"/cgi-zappi-mode-Z{self._serialno}-0-11-{int(amount)}-{time}"
        )
        return True

    async def stop_boost(self):
        """Stop boost"""
        await self._connection.get(f"/cgi-zappi-mode-Z{self._serialno}-0-2-0-0000")
        return True
