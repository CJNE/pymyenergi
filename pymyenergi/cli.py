import argparse
import asyncio
from pymyenergi.connection import Connection
from pymyenergi.client import MyEnergiClient
from pymyenergi.zappi import Zappi
from pymyenergi.eddi import Eddi
from pymyenergi.exceptions import WrongCredentials
import sys
import logging
import json
from getpass import getpass

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
            devices = await client.getDevices(args.kind)
            print(devices)
            # print(json.dumps(devices, indent=2))
    except WrongCredentials:
        sys.exit("Wrong username or password")
    else:
        await conn.close()


def cli():
    parser = argparse.ArgumentParser(description='MyEnergi CLI.')
    parser.add_argument('command', choices=['list'])
    parser.add_argument('-u', '--username', dest='username', default=None)
    parser.add_argument('-p', '--password', dest='password', default=None)
    parser.add_argument('-k', '--kind', dest='kind', default='all')
    parser.add_argument('-d', '--debug', dest='debug', action='store_true')

    args = parser.parse_args()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(args))
