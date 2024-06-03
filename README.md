# pymyenergi

An async Python library for myenergi API

This is a very early release, things are changing rapidly so use at your own risk!

> [!IMPORTANT]
> This work is not officially supported by myenergi and functionality can stop working at any time without warning

## Installation

The easiest method is to install using pip (`pip`/`pip3`):

```bash
pip install pymyenergi
```

Installing within a [Python virtual environment](https://docs.python.org/3/library/venv.html) is often a good idea:

```bash
python -m venv .venv
source .venv/bin/activate
pip install pymyenergi
```

To update to the latest version:

```bash
pip install pymyenergi -U
```

Setup will add a CLI under the name `myenergicli`. See below for usage.

## CLI

A simple CLI is provided with this library.

If no `username`, `password`, `app_email` or `app_password` is supplied as input arguments, and no configuration file is found, you will be prompted for credentials.

Configuration file will be searched for in `./.myenergi.cfg` and `~/.myenergi.cfg`.

### Example configuration file

```ini
[hub]
serial=12345678
password=your-password
app_email=myemail@email.com
app_password=your-app-password
```

### CLI usage

```
usage: myenergi [-h] [-u USERNAME] [-p PASSWORD] [-e APP_EMAIL] [-a APP_PASSWORD] [-d] [-j] [--skip-oauth]
                {list,overview,zappi,eddi,harvi,libbi} ...

myenergi CLI.

positional arguments:
  {list,overview,zappi,eddi,harvi,libbi}
                        sub-command help
    list                list devices
    overview            show overview
    zappi               use zappi --help for available commands
    eddi                use eddi --help for available commands
    harvi               use harvi --help for available commands
    libbi               use libbi --help for available commands

optional arguments:
  -h, --help            show this help message and exit
  -u USERNAME, --username USERNAME
  -p PASSWORD, --password PASSWORD
  -e APP_EMAIL, --app_email APP_EMAIL
  -a APP_PASSWORD, --app_password APP_PASSWORD
  -d, --debug
  -j, --json
```

## Library usage

Install pymyenergi using pip (requires Python > 3.6)

### Example library usage

```python
import asyncio
from pymyenergi.connection import Connection
from pymyenergi.client import MyenergiClient
from sys import argv
import logging

logging.basicConfig()
logging.root.setLevel(logging.INFO)

user, password = argv

async def zappis() -> None:
    conn = Connection(user, password)
    client = MyenergiClient(conn)

    zappis = await client.getDevices('zappi')
    for zappi in zappis:
        print(f"Zappi {zappi.serial_number} charge mode {zappi.charge_mode}")

loop = asyncio.get_event_loop()
loop.run_until_complete(zappis())
```

### Example library usage - Zappi

```python
import asyncio
from pymyenergi.connection import Connection
from pymyenergi.zappi import Zappi
from sys import argv
import logging

logging.basicConfig()
logging.root.setLevel(logging.INFO)

user, password, zappi_serial = argv


async def get_data() -> None:
    conn = Connection(user, password)
    zappi = Zappi(conn, zappi_serial)
    await zappi.refresh()
    print(f"Zappi S/N {zappi.serial_number} version {zappi.firmware_version}")
    print(f"Status: {zappi.status} Plug status: {zappi.plug_status} Locked: {zappi.locked}")
    print(f"Priority: {zappi.priority}")
    print(f"Charge mode: {zappi.charge_mode} {zappi.num_phases} phase")
    print()
    print(f"Lock when plugged in   : {zappi.lock_when_pluggedin}")
    print(f"Lock when unplugged    : {zappi.lock_when_unplugged}")
    print(f"Charge when locked     : {zappi.charge_when_locked}")
    print(f"Charge session allowed : {zappi.charge_session_allowed}")
    print(f"Charge added: {zappi.charge_added}")
    print()
    print(f"CT 1 {zappi.ct1.name} {zappi.ct1.power}W")
    print(f"CT 2 {zappi.ct2.name} {zappi.ct2.power}W")
    print(f"CT 3 {zappi.ct3.name} {zappi.ct3.power}W")
    print(f"CT 4 {zappi.ct4.name} {zappi.ct4.power}W")
    print(f"CT 5 {zappi.ct5.name} {zappi.ct5.power}W")
    print(f"CT 6 {zappi.ct6.name} {zappi.ct6.power}W")
    print()
    print(f"Supply voltage: {zappi.supply_voltage}V frequency: {zappi.supply_frequency}Hz")
    print("Power:")
    print(f"  Grid      : {zappi.power_grid}W")
    print(f"  Generated : {zappi.power_generated}W")
    print()
    # print(f"      Boost start at {zappi.boost_start_hour}:{zappi.boost_start_minute} add {zappi.boost_amount}kWh")
    print(f"Smart Boost start at {zappi.smart_boost_start_hour}:{zappi.smart_boost_start_minute} add {zappi.smart_boost_amount}kWh")

loop = asyncio.get_event_loop()
loop.run_until_complete(get_data())
```

## Libbi support

Currently supported features:

- Reads a few values such as State of Charge, DCPV CT
- Battery in and out energy
- Gets and sets the current operating mode (normal/stopped/export)
- Change priority of Libbi
- Enable/Disable charging from the grid
- Set charge target (in Wh)


## CLI examples:

```bash
myenergi libbi show
myenergi libbi mode normal
myenergi libbi priority 1
myenergi libbi energy
myenergi libbi chargefromgrid false
myenergi libbi chargetarget 10200
```

## Credits

[twonk](https://github.com/twonk/MyEnergi-App-Api) for documenting the unofficial API
