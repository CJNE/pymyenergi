"""Global fixtures"""
import json
from unittest.mock import patch

import pytest


def load_fixture_json(name):
    with open(f"tests/fixtures/{name}.json") as json_file:
        data = json.load(json_file)
        return data


# This fixture, when used, will result in calls to async_get_data to return None. To have the call
# return a value, we would add the `return_value=<VALUE_TO_RETURN>` parameter to the patch call.
@pytest.fixture(name="bypass_client_get_data")
def bypass_client_get_data_fixture():
    """Skip calls to get data from API."""
    with patch("pymyenergi.client.MyEnergiClient.getData"):
        yield


@pytest.fixture(name="error_on_client_get_data")
def error_client_get_data_fixture():
    """Simulate error when retrieving data from API."""
    with patch("pymyenergi.client.MyEnergiClient.getData", side_effect=Exception):
        yield


@pytest.fixture(name="client_get_data_fixture")
def client_get_data_fixture():
    """Mock data from client.getData()"""
    with patch(
        "pymyenergi.client.MyEnergiClient.getData",
        return_value=load_fixture_json("client"),
    ):
        yield


@pytest.fixture(name="zappi_get_data_fixture")
def zappi_get_data_fixture():
    """Mock data from client.getData()"""
    with patch(
        "pymyenergi.zappi.Zappi.getData", return_value=load_fixture_json("zappi")
    ):
        yield
