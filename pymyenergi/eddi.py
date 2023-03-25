import logging

from pymyenergi.connection import Connection

from . import EDDI
from .base_device import BaseDevice

_LOGGER = logging.getLogger(__name__)

MODE_NORMAL = 1
MODE_STOPEED = 0
STATES = [
    "Unkn0",
    "Paused",
    "Unkn2",
    "Diverting",
    "Boosting",
    "Max temp reached",
    "Stopped",
]
BOOST_TARGETS = {"heater1": 1, "heater2": 2, "relay1": 11, "relay2": 12}
EDDI_MODES = ["Stopped", "Normal"]


class Eddi(BaseDevice):
    """Eddi Client for myenergi API."""

    def __init__(self, connection: Connection, serialno, data={}) -> None:
        self.history_data = {}
        super().__init__(connection, serialno, data)

    @property
    def kind(self):
        return EDDI

    @property
    def prefix(self):
        return "E"

    @property
    def heater_priority(self):
        """Current heater priority"""
        return self._data.get("hpri", 1)

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
    def l1_phase(self):
        """What phase L1 is connected to"""
        return self._data.get("pha", 0)

    @property
    def status(self):
        """Current status, one of Paused, Charging or Completed"""
        return STATES[self._data.get("sta", 1)]

    @property
    def supply_frequency(self):
        """Supply frequency in Hz"""
        return self._data.get("frq")

    @property
    def supply_voltage(self):
        """Supply voltage in V"""
        return self._data.get("vol", 0) / 10

    @property
    def consumed_session(self):
        """Energy diverted this session kWh"""
        return self._data.get("che")

    @property
    def power_grid(self):
        """Grid power in W"""
        return self._data.get("grd", 0)

    @property
    def power_generated(self):
        """Generated power in W"""
        return self._data.get("gen", 0)

    @property
    def energy_total(self):
        """Device total energy from history data"""
        return self.history_data.get("device_total", 0)

    @property
    def energy_green(self):
        """Device green energy from history data"""
        return self.history_data.get("device_green", 0)

    @property
    def temp_1(self):
        """Temperature probe 1 temp"""
        return self._data.get("tp1", -1)

    @property
    def temp_2(self):
        """Temperature probe 2 temp"""
        return self._data.get("tp2", -1)

    @property
    def temp_name_1(self):
        """Temperature probe 2 name"""
        return self._data.get("ht1", None)

    @property
    def temp_name_2(self):
        """Temperature probe 2 name"""
        return self._data.get("ht2", None)

    @property
    def priority(self):
        """Current priority"""
        return self._data.get("pri")

    @property
    def active_heater(self):
        """Active heater"""
        return self._data.get("hno")

    @property
    def remaining_boost_time(self):
        """For how much longer boost will be active in seconds"""
        return self._data.get("rbt", 0)

    @property
    def is_boosting(self):
        """For how much longer boost will be active in seconds"""
        return self._data.get("bsm", 0) == 1

    # CT1 and CT2 are defined in base device
    @property
    def ct3(self):
        """Current transformer 3"""
        return self._create_ct(3)

    # The following properties are unknonw, names might change
    @property
    def r1a(self):
        """r1a?"""
        return self._data.get("r1a")

    @property
    def r2a(self):
        """r2a?"""
        return self._data.get("r2a")

    @property
    def r1b(self):
        """r1b?"""
        return self._data.get("r1b")

    async def set_operating_mode(self, mode: str):
        """Stopped or normal mode"""
        mode_int = EDDI_MODES.index(mode.capitalize())
        await self._connection.get(f"/cgi-eddi-mode-E{self._serialno}-{mode_int}")
        if mode_int == 0:
            self._data["sta"] = 6
        else:
            self._data["sta"] = 5
        return True

    async def manual_boost(self, target: str, time: int):
        """Start manual boost of target for time minutes"""
        target_int = BOOST_TARGETS[target.lower().replace(" ", "")]
        await self._connection.get(
            f"/cgi-eddi-boost-E{self._serialno}-10-{target_int}-{time}"
        )
        return True

    async def set_priority(self, priority):
        """Set device priority"""
        await self._connection.get(
            f"/cgi-set-priority-E{self._serialno}-{int(priority)}"
        )
        self._data["pri"] = int(priority)
        return True

    async def set_heater_priority(self, target: str):
        """Start manual boost of target for time minutes"""
        target_int = BOOST_TARGETS[target.lower().replace(" ", "")]
        response = await self._connection.get(
            f"/cgi-set-heater-priority-E{self._serialno}"
        )
        cpm = response.get("cpm", 0)
        await self._connection.get(
            f"/cgi-set-heater-priority-E{self._serialno}-{target_int}-{cpm}"
        )
        self._data["hpri"] = target_int
        return True

    def show(self, short_format=False):
        """Returns a string with all data in human readable format"""
        ret = ""
        name = ""
        if self.name:
            name = f" {self.name}"
        ret = ret + f"Eddi S/N {self.serial_number}"
        ret = ret + f"{name} version {self.firmware_version}\n\n"
        if short_format:
            return ret
        ret = ret.center(80, "-") + "\n"
        ret = ret + f"Active heater:   {self.active_heater}"
        ret = ret + f"Eddi priority:   {self.priority}"
        ret = ret + f"Heater priority: {self.heater_priority}"
        if self.is_boosting:
            ret = ret + f"Boosting, {self.remaining_boost_time} miuntes left"
        ret = ret + f"CT 1 {self.ct1.name} {self.ct1.power}W\n"
        ret = ret + f"CT 2 {self.ct2.name} {self.ct2.power}W\n"
        ret = ret + f"CT 3 {self.ct3.name} {self.ct3.power}W\n"
        if self.temp_1 != -1:
            ret = ret + f"Temp {self.temp_name_1}: {self.temp_1}C\n"
        if self.temp_2 != -1:
            ret = ret + f"Temp {self.temp_name_2}: {self.temp_2}C\n"
        for key in self.ct_keys:
            ret = ret + f"Energy {key} {self.history_data.get(key, 0)}Wh\n"
        return ret
