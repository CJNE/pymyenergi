import argparse
import asyncio
import configparser
import json
import logging
import os
import sys
from getpass import getpass

from pymyenergi.client import MyenergiClient
from pymyenergi.client import device_factory
from pymyenergi.connection import Connection
from pymyenergi.eddi import BOOST_TARGETS, EDDI_MODES, Eddi
from pymyenergi.exceptions import WrongCredentials
from pymyenergi.libbi import LIBBI_MODES, Libbi
from pymyenergi.zappi import CHARGE_MODES, Zappi

from . import EDDI
from . import HARVI
from . import LIBBI
from . import ZAPPI

logging.basicConfig()
logging.root.setLevel(logging.WARNING)


async def main(args):
    # handle --version first; no need to authenticate for this
    if args.version:
        ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
        version_file = open(os.path.join(ROOT_DIR, "VERSION"))
        version = version_file.read().strip()
        print(version)
        sys.exit(0)

    # also handle invalid commands
    # (no need to fetch data if we don't know what to do)
    if args.command not in [ZAPPI, EDDI, HARVI, LIBBI, 'list', 'overview']:
        sys.exit(
            "Dont know what to do, type myenergi --help form available commands"
        )

    username = args.username or input("Please enter your hub serial number: ")
    password = args.password or getpass(prompt="Password (apikey): ")
    if not args.skip_oauth:
        app_email = args.app_email or input(
            "App email (enter to skip; only needed for libbi): "
        )
        if app_email:
            app_password = args.app_password or getpass(prompt="App password: ")
        else:
            app_password = ""
    else:
        app_email = ""
        app_password = ""

    # establish connection
    conn = Connection(username, password, app_password, app_email)
    if app_email and app_password:
        await conn.discoverLocations()
        await conn.discoverHubs()

    # set logging to debug if requested
    if args.debug:
        logging.root.setLevel(logging.DEBUG)

    # create the client and execute the requested command
    client = MyenergiClient(conn)
    try:
        # display a list of devices
        if args.command == "list":
            devices = await client.get_devices(args.kind)
            for device in devices:
                if args.json:
                    print(json.dumps(device.data, indent=2))
                else:
                    print(device.show(True))
        # display an overview of all devices
        elif args.command == "overview":
            out = await client.show()
            print(out)
        else:
            if args.serial is None:
                # if no serial was provided, get the list of devices
                devices = await client.get_devices(args.command)
            else:
                # otherwise only get the specified device
                devices = [device_factory(conn, args.command, args.serial)]
                await devices[0].refresh()

            # iterate through the devices and execute the requested action
            for device in devices:
                if args.action == "show":
                    if args.json:
                        print(json.dumps(device.data, indent=2))
                    else:
                        print(device.show())

                elif args.action == "energy":
                    data = await device.energy_today(args.json)
                    if args.json:
                        print(json.dumps(data, indent=2))
                    else:
                        for key in data.keys():
                            print(f"{key}: {data[key]}kWh")

                elif args.action == "stop":
                    if args.command == ZAPPI and isinstance(device, Zappi):
                        await device.stop_charge()
                        print("Charging was stopped")

                elif args.action == "mode":
                    if args.command == ZAPPI and isinstance(device, Zappi):
                        if (
                            len(args.arg) < 1
                            or args.arg[0].capitalize() not in CHARGE_MODES
                        ):
                            modes = ", ".join(CHARGE_MODES)
                            sys.exit(f"A mode must be specifed, one of {modes}")
                        await device.set_charge_mode(args.arg[0])
                        print(f"Charging was set to {args.arg[0].capitalize()}")
                    elif args.command == EDDI and isinstance(device, Eddi):
                        if len(args.arg) < 1 or args.arg[0].capitalize() not in EDDI_MODES:
                            modes = ", ".join(EDDI_MODES)
                            sys.exit(f"A mode must be specifed, one of {modes}")
                        await device.set_operating_mode(args.arg[0])
                        print(f"Operating mode was set to {args.arg[0].capitalize()}")
                    elif args.command == LIBBI and isinstance(device, Libbi):
                        if len(args.arg) < 1 or args.arg[0].capitalize() not in LIBBI_MODES:
                            modes = ", ".join(LIBBI_MODES)
                            sys.exit(f"A mode must be specifed, one of {modes}")
                        await device.set_operating_mode(args.arg[0])
                        print(f"Operating mode was set to {args.arg[0].capitalize()}")

                elif args.action == "chargefromgrid":
                    if args.command == LIBBI and isinstance(device, Libbi):
                        if len(args.arg) < 1 or args.arg[0].capitalize() not in [
                            "True",
                            "False",
                        ]:
                            sys.exit("A mode must be specifed, one of true or false")
                        if (await device.set_charge_from_grid(args.arg[0])):
                            print(f"Charge from grid was set to {args.arg[0].capitalize()}")
                        else:
                            print(f"Could not set charge from grid")

                elif args.action == "chargetarget":
                    if args.command == LIBBI and isinstance(device, Libbi):
                        if len(args.arg) < 1 or not args.arg[0].isnumeric():
                            sys.exit("The charge target must be specified in Wh")
                        if (await device.set_charge_target(args.arg[0])):
                            print(f"Charge target was set to {args.arg[0]}Wh")
                        else:
                            print(f"Could not set charge target")

                elif args.action == 'gettariff':
                    if args.command == LIBBI and isinstance(device, Libbi):
                        tariff = await device.get_tariff()
                        print(f"Tariff information:")
                        print(json.dumps(tariff, indent=2))

                elif args.action == 'settariff':
                    if args.command == LIBBI and isinstance(device, Libbi):
                        if len(args.arg) < 1:
                            sys.exit("The new tariff must be specified")
                        if (await device.set_tariff(args.arg[0])):
                            print("Tariff was updated. New tariff information:")
                            print(device.showTariff())
                        else:
                            print("Failed to update tariff")

                elif args.action == "mingreen":
                    if args.command == ZAPPI and isinstance(device, Zappi):
                        if len(args.arg) < 1:
                            sys.exit("A minimum green level must be provided")
                        await device.set_minimum_green_level(args.arg[0])
                        print(f"Minimum green level was set to {args.arg[0]}")

                elif args.action == "boost":
                    if args.command == ZAPPI and isinstance(device, Zappi):
                        if (await device.start_boost(args.arg[0])):
                            print(f"Start boosting with {args.arg[0]}kWh")
                        else:
                            print("Could not start boost, charge mode must be Eco or Eco+")
                    elif args.command == EDDI and isinstance(device, Eddi):
                        if len(args.arg) < 2 or args.arg[0] not in BOOST_TARGETS:
                            targets = ", ".join(BOOST_TARGETS)
                            sys.exit(
                                f"A boost target and time must be specifed, one of {targets}"
                            )
                        if (await device.manual_boost(args.arg[0], args.arg[1])):
                            print(f"Start boosting {args.arg[0]} for {args.arg[1]} minutes")
                        else:
                            print("Could not start boost")

                elif args.action == "priority":
                    if (args.command in [EDDI, ZAPPI, LIBBI]) and isinstance(device, (Eddi, Zappi, Libbi)):
                        if len(args.arg) < 1:
                            sys.exit("A priority must be specifed, a number")
                        if (await device.set_priority(args.arg[0])):
                            print(f"Device priority was set to {args.arg[0]}")
                        else:
                            print("Could not set device priority")

                elif args.action == "heaterpriority":
                    if args.command == EDDI and isinstance(device, Eddi):
                        if len(args.arg) < 1 or args.arg[0] not in BOOST_TARGETS:
                            targets = ", ".join(BOOST_TARGETS)
                            sys.exit(
                                f"A priority target must be specifed, one of {targets}"
                            )
                        if await device.set_heater_priority(args.arg[0]):
                            print(f"Heater priority was set to {args.arg[0]}")
                        else:
                            print("Could not set heater priority")

                elif args.action == "smart-boost":
                    if args.command == ZAPPI and isinstance(device, Zappi):
                        if await device.start_smart_boost(args.arg[0], args.arg[1]):
                            print(
                                f"Start smart boosting with {args.arg[0]}kWh complete by {args.arg[1]}"
                            )
                        else:
                            print(
                                "Could not start smart boost, charge mode must be Eco or Eco+"
                            )
    except WrongCredentials:
        sys.exit("Wrong username or password")


