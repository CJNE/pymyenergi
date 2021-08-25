from pymyenergi.connection import Connection

CHARGE_MODES = [None, 'Fast', 'Eco', 'Eco+', 'Stopped']
class Zappi:
    """Zappi Client for MyEnergi API."""

    def __init__(
        self,
        connection: Connection,
        serialno,
        data={}
    ) -> None:
        self._connection = connection
        self._serialno = serialno
        self._data = data

    @property
    def serial_number(self):
        return self._data.get('sno', None)

    @property
    def charge_mode(self):
        return CHARGE_MODES[self._data.get('zmo', 0)]


    async def refresh(self):
        self._data = await self._connection.get(f"/cgi-jstatus-Z{self._serialno}")
        return self._data

    async def getData(self, refresh=False):
        if refresh:
            await self.refresh()
        return self._data

    def __str__(self):
        return f"Zappi S/N: {self._serialno}"

    def __repr__(self):
        return self.__str__()
