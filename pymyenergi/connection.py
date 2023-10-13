#  SPDX-License-Identifier: Apache-2.0
"""
Python Package for connecting to myenergi API.

"""
import logging
import sys
from typing import Text

import httpx

from pycognito import Cognito

from .exceptions import MyenergiException
from .exceptions import TimeoutException
from .exceptions import WrongCredentials

_LOGGER = logging.getLogger(__name__)
_USER_POOL_ID = 'eu-west-2_E57cCJB20'
_CLIENT_ID = '2fup0dhufn5vurmprjkj599041'

class Connection:
    """Connection to myenergi API."""

    def __init__(
        self, username: Text = None, password: Text = None, app_password: Text = None, app_email: Text = None, timeout: int = 20
    ) -> None:
        """Initialize connection object."""
        self.timeout = timeout
        self.director_url = "https://director.myenergi.net"
        self.base_url = None
        self.oauth_base_url = "https://myaccount.myenergi.com"
        self.username = username
        self.password = password
        self.app_password = app_password
        self.app_email = app_email
        self.auth = httpx.DigestAuth(self.username, self.password)
        self.headers = {"User-Agent": "Wget/1.14 (linux-gnu)"}
        self.oauth = Cognito(_USER_POOL_ID, _CLIENT_ID, username=self.app_email)
        self.oauth.authenticate(password=self.app_password)
        self.oauth_headers = {"Authorization": f"Bearer {self.oauth.access_token}"}
        self.do_query_asn = True
        self.invitation_id = ''
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

    async def discoverLocations(self):
        locs = await self.get("/api/Location", oauth=True)
        # check if guest location - use the first location by default
        if locs["content"][0]["isGuestLocation"] == True:
            self.invitation_id = locs["content"][0]["invitationData"]["invitationId"]

    def checkAndUpdateToken(self):
        # check if we have to renew out token
        self.oauth.check_token()
        self.oauth_headers = {"Authorization": f"Bearer {self.oauth.access_token}"}

    async def send(self, method, url, json=None, oauth=False):
        # Use OAuth for myaccount.myenergi.com
        if oauth:
            async with httpx.AsyncClient(
                headers=self.oauth_headers, timeout=self.timeout
            ) as httpclient:
                theUrl = self.oauth_base_url + url
                # if we have an invitiation id, we need to add that to the query
                if (self.invitation_id != ""):
                    if ("?" in theUrl):
                        theUrl = theUrl + "&invitationId=" + self.invitation_id
                    else:
                        theUrl = theUrl + "?invitationId=" + self.invitation_id
                try:
                    _LOGGER.debug(f"{method} {url} {theUrl}")
                    response = await httpclient.request(method, theUrl, json=json)
                except httpx.ReadTimeout:
                    raise TimeoutException()
                else:
                    _LOGGER.debug(f"{method} status {response.status_code}")
                    if response.status_code == 200:
                        return response.json()
                    elif response.status_code == 401:
                        raise WrongCredentials()
                    raise MyenergiException(response.status_code)

        # Use Digest Auth for director.myenergi.net and s18.myenergi.net
        else:
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

    async def get(self, url, data=None, oauth=False):
        return await self.send("GET", url, data, oauth)

    async def post(self, url, data=None, oauth=False):
        return await self.send("POST", url, data, oauth)

    async def put(self, url, data=None, oauth=False):
        return await self.send("PUT", url, data, oauth)

    async def delete(self, url, data=None, oauth=False):
        return await self.send("DELETE", url, data, oauth)
