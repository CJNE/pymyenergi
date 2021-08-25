#  SPDX-License-Identifier: Apache-2.0
"""
Python Package for connecting to MyEnergi API.

"""
import logging

from typing import Text
import httpx
import sys

from .exceptions import WrongCredentials, MyEnergiException

_LOGGER = logging.getLogger(__name__)


class Connection:
    """Connection to MyEnergi API."""

    def __init__(
        self,
        username: Text = None,
        password: Text = None,
        timeout: int = 10
    ) -> None:
        """Initialize connection object."""
        self.timeout = timeout
        self.director_url = 'https://director.myenergi.net'
        self.base_url = None
        self.username = username
        self.password = password
        self.auth = httpx.DigestAuth(self.username, self.password)
        self._httpclient = httpx.AsyncClient()
        _LOGGER.debug("New connection created")

    def _checkMyEnergiServerURL(self, responseHeader):
        _LOGGER.debug('Extract MyEnergi ASN from Myenergi header')
        if 'X_MYENERGI-asn' in responseHeader:
            self.base_url = 'https://'+responseHeader['X_MYENERGI-asn']
        else:
            _LOGGER.debug('MyEnergi ASN not found in Myenergi header')

    async def _createhead(self):
        headers = {'User-Agent': 'Wget/1.14 (linux-gnu)'}
        _LOGGER.debug('Create headers')
        if self.base_url is None:
            _LOGGER.debug('Get MyEnergi base url from director')
            try:
                url = self.director_url + '/cgi-jstatus-E'
                response = await self._httpclient.get(url,
                                                      headers=headers,
                                                      auth=self.auth,
                                                      timeout=self.timeout)
            except:
                _LOGGER.error("Myenergi server request problem")
                _LOGGER.debug(sys.exc_info()[0])
            else:
                self._checkMyEnergiServerURL(response.headers)
        return headers

    async def get(self, url):
        headers = await self._createhead()
        theUrl = self.base_url + url
        _LOGGER.debug(f"GET {url} {theUrl}")
        response = await self._httpclient.get(theUrl,
                                              headers=headers,
                                              auth=self.auth,
                                              timeout=self.timeout)
        _LOGGER.debug(f"GET status {response.status_code}")
        if (response.status_code == 200):
            return response.json()
        raise MyEnergiException(response.status_code)

    async def post(self, url, data=None):
        headers = await self._createhead()
        theUrl = self.base_url + url
        _LOGGER.debug(f"POST {url} {theUrl}")
        response = await self._httpclient.post(theUrl,
                                               headers=headers,
                                               data=data,
                                               auth=self.auth,
                                               timeout=self.timeout)
        _LOGGER.debug(f"POST status {response.status_code}")
        if (response.status_code == 200):
            return response.json()
        raise MyEnergiException(response.status_code)

    async def put(self, url, data=None):
        headers = await self._createhead()
        theUrl = self.base_url + url
        _LOGGER.debug(f"PUT {url} {theUrl}")
        response = await self._httpclient.put(theUrl,
                                              headers=headers,
                                              data=data,
                                              auth=self.auth,
                                              timeout=self.timeout)
        _LOGGER.debug(f"PUT status {response.status_code}")
        if (response.status_code == 200):
            return response.json()
        raise MyEnergiException(response.status_code)

    async def delete(self, url, data=None):
        headers = await self._createhead()
        theUrl = self.base_url + url
        _LOGGER.debug(f"DELETE {url} {theUrl}")
        response = await self.httpsclient.delete(theUrl,
                                                 headers=headers,
                                                 data=data,
                                                 auth=self.auth,
                                                 timeout=self.timeout)
        _LOGGER.debug(f"DELETE status {response.status_code}")
        if (response.status_code == 200):
            return response.json()
        raise MyEnergiException(response.status_code)

    async def close(self):
        await self._httpclient.aclose()
