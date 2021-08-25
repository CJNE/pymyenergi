# pymyenergi
An async python library for MyEnergi API

This is a very early release, things are changing rapidly so use at your own risk!

*NOTE:* This work is not officially supported by MyEnergi and functionality can stop working at any time without warning

## Installation

The easiest method is to install using pip3/pip (venv is also a good idea)
```
pip install pymyenergi
```

to update to the latest version

```
pip install pymyenergi -U
```

Setup will add a cli under the name myenergicli, see below for usage


## CLI usage

A simple cli is provided with this library.

If no username or password is supplied as input arguments you will be prompted. 
```
usage: cli.py [-h] [-u USERNAME] [-p PASSWORD] [-k KIND] [-d] {list}

MyEnergi CLI.

positional arguments:
  {list}

optional arguments:
  -h, --help            show this help message and exit
  -u USERNAME, --username USERNAME
  -p PASSWORD, --password PASSWORD
  -k KIND, --kind KIND
  -d, --debug
```

## Library usage

Install pymyenergi using pip (requires python > 3.6)


### Example client usage
```
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
```

## Credits
[twonk](https://github.com/twonk/MyEnergi-App-Api) for documenting the unofficial API
