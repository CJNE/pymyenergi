import argparse
import asyncio
import logging
import sys
from getpass import getpass

from pymyenergi.client import device_factory
from pymyenergi.client import MyEnergiClient
from pymyenergi.connection import Connection
from pymyenergi.exceptions import WrongCredentials

logging.basicConfig()
logging.root.setLevel(logging.WARNING)


async def main(args):
    username = args.username or input("Please enter your hub serial number: ")
    password = args.password or getpass()
    conn = Connection(username, password)
    if args.debug:
        logging.root.setLevel(logging.DEBUG)
    try:
        if args.command == "list":
            client = MyEnergiClient(conn)
            devices = await client.get_devices(args.kind)
            print(devices)
            # print(json.dumps(devices, indent=2))
        if args.serial is not None and args.kind != "all":
            device = device_factory(conn, args.kind, args.serial)
            if args.kind in ["zappi", "eddi"] and args.command == "stop":
                await device.stop()
                print("Charging was stopped")
            if args.kind == "zappi" and args.command in ["fast", "eco", "eco+"]:
                await device.set_mode(args.command)
                print(f"Charging was set to {args.command.capitalize()}")
            if args.kind == "zappi" and args.command in ["fast", "eco", "eco+"]:
                await device.set_mode(args.command)
                print(f"Charging was set to {args.command.capitalize()}")

        else:
            sys.exit("A serial number is needed")
    except WrongCredentials:
        sys.exit("Wrong username or password")
    finally:
        await conn.close()


def cli():
    parser = argparse.ArgumentParser(description="MyEnergi CLI.")
    parser.add_argument("command", choices=["list", "stop", "eco", "eco+", "fast"])
    parser.add_argument("-u", "--username", dest="username", default=None)
    parser.add_argument("-p", "--password", dest="password", default=None)
    parser.add_argument("-k", "--kind", dest="kind", default="all")
    parser.add_argument("-s", "--serial", dest="serial", default=None)
    parser.add_argument("-d", "--debug", dest="debug", action="store_true")

    args = parser.parse_args()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(args))
