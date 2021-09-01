import asyncio
import logging
from sys import argv

from pymyenergi.connection import Connection
from pymyenergi.zappi import Zappi

logging.basicConfig()
logging.root.setLevel(logging.INFO)

user = argv[1]
password = argv[2]
zappi_serial = argv[3]


async def get_data() -> None:
    conn = Connection(user, password)
    zappi = Zappi(conn, zappi_serial)
    await zappi.refresh()
    print(f"Zappi S/N {zappi.serial_number} version {zappi.firmware_version}")
    print(
        f"Status: {zappi.status} Plug status: {zappi.plug_status} Locked: {zappi.locked}"
    )
    print(f"Priority: {zappi.priority}")
    print(f"Charge mode: {zappi.charge_mode}")
    print("")
    print(f"Lock when plugged in   : {zappi.lock_when_pluggedin}")
    print(f"Lock when unplugged    : {zappi.lock_when_unplugged}")
    print(f"Charge when locked     : {zappi.charge_when_locked}")
    print(f"Charge session allowed : {zappi.charge_session_allowed}")
    print(f"Charge added: {zappi.charge_added}")
    print("")
    print(f"CT 1 {zappi.ct1.name} {zappi.ct1.power}W")
    print(f"CT 2 {zappi.ct2.name} {zappi.ct2.power}W")
    print(f"CT 3 {zappi.ct3.name} {zappi.ct3.power}W")
    print(f"CT 4 {zappi.ct4.name} {zappi.ct4.power}W")
    print(f"CT 5 {zappi.ct5.name} {zappi.ct5.power}W")
    print(f"CT 6 {zappi.ct6.name} {zappi.ct6.power}W")
    print("")
    print(
        f"Supply voltage: {zappi.supply_voltage}V frequency: {zappi.supply_frequency}Hz"
    )
    print("Power:")
    print(f"  Grid      : {zappi.power_grid}W")
    print(f"  Generated : {zappi.power_generated}W")


loop = asyncio.get_event_loop()
loop.run_until_complete(get_data())
