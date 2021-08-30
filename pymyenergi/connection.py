#  SPDX-License-Identifier: Apache-2.0
"""
Python Package for connecting to myenergi API.

"""
import logging
import sys
from typing import Text

import httpx

from .exceptions import MyenergiException
from .exceptions import WrongCredentials

_LOGGER = logging.getLogger(__name__)


class Connection:
    """Connection to myenergi API."""

    def __init__(
        self, username: Text = None, password: Text = None, timeout: int = 15
    ) -> None:
        """Initialize connection object."""
        self.timeout = timeout
        self.director_url = "https://director.myenergi.net"
        self.base_url = None
        self.username = username
        self.password = password
        self.auth = httpx.DigestAuth(self.username, self.password)
        self.headers = {"User-Agent": "Wget/1.14 (linux-gnu)"}
        self._httpclient = httpx.AsyncClient(
            auth=self.auth, headers=self.headers, timeout=self.timeout
        )
        _LOGGER.debug("New connection created")

    def _checkMyenergiServerURL(self, responseHeader):
        _LOGGER.debug("Extract Myenergi ASN from Myenergi header")
        if "X_MYENERGI-asn" in responseHeader:
            self.base_url = "https://" + responseHeader["X_MYENERGI-asn"]
        else:
            _LOGGER.debug("Myenergi ASN not found in Myenergi header")

    async def send(self, method, url, json=None):
        # If base URL has not been set, make a request to director to fetch it
        if self.base_url is None:
            _LOGGER.debug("Get Myenergi base url from director")
            try:
                directorUrl = self.director_url + "/cgi-jstatus-E"
                response = await self._httpclient.get(directorUrl)
            except Exception:
                _LOGGER.error("Myenergi server request problem")
                _LOGGER.debug(sys.exc_info()[0])
            else:
                self._checkMyenergiServerURL(response.headers)
        theUrl = self.base_url + url
        try:
            _LOGGER.debug(f"{method} {url} {theUrl}")
            response = await self._httpclient.request(method, theUrl, json=json)
        except httpx.ReadTimeout:
            raise Exception("Read timeout")
        else:
            _LOGGER.debug(f"GET status {response.status_code}")
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 401:
                raise WrongCredentials()
            raise MyenergiException(response.status_code)

    async def get(self, url):
        return await self.send("GET", url)

    async def post(self, url, data=None):
        return await self.send("POST", url, data)

    async def put(self, url, data=None):
        return await self.send("PUT", url, data)

    async def delete(self, url, data=None):
        return await self.send("DELETE", url, data)

    async def close(self):
        _LOGGER.debug("Closing Myenergi http client connection")
        await self._httpclient.aclose()
