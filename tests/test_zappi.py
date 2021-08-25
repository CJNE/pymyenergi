from pymyenergi.zappi import Zappi
import pytest


conn = {}


async def test_refresh(zappi_get_data_fixture):
    zappi = Zappi(conn, 16042300)
    await zappi.refresh()
    assert zappi.serial_number == 16042300
    assert zappi.charge_mode == 'Fast'
    assert zappi.charge_added == 4.2
