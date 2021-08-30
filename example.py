import asyncio
import logging
from sys import argv

from pymyenergi.client import MyenergiClient
from pymyenergi.connection import Connection

logging.basicConfig()
logging.root.setLevel(logging.INFO)

user = argv[1]
password = argv[2]


async def zappis() -> None:
    conn = Connection(user, password)
    client = MyenergiClient(conn)

    zappis = await client.getDevices("zappi")
    for zappi in zappis:
        print(f"Zappi {zappi.serial_number} charge mode {zappi.charge_mode}")

    await conn.close()


loop = asyncio.get_event_loop()
loop.run_until_complete(zappis())
