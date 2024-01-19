import logging

from pymyenergi.connection import Connection

from . import LIBBI
from .base_device import BaseDevice

_LOGGER = logging.getLogger(__name__)

STATES = {
    0: "Off",
    1: "On",
    2: "Battery Full",
    4: "Idle",
    5: "Charging",
    6: "Discharging",
    7: "Duration Charging",
    8: "Duration Drain",
    12: "Target Charge",
    51: "Boosting",
    53: "Boosting",
    55: "Boosting",
    11: "Stopped",
    101: "Battery Empty",
    102: "Full",
    104: "Full",
    151: "FW Upgrade (ARM)",
    156: "FW Upgrade (DSP)",
    172: "BMS Charge Temperature Low",
    234: "Calibration Charge",
    251: "FW Upgrade (DSP)",
    252: "FW Upgrade (ARM)",
}

LIBBI_MODES = ["Stopped", "Normal", "Export"]
LIBBI_MODE_CONFIG = {
    "Stopped": {"mode_int": 0, "mode_name": "STOP"},
    "Normal": {"mode_int": 1, "mode_name": "BALANCE"},
    "Export": {"mode_int": 5, "mode_name": "DRAIN"},
}
"""The myenergi app defines other modes as well (capture, charge, match), but these cannot be set"""


class Libbi(BaseDevice):
    """Libbi Client for myenergi API."""

    def __init__(self, connection: Connection, serialno, data={}) -> None:
        self.history_data = {}
        self._extra_data = {}
        super().__init__(connection, serialno, data)

    async def refresh_extra(self):
        # only refresh this data if we have app credentials
        if self._connection.app_email and self._connection.app_password:
            chargeFromGrid = await self._connection.get(
                "/api/AccountAccess/LibbiMode?serialNo=" + str(self.serial_number),
                oauth=True,
            )
            self._extra_data["charge_from_grid"] = chargeFromGrid["content"][
                str(self.serial_number)
            ]
            chargeTarget = await self._connection.get(
                "/api/AccountAccess/" + str(self.serial_number) + "/LibbiChargeSetup",
                oauth=True,
            )
            self._extra_data["charge_target"] = chargeTarget["content"]["energyTarget"]

    @property
    def kind(self):
        return LIBBI

    @property
    def status(self):
        """Get current known status"""
        n = self._data.get("sta", 1)
        if n in STATES:
            return STATES[n]
        else:
            return n

    @property
    def local_mode(self):
        """Get current known status"""
        return self._data.get("lmo", 1)

    @property
    def prefix(self):
        return "E"

    @property
    def ct_keys(self):
        """Return CT key names that are not none"""
        keys = {}
        for i in range(6):
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
        return self._data.get("che", 0)

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
    def state_of_charge(self):
        """State of Charge in %"""
        return self._data.get("soc", 0)

    @property
    def priority(self):
        """Current priority"""
        return self._data.get("pri")

    @property
    def battery_size(self):
        """Battery size in kwh"""
        return self._data.get("mbc", 0) / 1000

    @property
    def inverter_size(self):
        """Inverter size in kwh"""
        return self._data.get("mic", 0) / 1000

    @property
    def grid_import(self):
        """Grid import from history data"""
        return self.history_data.get("grid_import", 0)

    @property
    def grid_export(self):
        """Grid export from history data"""
        return self.history_data.get("grid_export", 0)

    @property
    def battery_charge(self):
        """Battery charge from history data"""
        return self.history_data.get("battery_charge", 0)

    @property
    def battery_discharge(self):
        """Battery discharge from history data"""
        return self.history_data.get("battery_discharge", 0)

    @property
    def generated(self):
        """Solar generation from history data"""
        return self.history_data.get("generated", 0)

    @property
    def charge_from_grid(self):
        """Is charging from the grid enabled?"""
        return self._extra_data.get("charge_from_grid")

    @property
    def charge_target(self):
        """Libbi charge target"""
        return self._extra_data.get("charge_target", 0) / 1000

    @property
    def prefix(self):
        return "L"

    def get_mode_description(self, mode: str):
        """Get the mode name as returned by myenergi API. E.g. Normal mode is BALANCE"""
        for k in LIBBI_MODE_CONFIG:
            if LIBBI_MODE_CONFIG[k]["mode_name"] == mode:
                return k
        return "???"

    async def set_operating_mode(self, mode: str):
        """Set operating mode"""
        print("current mode", self.get_mode_description(self._data["lmo"]))
        mode_int = LIBBI_MODE_CONFIG[mode.capitalize()]["mode_int"]
        await self._connection.get(
            f"/cgi-libbi-mode-{self.prefix}{self._serialno}-{mode_int}"
        )
        self._data["lmo"] = LIBBI_MODE_CONFIG[mode.capitalize()]["mode_name"]
        return True

    async def set_charge_from_grid(self, charge_from_grid: bool):
        """Set charge from grid"""
        await self._connection.put(
            f"/api/AccountAccess/LibbiMode?chargeFromGrid={charge_from_grid}&serialNo={self._serialno}",
            oauth=True,
        )
        self._extra_data["charge_from_grid"] = charge_from_grid
        return True

    async def set_priority(self, priority):
        """Set device priority"""
        await self._connection.get(
            f"/cgi-set-priority-{self.prefix}{self._serialno}-{int(priority)}"
        )
        self._data["pri"] = int(priority)
        return True

    async def set_charge_target(self, charge_target: float):
        """Set charge target"""
        await self._connection.put(
            f"/api/AccountAccess/{self._serialno}/TargetEnergy?targetEnergy={charge_target}",
            oauth=True,
        )
        self._extra_data["charge_target"] = charge_target
        return True

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
        ret = ret + f"Libbi priority: {self.priority}\n"
        ret = ret + f"Battery size: {self.battery_size}kWh\n"
        ret = ret + f"Inverter size: {self.inverter_size}kWh\n"
        ret = ret + f"State of Charge: {self.state_of_charge}%\n"
        ret = ret + f"Generating: {self.power_generated}W\n"
        ret = ret + f"Grid: {self.power_grid}W\n"
        ret = ret + f"Status: {self.status}\n"
        ret = ret + "Local Mode: " + self.get_mode_description(self.local_mode) + "\n"
        ret = ret + "Charge from Grid: "
        if self.charge_from_grid:
            ret = ret + "Enabled\n"
        else:
            ret = ret + "Disabled\n"
        ret = ret + f"Charge target: {self.charge_target}kWh\n"
        ret = ret + f"CT 1 {self.ct1.name} {self.ct1.power}W phase {self.ct1.phase}\n"
        ret = ret + f"CT 2 {self.ct2.name} {self.ct2.power}W phase {self.ct2.phase}\n"
        ret = ret + f"CT 3 {self.ct3.name} {self.ct3.power}W phase {self.ct3.phase}\n"
        ret = ret + f"CT 4 {self.ct4.name} {self.ct4.power}W phase {self.ct4.phase}\n"
        ret = ret + f"CT 5 {self.ct5.name} {self.ct5.power}W phase {self.ct5.phase}\n"
        ret = ret + f"CT 6 {self.ct6.name} {self.ct6.power}W phase {self.ct6.phase}\n"
        for key in self.ct_keys:
            ret = ret + f"Energy {key} {self.history_data.get(key, 0)}Wh\n"
        if not self._connection.app_email or not self._connection.app_password:
            ret += "No app credentials provided - the above information might not be totally accurate\n"
        return ret
