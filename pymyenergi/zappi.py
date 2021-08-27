from pymyenergi.connection import Connection

from .base_device import BaseDevice

CHARGE_MODES = [None, "Fast", "Eco", "Eco+", "Stopped"]
STATES = ["Unkn0", "Paused", "Unkn2", "Charging", "Unkn4", "Completed"]
PLUG_STATES = {
    "A": "EV Disconnected",
    "B1": "EV Connected",
    "B2": "Waiting for EV",
    "C1": "EV ready to charge",
    "C2": "Charging",
    "F": "Fault",
}


class Zappi(BaseDevice):
    """Zappi Client for MyEnergi API."""

    def __init__(self, connection: Connection, serialno, data=None) -> None:
        super().__init__(connection, serialno, data)

    @property
    def kind(self):
        return "zappi"

    @property
    def charge_mode(self):
        """Charge mode, one of Fast, Eco, Eco+ and Stopped"""
        return CHARGE_MODES[self._data.get("zmo", 0)]

    @property
    def charge_added(self):
        """Charge added in kWh"""
        return self._data.get("che")

    @property
    def is_dst(self):
        """Is DST in use"""
        return self._data.get("dat") == 1

    @property
    def ct4(self):
        """Current transformer 4"""
        return self._createCT(4)

    @property
    def ct5(self):
        """Current transformer 5"""
        return self._createCT(5)

    @property
    def ct6(self):
        """Current transformer 6"""
        return self._createCT(6)

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
    def num_phases(self):
        """Number of phases"""
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

    @property
    def boost_start_hour(self):
        """Boost starting at hour"""
        return self._data.get("tbh", -1)

    @property
    def boost_start_minute(self):
        """Boost starting at minute"""
        return self._data.get("tbm", -1)

    @property
    def boost_amount(self):
        """Boost amount of energy to add"""
        return self._data.get("tbk", -1)

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
        return True

    async def get_data(self):
        """Fetch data from MyEnergi"""
        response = await self._connection.get(f"/cgi-jstatus-Z{self._serialno}")
        data = response["zappi"][0]
        return data
