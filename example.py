import asyncio
import logging
from sys import argv

from pymyenergi.client import MyenergiClient
from pymyenergi.connection import Connection

logging.basicConfig()
logging.root.setLevel(logging.INFO)

user = argv[1]
password = argv[2]


async def get_zappis() -> None:
    conn = Connection(user, password)
    client = MyenergiClient(conn)

    zappis = await client.get_devices("zappi")
    for zappi in zappis:
        print(f"Zappi {zappi.serial_number} charge mode {zappi.charge_mode}")


loop = asyncio.get_event_loop()
loop.run_until_complete(get_zappis())
