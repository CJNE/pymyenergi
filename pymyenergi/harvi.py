from pymyenergi.connection import Connection

from .base_device import BaseDevice


class Harvi(BaseDevice):
    """Zappi Client for MyEnergi API."""

    def __init__(self, connection: Connection, serialno, data={}) -> None:
        super().__init__(connection, serialno, data)

    @property
    def kind(self):
        return "eddi"

    async def getData(self):
        response = await self._connection.get(f"/cgi-jstatus-H{self._serialno}")
        data = response["harvi"][0]
        return data
