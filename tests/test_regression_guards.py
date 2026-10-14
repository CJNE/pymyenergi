"""Regression checks for small, backwards-compatible myenergi fixes."""

from types import SimpleNamespace
from unittest.mock import AsyncMock

import httpx
import pytest

from pymyenergi import LIBBI
from pymyenergi.client import MyenergiClient
from pymyenergi.connection import Connection
from pymyenergi.zappi import Zappi


@pytest.mark.asyncio
async def test_director_connection_failure_is_not_masked_by_typeerror():
    transport = AsyncMock()
    transport.get.side_effect = httpx.ConnectError("director offline")
    connection = Connection("hub", "api-key", asyncClient=transport)

    with pytest.raises(httpx.ConnectError, match="director offline"):
        await connection.get("/cgi-jstatus-*")

    transport.request.assert_not_awaited()


@pytest.mark.parametrize(
    "phase,code,setting",
    [
        ("1", 0, "SINGLE_PHASE"),
        ("3", 1, "THREE_PHASE"),
        ("auto", 2, "AUTO"),
    ],
)
@pytest.mark.asyncio
async def test_setting_phase_updates_actual_local_field(phase, code, setting):
    connection = AsyncMock()
    zappi = Zappi(connection, 16042300, {"phaseSetting": "SINGLE_PHASE"})

    assert await zappi.set_phase_setting(phase) is True

    connection.get.assert_awaited_once_with(
        f"/cgi-zappi-phase-setting-Z16042300-{code}"
    )
    assert zappi.data["phaseSetting"] == setting
    assert zappi.num_phases == phase


@pytest.mark.parametrize("invalid", ["2", "3-phase", None])
@pytest.mark.asyncio
async def test_invalid_phase_fails_before_api_command(invalid):
    connection = AsyncMock()
    zappi = Zappi(connection, 16042300, {"phaseSetting": "SINGLE_PHASE"})

    with pytest.raises(ValueError, match="Phase setting"):
        await zappi.set_phase_setting(invalid)

    connection.get.assert_not_awaited()
    assert zappi.num_phases == "1"


@pytest.mark.asyncio
async def test_failed_phase_command_preserves_previous_local_setting():
    connection = AsyncMock()
    connection.get.side_effect = httpx.ConnectError("connection lost")
    zappi = Zappi(connection, 16042300, {"phaseSetting": "SINGLE_PHASE"})

    with pytest.raises(httpx.ConnectError):
        await zappi.set_phase_setting("3")

    assert zappi.num_phases == "1"


def test_libbi_fallback_is_selected_for_history_totals():
    client = MyenergiClient(AsyncMock())
    client.devices = {
        123: SimpleNamespace(
            kind=LIBBI,
            is_vhub_enabled=False,
            history_data={
                "generated": 1.5,
                "grid_import": 2.0,
                "grid_export": 3.0,
                "device_green": 4.0,
            },
        )
    }

    client._calculate_history_totals()

    assert client.energy_generated == 1.5
    assert client.energy_imported == 2.0
    assert client.energy_exported == 3.0
    assert client.energy_green == 4.0
