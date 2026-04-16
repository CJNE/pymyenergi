import pytest
import json
from unittest.mock import AsyncMock

from pymyenergi.libbi import Libbi

pytestmark = pytest.mark.asyncio


class MockLibbiConnection:
    def __init__(self, app_email="user@example.com", app_password="password"):
        self.app_email = app_email
        self.app_password = app_password
        self.post = AsyncMock(return_value={})


async def test_refresh(libbi_fetch_data_fixture):
    """Test Libbi data"""
    libbi = Libbi({}, 24047164)
    await libbi.refresh()
    assert libbi.serial_number == 24047164


async def test_set_tariff_accepts_all_days_once():
    """Tariff should validate when all days are represented exactly once."""
    conn = MockLibbiConnection()
    libbi = Libbi(conn, 24047164)
    tariff = [
        {
            "default_price": 15.0,
            "days": [0, 1, 2],
            "bands": [{"from": 120, "to": 300, "price": 1.0}],
        },
        {
            "default_price": 15.0,
            "days": [3, 4, 5, 6],
            "bands": [{"from": 0, "to": 120, "price": 1.0}],
        },
    ]

    assert await libbi.set_tariff(json.dumps(tariff)) is True
    conn.post.assert_awaited_once()


async def test_set_tariff_rejects_missing_days():
    """Tariff should fail validation when not all days are present."""
    conn = MockLibbiConnection()
    libbi = Libbi(conn, 24047164)
    tariff = [
        {
            "default_price": 15.0,
            "days": [0, 1, 2],
            "bands": [{"from": 120, "to": 300, "price": 1.0}],
        },
    ]

    assert await libbi.set_tariff(json.dumps(tariff)) is False


async def test_set_tariff_rejects_duplicate_days():
    """Tariff should fail validation when a day appears more than once."""
    conn = MockLibbiConnection()
    libbi = Libbi(conn, 24047164)
    tariff = [
        {
            "default_price": 15.0,
            "days": [0, 1, 2],
            "bands": [{"from": 120, "to": 300, "price": 1.0}],
        },
        {
            "default_price": 15.0,
            "days": [2, 3, 4, 5, 6],
            "bands": [{"from": 0, "to": 120, "price": 1.0}],
        },
    ]

    assert await libbi.set_tariff(json.dumps(tariff)) is False


async def test_set_tariff_translates_to_remote_api_format():
    """Tariff bands should be translated to full-day remote API tariff slots."""
    conn = MockLibbiConnection()
    libbi = Libbi(conn, 24047164)
    libbi._extra_data["energy_setup_id"] = 12345
    tariff = [
        {
            "default_price": 15.0,
            "days": [0, 1, 2],
            "bands": [{"from": 120, "to": 300, "price": 1.0}],
        },
        {
            "default_price": 15.0,
            "days": [3, 4, 5, 6],
            "bands": [{"from": 0, "to": 120, "price": 1.0}],
        },
    ]

    ok = await libbi.set_tariff(json.dumps(tariff))

    assert ok is True
    assert libbi._extra_data["energy_setup"] == [
        {
            "days": [0, 1, 2],
            "tariffs": [
                {"fromMinutes": 0, "toMinutes": 120, "price": 15.0},
                {"fromMinutes": 120, "toMinutes": 300, "price": 1.0},
                {"fromMinutes": 300, "toMinutes": 1440, "price": 15.0},
            ],
            "energySetupId": 12345,
        },
        {
            "days": [3, 4, 5, 6],
            "tariffs": [
                {"fromMinutes": 0, "toMinutes": 120, "price": 1.0},
                {"fromMinutes": 120, "toMinutes": 1440, "price": 15.0},
            ],
            "energySetupId": 12345,
        },
    ]
    conn.post.assert_awaited_once_with(
        "/api/EnergySetup/SaveDualTariffEnergyPrices",
        data=libbi._extra_data["energy_setup"],
        oauth=True,
    )


async def test_set_tariff_requires_app_credentials():
    """Tariff update should fail when app credentials are not configured."""
    conn = MockLibbiConnection(app_email=None, app_password=None)
    libbi = Libbi(conn, 24047164)
    tariff = [
        {
            "default_price": 15.0,
            "days": [0, 1, 2],
            "bands": [{"from": 120, "to": 300, "price": 1.0}],
        },
        {
            "default_price": 15.0,
            "days": [3, 4, 5, 6],
            "bands": [{"from": 0, "to": 120, "price": 1.0}],
        },
    ]

    assert await libbi.set_tariff(json.dumps(tariff)) is False
    conn.post.assert_not_awaited()


async def test_set_tariff_no_default_price_with_full_coverage():
    """Tariff without default_price should be accepted when bands cover the full day."""
    conn = MockLibbiConnection()
    libbi = Libbi(conn, 24047164)
    tariff = [
        {
            "days": [0, 1, 2],
            "bands": [
                {"from": 0, "to": 720, "price": 15.0},
                {"from": 720, "to": 1440, "price": 1.0},
            ],
        },
        {
            "days": [3, 4, 5, 6],
            "bands": [
                {"from": 0, "to": 1440, "price": 5.0},
            ],
        },
    ]

    assert await libbi.set_tariff(json.dumps(tariff)) is True
    conn.post.assert_awaited_once()


async def test_set_tariff_no_default_price_with_gap_fails():
    """Tariff without default_price should fail when bands leave a gap."""
    conn = MockLibbiConnection()
    libbi = Libbi(conn, 24047164)
    tariff = [
        {
            "days": [0, 1, 2],
            "bands": [
                {"from": 0, "to": 720, "price": 15.0},
                # gap: 720-1440 is not covered
            ],
        },
        {
            "days": [3, 4, 5, 6],
            "bands": [
                {"from": 0, "to": 1440, "price": 5.0},
            ],
        },
    ]

    assert await libbi.set_tariff(json.dumps(tariff)) is False
    conn.post.assert_not_awaited()


async def test_get_tariff_condenses_to_default_price():
    """get_tariff should identify the most-used price as default and omit its bands."""
    conn = MockLibbiConnection()
    libbi = Libbi(conn, 24047164)
    # Simulate cached energy_setup (remote API format).
    libbi._extra_data["energy_setup"] = [
        {
            "days": [0, 1, 2],
            "tariffs": [
                {"fromMinutes": 0, "toMinutes": 120, "price": 15.0},
                {"fromMinutes": 120, "toMinutes": 300, "price": 1.0},
                {"fromMinutes": 300, "toMinutes": 1440, "price": 15.0},
            ],
        },
        {
            "days": [3, 4, 5, 6],
            "tariffs": [
                {"fromMinutes": 0, "toMinutes": 120, "price": 1.0},
                {"fromMinutes": 120, "toMinutes": 1440, "price": 15.0},
            ],
        },
    ]

    result = await libbi.get_tariff()

    assert result == [
        {
            "days": [0, 1, 2],
            "default_price": 15.0,
            "bands": [{"from": 120, "to": 300, "price": 1.0}],
        },
        {
            "days": [3, 4, 5, 6],
            "default_price": 15.0,
            "bands": [{"from": 0, "to": 120, "price": 1.0}],
        },
    ]
