"""Global fixtures"""

import json
from unittest.mock import patch

import pytest


def load_fixture_json(name):
    with open(f"tests/fixtures/{name}.json") as json_file:
        data = json.load(json_file)
        return data


# This fixture, when used, will result in calls to async_fetch_data to return None. To have the call
# return a value, we would add the `return_value=<VALUE_TO_RETURN>` parameter to the patch call.
@pytest.fixture(name="bypass_client_fetch_data")
def bypass_client_fetch_data_fixture():
    """Skip calls to get data from API."""
    with patch("pymyenergi.client.MyenergiClient.fetch_data"):
        yield


@pytest.fixture(name="error_on_client_fetch_data")
def error_client_fetch_data_fixture():
    """Simulate error when retrieving data from API."""
    with patch("pymyenergi.client.MyenergiClient.fetch_data", side_effect=Exception):
        yield


@pytest.fixture(name="client_fetch_data_fixture")
def client_fetch_data_fixture():
    """Mock data from client.fetch_data()"""
    with patch(
        "pymyenergi.client.MyenergiClient.fetch_data",
        return_value=load_fixture_json("client"),
    ):
        yield


@pytest.fixture(name="client_1p_zappi_harvi_solar_battery_fixture")
def client_1p_zappi_harvi_solar_battery_fixture():
    """Mock data from client.fetch_data()"""
    with patch(
        "pymyenergi.client.MyenergiClient.fetch_data",
        return_value=load_fixture_json("client_1p_zappi_harvi_solar_battery"),
    ):
        yield


@pytest.fixture(name="zappi_fetch_data_fixture")
def zappi_fetch_data_fixture():
    """Mock data from client.fetch_data()"""
    with patch(
        "pymyenergi.zappi.Zappi.fetch_data",
        return_value=load_fixture_json("zappi"),
    ):
        yield


@pytest.fixture(name="zappi_fetch_boost_data_fixture")
def zappi_fetch_boost_data_fixture():
    """Mock data from client.fetch_data()"""
    with patch(
        "pymyenergi.zappi.Zappi.fetch_boost_data",
        return_value=load_fixture_json("zappi"),
    ):
        yield


@pytest.fixture(name="eddi_fetch_data_fixture")
def eddi_fetch_data_fixture():
    """Mock data from client.fetch_data()"""
    with patch(
        "pymyenergi.eddi.Eddi.fetch_data", return_value=load_fixture_json("eddi")
    ):
        yield


@pytest.fixture(name="harvi_fetch_data_fixture")
def harvi_fetch_data_fixture():
    """Mock data from client.fetch_data()"""
    with patch(
        "pymyenergi.harvi.Harvi.fetch_data", return_value=load_fixture_json("harvi")
    ):
        yield


@pytest.fixture(name="libbi_fetch_data_fixture")
def libbi_fetch_data_fixture():
    """Mock data from client.fetch_data()"""
    with patch(
        "pymyenergi.libbi.Libbi.fetch_data", return_value=load_fixture_json("libbi")
    ):
        yield


# @pytest.fixture
# def eddi_connection_mock():
#    with patch("pymyenergi.eddi.Eddi._connection"):
#        yield AsyncMock
