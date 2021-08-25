import asyncio
from pymyenergi.connection import Connection
from pymyenergi.client import MyEnergiClient
from sys import argv
import logging

logging.basicConfig()
logging.root.setLevel(logging.INFO)

user = argv[1]
password = argv[2]


async def zappis() -> None:
    conn = Connection(user, password)
    client = MyEnergiClient(conn)

    zappis = await client.getDevices('zappi')
    for zappi in zappis:
        print(f"Zappi {zappi.serial_number} charge mode {zappi.charge_mode}")

    await conn.close()

loop = asyncio.get_event_loop()
loop.run_until_complete(zappis())

