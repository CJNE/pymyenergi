"""Regressions for cache consistency and discovery failures; no live devices."""

from unittest.mock import AsyncMock

import httpx
import pytest

from pymyenergi.connection import Connection
from pymyenergi.exceptions import TimeoutException
from pymyenergi.zappi import Zappi


@pytest.mark.asyncio
@pytest.mark.parametrize("initial", ["SINGLE_PHASE", "THREE_PHASE", "AUTO"])
@pytest.mark.parametrize(
    "phase,code,state",
    [("1", 0, "SINGLE_PHASE"), ("3", 1, "THREE_PHASE"), ("auto", 2, "AUTO")],
)
async def test_phase_cache_matches_requested_setting(initial, phase, code, state):
    connection = AsyncMock(spec=Connection)
    device = Zappi(connection, 123, {"phaseSetting": initial})
    assert await device.set_phase_setting(phase) is True
    connection.get.assert_awaited_once_with(f"/cgi-zappi-phase-setting-Z123-{code}")
    assert device.data == {"phaseSetting": state}
    assert device.num_phases == phase


@pytest.mark.asyncio
@pytest.mark.parametrize("phase", [None, "", "2", "AUTO", 1, 3, True, [], {}])
async def test_invalid_phases_never_reach_the_network(phase):
    connection = AsyncMock(spec=Connection)
    device = Zappi(connection, 123, {"phaseSetting": "SINGLE_PHASE"})
    with pytest.raises(ValueError):
        await device.set_phase_setting(phase)
    connection.get.assert_not_awaited()
    assert device.data == {"phaseSetting": "SINGLE_PHASE"}


@pytest.mark.asyncio
@pytest.mark.parametrize("phase", ["1", "3", "auto"])
async def test_failed_phase_command_preserves_previous_cache(phase):
    connection = AsyncMock(spec=Connection)
    failure = RuntimeError("simulated request failure")
    connection.get.side_effect = failure
    device = Zappi(connection, 123, {"phaseSetting": "THREE_PHASE"})
    with pytest.raises(RuntimeError) as caught:
        await device.set_phase_setting(phase)
    assert caught.value is failure
    assert device.data == {"phaseSetting": "THREE_PHASE"}


@pytest.mark.asyncio
@pytest.mark.parametrize("initial", [0, 1, 2, 3, 4])
async def test_stop_updates_mode_but_does_not_invent_physical_status(initial):
    connection = AsyncMock(spec=Connection)
    device = Zappi(connection, 123, {"zmo": initial, "sta": 3})
    assert await device.stop_charge() is True
    connection.get.assert_awaited_once_with("/cgi-zappi-mode-Z123-4-0-0-0000")
    assert device.charge_mode == "Stopped"
    assert device.status == "Charging"  # Last measured status, not confirmation.


@pytest.mark.asyncio
async def test_failed_stop_does_not_change_mode():
    connection = AsyncMock(spec=Connection)
    connection.get.side_effect = RuntimeError("simulated request failure")
    device = Zappi(connection, 123, {"zmo": 1})
    with pytest.raises(RuntimeError):
        await device.stop_charge()
    assert device.charge_mode == "Fast"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "failure_type",
    [httpx.ConnectTimeout, httpx.ReadTimeout, httpx.WriteTimeout, httpx.PoolTimeout],
)
async def test_discovery_timeout_preserves_its_cause(failure_type):
    transport = AsyncMock(spec=httpx.AsyncClient)
    failure = failure_type("simulated timeout")
    transport.get.side_effect = failure
    connection = Connection("hub", "key", asyncClient=transport)
    with pytest.raises(TimeoutException) as caught:
        await connection.get("/cgi-jstatus-Z123")
    assert caught.value.__cause__ is failure
    assert connection.do_query_asn is True
    assert connection.base_url is None
    transport.request.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize("failure_type", [httpx.ConnectError, RuntimeError])
async def test_discovery_error_is_not_replaced_by_none_plus_url(failure_type):
    transport = AsyncMock(spec=httpx.AsyncClient)
    failure = failure_type("simulated failure")
    transport.get.side_effect = failure
    connection = Connection("hub", "key", asyncClient=transport)
    with pytest.raises(failure_type) as caught:
        await connection.get("/cgi-jstatus-Z123")
    assert caught.value is failure
    transport.request.assert_not_awaited()
    assert connection.do_query_asn is True


@pytest.mark.asyncio
async def test_caller_can_retry_after_failed_discovery():
    transport = AsyncMock(spec=httpx.AsyncClient)
    headers = {"X_MYENERGI-asn": "s18.myenergi.net"}
    transport.get.side_effect = [
        httpx.ReadTimeout("simulated timeout"),
        httpx.Response(200, headers=headers, json={}),
    ]
    transport.request.return_value = httpx.Response(
        200, headers=headers, json={"ok": True}
    )
    connection = Connection("hub", "key", asyncClient=transport)
    with pytest.raises(TimeoutException):
        await connection.get("/cgi-jstatus-Z123")
    assert await connection.get("/cgi-jstatus-Z123") == {"ok": True}
    assert transport.get.await_count == 2
    assert transport.request.await_count == 1
    assert connection.do_query_asn is False
