import argparse
import asyncio
import configparser
import json
import logging
import os
import sys
from getpass import getpass

from pymyenergi.client import device_factory
from pymyenergi.client import MyenergiClient
from pymyenergi.connection import Connection
from pymyenergi.exceptions import WrongCredentials
from pymyenergi.zappi import CHARGE_MODES

from . import HARVI

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
            client = MyenergiClient(conn)
            devices = await client.get_devices(args.kind)
            for device in devices:
                if args.json:
                    print(json.dumps(device.data, indent=2))
                else:
                    print(device.show())
        elif args.command == "overview":
            client = MyenergiClient(conn)
            devices = await client.get_devices()
            await client.refresh_history_today()
            out = f"Site name: {client.site_name}\n"
            out = out + f"Home consumption : {client.consumption_home}W\n"
            out = out + f"Power grid       : {client.power_grid}W\n"
            out = out + f"Power generation : {client.power_generation}W\n"
            out = out + f"Power EV charge  : {client.power_charging}W\n"
            out = out + f"Power battery    : {client.power_battery}W\n"
            out = out + f"Energy imported  : {client.energy_imported}kWh\n"
            out = out + f"Energy exported  : {client.energy_exported}kWh\n"
            out = out + f"Energy generated : {client.energy_generated}kWh\n"
            out = out + f"Energy green     : {client.energy_green}kWh\n"
            out = out + "Devices:\n"
            for device in devices:
                out = out + f"\t{device.kind.capitalize()}: {device.name}"
                if device.kind != HARVI:
                    out = out + f"\t{device.energy_total}kWh today\n"
                    for key in device.ct_keys:
                        out = (
                            out
                            + f"\t{key} {device.history_data.get(key, 0)}kWh today\n"
                        )
                    out = out + "\n"
                else:
                    out = out + "\n"
            print(out)
        elif args.command in ["zappi", "eddi", "harvi"]:
            device = device_factory(conn, args.command, args.serial)
            await device.refresh()
            if args.action == "show":
                if args.json:
                    print(json.dumps(device.data, indent=2))
                else:
                    print(device.show())
            elif args.action == "energy":
                data = await device.energy_today()
                if args.json:
                    print(json.dumps(data, indent=2))
                else:
                    for key in data.keys():
                        print(f"{key}: {(data[key]/1000):.2f}kWh")
            elif args.action == "stop" and args.command == "zappi":
                await device.stop_charge()
                print("Charging was stopped")
            elif args.action == "mode" and args.command == "zappi":
                if len(args.arg) < 1 or args.arg[0].capitalize() not in CHARGE_MODES:
                    modes = ", ".join(CHARGE_MODES)
                    sys.exit(f"A mode must be specifed, one of {modes}")
                await device.set_charge_mode(args.arg[0])
                print(f"Charging was set to {args.arg[0].capitalize()}")
            elif args.action == "mingreen" and args.command == "zappi":
                if len(args.arg) < 1:
                    sys.exit("A minimum green level must be provided")
                await device.set_minimum_green_level(args.arg[0])
                print(f"Minimum green level was set to {args.arg[0]}")
            elif args.action == "boost" and args.command == "zappi":
                await device.start_boost(args.arg[0])
                print(f"Start boosting with {args.arg[0]}kWh")
            elif args.action == "smart-boost" and args.command == "zappi":
                await device.start_smart_boost(args.arg[0], args.arg[1])
                print(
                    f"Start smart boosting with {args.arg[0]}kWh complete by {args.arg[1]}"
                )
        else:
            sys.exit(
                "Dont know what to do, type myenergi --help form available commands"
            )
    except WrongCredentials:
        sys.exit("Wrong username or password")


def cli():
    config = configparser.ConfigParser()
    config["hub"] = {"serial": "", "password": ""}
    config.read([".myenergi.cfg", os.path.expanduser("~/.myenergi.cfg")])
    parser = argparse.ArgumentParser(prog="myenergi", description="myenergi CLI.")
    parser.add_argument(
        "-u",
        "--username",
        dest="username",
        default=config.get("hub", "serial"),
    )
    parser.add_argument(
        "-p", "--password", dest="password", default=config.get("hub", "password")
    )
    parser.add_argument("-d", "--debug", dest="debug", action="store_true")
    parser.add_argument("-j", "--json", dest="json", action="store_true", default=False)
    subparsers = parser.add_subparsers(dest="command", help="sub-command help")
    subparser_list = subparsers.add_parser("list", help="list devices")
    subparser_list.add_argument("-k", "--kind", dest="kind", default="all")
    subparsers.add_parser("overview", help="show overview")
    subparser_zappi = subparsers.add_parser(
        "zappi", help="use zappi --help for available commands"
    )
    subparser_zappi.add_argument("serial", default=None)
    subparser_zappi.add_argument(
        "action",
        choices=["show", "energy", "stop", "mode", "boost", "smart-boost", "mingreen"],
    )
    subparser_zappi.add_argument("arg", nargs="*")
    subparser_eddi = subparsers.add_parser(
        "eddi", help="use eddi --help for available commands"
    )
    subparser_eddi.add_argument("serial", default=None)
    subparser_eddi.add_argument("action", choices=["show", "energy"])
    subparser_eddi.add_argument("arg", nargs="*")

    subparser_harvi = subparsers.add_parser(
        "harvi", help="use harvi --help for available commands"
    )
    subparser_harvi.add_argument("serial", default=None)
    subparser_harvi.add_argument("action", choices=["show"])
    subparser_harvi.add_argument("arg", nargs="*")

    args = parser.parse_args()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(args))
