#  SPDX-License-Identifier: Apache-2.0
"""
Python Package for connecting to myenergi API.

"""
import logging
import sys
from typing import Text

import httpx

from .exceptions import MyenergiException
from .exceptions import TimeoutException
from .exceptions import WrongCredentials

_LOGGER = logging.getLogger(__name__)


class Connection:
    """Connection to myenergi API."""

    def __init__(
        self, username: Text = None, password: Text = None, timeout: int = 20
    ) -> None:
        """Initialize connection object."""
        self.timeout = timeout
        self.director_url = "https://director.myenergi.net"
        self.base_url = None
        self.username = username
        self.password = password
        self.auth = httpx.DigestAuth(self.username, self.password)
        self.headers = {"User-Agent": "Wget/1.14 (linux-gnu)"}
        self.do_query_asn = True
        _LOGGER.debug("New connection created")

    def _checkMyenergiServerURL(self, responseHeader):
        if "X_MYENERGI-asn" in responseHeader:
            new_url = "https://" + responseHeader["X_MYENERGI-asn"]
            if new_url != self.base_url:
                _LOGGER.info(f"Updated myenergi active server to {new_url}")
            self.base_url = new_url
        else:
            _LOGGER.debug(
                "Myenergi ASN not found in Myenergi header, assume auth failure (bad username)"
            )
            raise WrongCredentials()

    async def send(self, method, url, json=None):
        # If base URL has not been set, make a request to director to fetch it

        async with httpx.AsyncClient(
            auth=self.auth, headers=self.headers, timeout=self.timeout
        ) as httpclient:
            if self.base_url is None or self.do_query_asn:
                _LOGGER.debug("Get Myenergi base url from director")
                try:
                    directorUrl = self.director_url + "/cgi-jstatus-E"
                    response = await httpclient.get(directorUrl)
                except Exception:
                    _LOGGER.error("Myenergi server request problem")
                    _LOGGER.debug(sys.exc_info()[0])
                else:
                    self.do_query_asn = False
                    self._checkMyenergiServerURL(response.headers)
            theUrl = self.base_url + url
            try:
                _LOGGER.debug(f"{method} {url} {theUrl}")
                response = await httpclient.request(method, theUrl, json=json)
            except httpx.ReadTimeout:
                # Make sure to query for ASN next request, might be a server problem
                self.do_query_asn = True
                raise TimeoutException()
            else:
                _LOGGER.debug(f"GET status {response.status_code}")
                self._checkMyenergiServerURL(response.headers)
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 401:
                    raise WrongCredentials()
                # Make sure to query for ASN next request, might be a server problem
                self.do_query_asn = True
                raise MyenergiException(response.status_code)

    async def get(self, url):
        return await self.send("GET", url)

    async def post(self, url, data=None):
        return await self.send("POST", url, data)

    async def put(self, url, data=None):
        return await self.send("PUT", url, data)

    async def delete(self, url, data=None):
        return await self.send("DELETE", url, data)
