#!/usr/bin/env python3
import asyncio
import json
import os
from itertools import cycle
from typing import Union

from eth_typing import ChecksumAddress

import data.constants
from data.constants import network_index_configs
from data.user_config import UserApiKeys
from utils import ahttp


class KeyRotator:
    def __init__(self, keys: list[str]):
        self.keys = keys
        self.key_cycler = cycle(keys)
        print(f"[+] KeyRotator loaded {len(self.keys)} API keys ... ")

    def next(self):
        return self.key_cycler.__next__()


class IndexerConfig:
    def __init__(
        self,
        network: str,
        url: str,
        indexer: str,
        from_block: int = 0,
        to_block: int = 9999999999999,
        api_keys: list[str] = None,
    ):
        self.network = network
        self.url = url
        self.indexer = indexer
        self.from_block = from_block
        self.to_block = to_block
        if api_keys is None:
            self.key_cycler = False
        else:
            self.key_cycler = KeyRotator(api_keys)

    def get_url(self, address: ChecksumAddress = None, action: str = "tokentx"):
        # print(address, action)
        assert action in ["tokentx", "txlist", "ethprice"]
        if address is None:
            assert action == 'ethprice'
        if not self.key_cycler:
            api_key = os.environ.get("%s_api_key" % self.indexer)
        else:
            # self.key_cycler: KeyRotator
            api_key = self.key_cycler.next()
        if address is None:
            if self.network == 'polygon':
                _action = 'maticprice'
            elif self.network == 'bsc':
                _action = 'bnbprice'
            else:
                _action = 'ethprice'
            _url = f"https://{self.url}/api?module=stats&action={_action}"
        else:
            _action = action

            _url = f"""https://{self.url}/api?module=account&action={_action}&address={address}&&startblock={self.from_block}&endblock={self.to_block}&sort=asc"""

        if api_key is not None:
            _url += f"&apikey={api_key}"
        return _url


class NetworkApi(IndexerConfig):
    def __init__(
        self,
        network,
        url,
        indexer,
        from_block: int = 0,
        to_block: int = 9999999999999,
        api_keys: list[str] = None,
    ):
        super().__init__(network, url, indexer, from_block, to_block, api_keys)


class ApiLoader:
    def __init__(self, config_json: str, name: str):
        # print('apiloader', config_json, name)
        self.name = name
        config = json.loads(config_json)
        if hasattr(UserApiKeys, name):
            api_key_list = getattr(UserApiKeys, name)
        else:
            api_key_list = None
        self._api = NetworkApi(None, None, None, None, None, api_keys=api_key_list)
        for key in ["network", "url", "indexer", "from_block", "to_block"]:
            setattr(self._api, key, config.get(key))
        # self._api

    @property
    def api(self):
        return self._api


class NativeAssetPriceAggregate:
    def __init__(self, network: str):
        self.network = network
        self.api: ApiLoader = self.setup_api()
        self.http: Union[None, ahttp.AsyncHttpClient] = None
        self.is_async_initialized = False

    async def __ainit__(self):
        if self.is_async_initialized:
            return
        self.http = ahttp.AsyncHttpClient()
        await self.http.__ainit__()


    def setup_api(self):
        config = None
        for cfg in network_index_configs:
            if cfg[0] == self.network:
                config = cfg[1]
        return ApiLoader(config, self.network)

    async def get_price(self):
        url = self.api.api.get_url(None, 'ethprice')
        # print(url)
        status, response = await self.http.get(url)
        if status == 200:
            # if self.network in ['ethereum', 'optimism', 'arbitrum']:

            if self.network == 'polygon':
                _key = 'maticusd'
            else:
                _key = 'ethusd'
            return response.get('result').get(_key)


async def get_price_a_main(network: str = None):
    if network is None:
        network = 'ethereum'
    assert network in data.constants.networks
    test_api = NativeAssetPriceAggregate(network)
    await test_api.__ainit__()
    ret = await test_api.get_price()
    # print(ret)
    await test_api.http.__aclose__()
    return ret

if __name__ == '__main__':
    print(asyncio.run(get_price_a_main()))

