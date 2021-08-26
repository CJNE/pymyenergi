from pymyenergi.connection import Connection

from .base_device import BaseDevice


class Eddi(BaseDevice):
    """Eddi Client for MyEnergi API."""

    def __init__(self, connection: Connection, serialno, data={}) -> None:
        super().__init__(connection, serialno, data)

    @property
    def kind(self):
        return "eddi"

    async def getData(self):
        response = await self._connection.get(f"/cgi-jstatus-H{self._serialno}")
        data = response["eddi"][0]
        return data

    async def stop(self):
        """Stop diverting"""
        await self._connection.get(f"/cgi-zappi-mode-E{self._serialno}-0-0-0-0000")
        return True
