import asyncio
import json
from typing import Union, Tuple, Any

import aiohttp


class AsyncHttpClient:
    def __init__(self, _headers=None, base_url: str = None, timeout: Union[int, float] = 60):
        """
        A skeletal asynchronous HTTP class. Because I found myself writing this same code
        hundreds of times, I decided to just write a reusable module.
        :param _headers:
        :param base_url:
        :param timeout:
        """
        if _headers is None:
            _headers = {}
        self.timeout_secs: Union[int, float] = timeout
        self.base_url: str = base_url
        self._session: Union[aiohttp.ClientSession, None] = None
        self.is_a_initialized: bool = False
        self.global_headers: dict = _headers

    async def __ainit__(self):
        """
        async __init__ , this must be awaited to create the client session
        :return:
        """
        timeout = aiohttp.ClientTimeout(total=self.timeout_secs, connect=(self.timeout_secs / 3),
                              sock_connect=(self.timeout_secs / 3), sock_read=(self.timeout_secs / 3))
        self._session: aiohttp.ClientSession = aiohttp.ClientSession(headers=self.global_headers,
                                                                     base_url=self.base_url,
                                                                     timeout=timeout)
        self.is_a_initialized = True

    async def __aclose__(self):
        self._session: aiohttp.ClientSession
        await self._session.close()

    async def parse_response(self, response: aiohttp.ClientResponse) -> tuple[int, bytes | Any]:
        """

        :param response: client response object
        :return: status code, (either json dict, OR bytes if the content was not json)
        """

        status = response.status

        if status == 200:
            try:
                resp = await response.json(content_type=None)
            except json.JSONDecodeError:
                resp = await response.read()
        else:
            resp = await response.read()
        return status, resp

    async def post(self, path: str, data=None, verify_ssl: bool = False, _headers_overide: dict = None) -> tuple[
        int, bytes | Any]:
        """
        HTTP post request
        :param _headers_overide:
        :param path: URL
        :param data: payload
        :param verify_ssl: ignore ssl warnings
        :return: status, resp
        """
        if data is None:
            data = {}
        if _headers_overide:
            _headers = _headers_overide
        else:
            _headers = self.global_headers
        session: aiohttp.ClientSession = self._session
        async with session.post(url=path, json=data, verify_ssl=verify_ssl, headers=_headers) as response:
            return await self.parse_response(response)

    async def get(self, path: str, params=None, verify_ssl: bool = False, _headers_overide: dict = None) -> tuple[
        int, bytes | Any]:
        """
        HTTP GET request
        :param _headers_overide:
        :param path: URL
        :param params: query parameters (ie ?&param=value)
        :param verify_ssl: bool
        :return: status, resp
        """
        if params is None:
            params = {}
        if _headers_overide:
            _headers = _headers_overide
        else:
            _headers = self.global_headers
        async with self._session.get(url=path, params=params, verify_ssl=verify_ssl, headers=_headers) as response:
            response: aiohttp.ClientResponse
            # print(response.request_info)
            return await self.parse_response(response)

    async def request(self, method: str, *args, **kwargs) -> tuple[
        int, bytes | Any]:
        """
        wrapper function for making requests
        :param method: get, or post
        :param args: arguments
        :param kwargs: keyword arguments
        :return: status, resp
        """
        resp = ''
        status = 0
        if hasattr(self, method.lower()):
            fn = getattr(self, method.lower())
            coro = fn(*args, **kwargs)
            try:
                status, resp = await coro
            except (aiohttp.ClientResponseError, aiohttp.ClientConnectorError, aiohttp.ServerDisconnectedError,
                    aiohttp.ClientOSError) as err:
                print('[!] HTTP Request error %s' % err)
            except asyncio.exceptions.TimeoutError:
                print('[!] Timed out ...  ')
            except aiohttp.ClientConnectorSSLError as err:
                print('[!] ssl error %s with: ' % err)
            except ValueError as err:
                print('[!] invalid ?: %s' % err)
            finally:
                return status, resp

    async def demo(self, url_path: str, method: str = 'get'):
        """
        Just do an HTTP get
        :param url_path: URL
        :param method:
        :return:
        """
        if not self.is_a_initialized:
            await self.__ainit__()
        s, ret = await self.request(method, path=url_path)
        await self._session.close()
        if s == 200:
            if type(ret) is bytes:
                return ret.decode()
            return s, ret


if __name__ == '__main__':
    headers = {'content-type': 'application/json'}
    http = AsyncHttpClient(_headers=headers)
    print(asyncio.run(http.demo('https://ipecho.net/plain', 'get')))
