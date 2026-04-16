#! /usr/bin/env python3
from pymyenergi.cli import cli
import asyncio

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
cli()

