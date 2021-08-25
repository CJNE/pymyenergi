from pymyenergi.connection import Connection


class Eddi:
    """Eddi Client for MyEnergi API."""

    def __init__(self, connection: Connection, serialno, data={}) -> None:
        self._connection = connection
        self._serialno = serialno
        self._data = data

    async def refresh(self):
        self._data = await self._connection.get(f"/cgi-jstatus-E{self._serialno}")
        return self._data

    async def getData(self, refresh=False):
        if refresh:
            await self.refresh()
        return self._data

    def __str__(self):
        return f"Eddi S/N: {self._serialno}"

    def __repr__(self):
        return self.__str__()
