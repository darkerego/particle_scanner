#!/usr/bin/env python3

import os
from typing import Union

import dotenv
import web3
from web3.exceptions import ExtraDataLengthError
from web3.middleware import geth_poa_middleware
from data.constants import CHAIN_ALIASES
from utils.errors import DotenvNotConfigured

dotenv.load_dotenv()


def check_for_chain_alias(network_name: str) -> Union[str, bool]:
    for network in CHAIN_ALIASES:
        if network[0] == network_name:
            return network[1]
        if network[1] == network_name:
            return network[0]
    return False


def is_poa_chain(w3: web3.Web3) -> bool:
    try:
        genesis_block = w3.eth.get_block(0)
        this_block = w3.eth.get_block('latest')
    except ExtraDataLengthError:
        return True
    else:
        extra_data = genesis_block['extraData']
        consensus_engine = extra_data[0:4]
        if consensus_engine in (b'\x63\x6c\x69\x71', b'\x69\x62\x66\x74') or len(extra_data) > 64:
            return True
        else:
            return False


def attempt_setup(network_name: str) -> Union[web3.Web3, bool]:
    endpoint = os.environ.get(f'{network_name}_http_endpoint')
    if endpoint is None:
        return False
    else:
        _provider = web3.HTTPProvider(endpoint)
        w3 = web3.Web3(_provider)
        return w3


def setup_w3(network: str = None, provider: (web3.HTTPProvider, web3.WebsocketProvider) = None) -> Union[
    web3.Web3, bool]:
    assert network is not None or provider is not None
    assert not (network and provider)
    # assert type(provider) in [web3.providers.BaseProvider]
    if network:
        dotenv.load_dotenv()
        w3 = attempt_setup(network)
        if not w3:
            network = check_for_chain_alias(network)
            if network:
                w3 = attempt_setup(network)
                if not w3:
                    raise DotenvNotConfigured("You need to setup your `.env` file first! See docs.")
    else:
        w3 = web3.Web3(provider)
    if hasattr(w3, 'is_connected'):
        connected = w3.is_connected(show_traceback=True)
    else:
        connected = w3.isConnected()
    if connected:
        print(f'[+] Web3 is connected to network {network} ')
        if is_poa_chain(w3):
            if network:
                print('[+] init_w3: injecting poa middleware for network: %s' % network)
            else:
                print('[+] init_w3: injecting poa middleware for provider: %s' % provider.__str__())
            w3.middleware_onion.inject(geth_poa_middleware, layer=0)
        else:
            print('[+] init_w3: not a poa chain: %s' % network)
        return w3
    return False