def cli():
    config = configparser.ConfigParser()
    config["hub"] = {"serial": "", "password": "", "app_password": "", "app_email": ""}
    config.read([".myenergi.cfg", os.path.expanduser("~/.myenergi.cfg")])
    parser = argparse.ArgumentParser(prog="myenergi", description="myenergi CLI.")
    parser.add_argument(
        "-u",
        "--username",
        dest="username",
        default=config.get("hub", "serial"),
    )
    parser.add_argument(
        "-p",
        "--password",
        dest="password",
        default=config.get("hub", "password").strip('"'),
    )
    parser.add_argument(
        "-a",
        "--app_password",
        dest="app_password",
        default=config.get("hub", "app_password").strip('"'),
    )
    parser.add_argument(
        "-e",
        "--app_email",
        dest="app_email",
        default=config.get("hub", "app_email").strip('"'),
    )
    parser.add_argument(
        "--skip-oauth", dest="skip_oauth", action="store_true", default=False
    )
    parser.add_argument("-d", "--debug", dest="debug", action="store_true")
    parser.add_argument("-j", "--json", dest="json", action="store_true", default=False)
    parser.add_argument("--version", dest="version", action="store_true", default=False)
    subparsers = parser.add_subparsers(dest="command", help="sub-command help")
    subparser_list = subparsers.add_parser("list", help="list devices")
    subparser_list.add_argument("-k", "--kind", dest="kind", default="all")
    subparsers.add_parser("overview", help="show overview")
    subparser_zappi = subparsers.add_parser(
        ZAPPI, help="use zappi --help for available commands"
    )
    subparser_zappi.add_argument("-s", "--serial", dest="serial", default=None)
    subparser_zappi.add_argument(
        "action",
        choices=[
            "show",
            "energy",
            "stop",
            "mode",
            "boost",
            "smart-boost",
            "mingreen",
            "priority",
            "unlock",
        ],
    )
    subparser_zappi.add_argument("arg", nargs="*")
    subparser_eddi = subparsers.add_parser(
        EDDI, help="use eddi --help for available commands"
    )
    subparser_eddi.add_argument("-s", "--serial", dest="serial", default=None)
    subparser_eddi.add_argument(
        "action",
        choices=["show", "energy", "mode", "boost", "heaterpriority", "priority"],
    )
    subparser_eddi.add_argument("arg", nargs="*")

    subparser_harvi = subparsers.add_parser(
        HARVI, help="use harvi --help for available commands"
    )
    subparser_harvi.add_argument("-s", "--serial", dest="serial", default=None)
    subparser_harvi.add_argument("action", choices=["show"])
    subparser_harvi.add_argument("arg", nargs="*")

    subparser_libbi = subparsers.add_parser(
        LIBBI, help="use libbi --help for available commands"
    )
    subparser_libbi.add_argument("-s", "--serial", dest="serial", default=None)
    subparser_libbi.add_argument(
        "action",
        choices=[
            "show",
            "mode",
            "priority",
            "energy",
            "chargefromgrid",
            "chargetarget",
            "gettariff",
            "settariff"
        ],
    )
    subparser_libbi.add_argument("arg", nargs="*")

    args = parser.parse_args()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(args))
