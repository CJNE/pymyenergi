from pymyenergi.connection import Connection

from .base_device import BaseDevice


class Eddi(BaseDevice):
    """Eddi Client for MyEnergi API."""

    def __init__(self, connection: Connection, serialno, data={}) -> None:
        super().__init__(connection, serialno, data)

    async def fetch_data(self):
        response = await self._connection.get(f"/cgi-jstatus-H{self._serialno}")
        data = response["eddi"][0]
        return data

    @property
    def kind(self):
        return "eddi"

    async def stop(self):
        """Stop diverting"""
        await self._connection.get(f"/cgi-zappi-mode-E{self._serialno}-0-0-0-0000")
        return True

    def show(self):
        """Returns a string with all data in human readable format"""
        ret = ""
        ret = ret + f"Eddi S/N {self.serial_number} version {self.firmware_version}\n"
        ret = ret + f"Priority: {self.priority}\n"
        ret = ret + f"CT 1 {self.ct1.name} {self.ct1.power}W\n"
        ret = ret + f"CT 2 {self.ct2.name} {self.ct2.power}W\n"
        ret = ret + f"CT 3 {self.ct3.name} {self.ct3.power}W\n"
        return ret
