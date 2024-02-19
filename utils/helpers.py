import asyncio
import binascii
import json
import os
import os.path
import os.path as path
from typing import Union

import aiofiles
import trio
import web3
from eth_account import Account
from eth_typing import ChecksumAddress
from eth_utils import to_checksum_address
from hexbytes import HexBytes

from data import constants
from data.constants import NULL_KEY


class Acct:
    def __init__(self, key: Union[str, bytes, None], address: Union[str, None, ChecksumAddress]):
        self.key = HexBytes(key)
        self.address = to_checksum_address(address)

    def to_json(self):
        return json.dumps({
            'key': self.key.hex(),  # Convert HexBytes to hex string
            'address': self.address  # Assuming address is already a string
        })

    @property
    def as_dict(self) -> dict:
        return json.loads(self.to_json())

    @classmethod
    def from_json(cls, json_or_str: Union[str, dict]) -> object:
        if type(json_or_str) is str:
            data = json.loads(json_or_str)
        else:
            data = json_or_str
        return cls(data['key'], data['address'])

    def __repr__(self):
        return f"Acct(key={self.key}, address={self.address})"


def parse_key(key: str) -> Acct | None:
    try:
        account = Account.from_key(key)
    except (ValueError, binascii.Error):
        try:
            addr = to_checksum_address(key)
        except (ValueError, binascii.Error):
            return None
        else:
            return Acct(key=NULL_KEY, address=addr)
    else:
        return Acct(key=account.key, address=account.address)


def divide_chunks(l: list, n: int) -> list:
    def split_gen(ll: list, nn: int):
        for i in range(0, len(ll), nn):
            yield ll[i:i + nn]

    """
    Split a list
    :param l: list
    :param n: batch size
    :return: generator
    """
    # unwrap the generator
    return [chunk for chunk in split_gen(l, n)]


def load_json(file: str) -> dict:
    assert os.path.exists(file)
    with open(file, 'r') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError as err:
            print('[!] Error parsing %s: %s: ' % (file, err))
            return {}


def dump_json(file: str, _object: Union[dict, list]) -> None:
    with open(file, 'w') as f:
        json.dump(_object, f)


async def async_dump_json(file: str, _object: Union[dict, list]) -> None:
    async def asyncio_dump_json(_file, __object):
        async with aiofiles.open(_file, 'w') as f:
            await f.write(json.dumps(__object))

    def sync_dump_json(_file: str, _object: Union[dict, list]) -> None:
        with open(_file, 'w') as f:
            json.dump(_object, f)

    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return await trio.to_thread.run_sync(sync_dump_json, file, _object)
    else:
        return await asyncio_dump_json(file, _object)


async def async_load_json(file: str) -> Union[dict, str, None]:
    if not path.exists(file):
        raise FileExistsError('The file %s does not exist' % file)
    async with aiofiles.open(file, 'r') as f:
        try:
            return json.loads(await f.read())
        except json.JSONDecodeError as err:
            print('[!] Error parsing %s: %s: ' % (file, err))
            return None


async def async_read_as_lines(file: str) -> list[str]:
    async def strip_sleep(_line: str):
        ret = _line.strip('\r\n')
        await asyncio.sleep(0)
        return ret

    async def asyncio_read_lines(_file):
        async with aiofiles.open(_file, 'r') as f:
            return [await strip_sleep(line) for line in await f.readlines()]

    def read_as_lines_sync(_file):
        with open(_file, 'r') as f:
            return [_line.strip('\r\n') for _line in f.readlines()]



    if not path.exists(file):
        print('[!] The path specified: "%s" does not exist.' % file)
        return []
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return await trio.to_thread.run_sync(read_as_lines_sync, file)
    else:
        return await asyncio_read_lines(file)





def load_account(key: Union[HexBytes, str, bytes]):
    try:
        account = web3.Account.from_key(key)
    except (ValueError, binascii.Error):
        try:
            address = to_checksum_address(key)
        except (ValueError, binascii.Error):
            return None
        else:
            return Acct(address=address, key=constants.NULL_KEY)
    else:
        return Acct(address=account.address, key=account.key.hex())


def is_valid_eth_key(hex_str: Union[HexBytes, str, bytes]) -> bool:
    try:
        int(hex_str, 16)
    except ValueError:
        return False
    return True


def validate_eth_address(address: (HexBytes, str)) -> bool:
    try:
        to_checksum_address(address)
    except (binascii.Error, ValueError):
        return False
    return True


def read_as_lines(file_or_str: str):
    if not path.exists(file_or_str):
        print('[!] The path specified: "%s" does not exist.' % file_or_str)
        return []

    with open(file_or_str, 'r') as f:
        return [line.strip('\r\n') for line in f.readlines()]


async def async_load_eth_keys(file_or_str: str) -> list[Acct | None] | list[Acct]:
    """
    Load either a list of keys from a file or a single key into an Acct object
    :param file_or_str: string path or hex key
    :return: list[Acct]
    """
    if path.exists(file_or_str):
        print('[+] Loading ... ')
        return [load_account(key) for key in await async_read_as_lines(file_or_str)]
    else:
        _acct = load_account(file_or_str)
        if _acct is not None:
            return [Acct(_acct.key.hex(), _acct.address)]


def format_float(amount: float, precision: int = None) -> str:
    """
    Formats a float as a decimal string with large precision.
    :param amount:
    :param precision:
    :return:
    """
    if not precision:
        precision = 18
    format_str = "{:.%sf}" % precision
    formatted_amount = format_str.format(float(amount))
    return formatted_amount.rstrip('0').rstrip('.')


def load_keys(file_or_str: str):
    if path.exists(file_or_str):
        return [load_account(key) for key in read_as_lines(file_or_str)]
    else:
        _acct = load_account(file_or_str)
        return [Acct(_acct.key.hex(), _acct.address)]

def divide_chunks_to_list(l: list, n: int) -> list:
    """
    Split a list
    :param l: list
    :param n: batch size
    :return: generator
    """

    def divider(l, n):
        # looping till length l
        for i in range(0, len(l), n):
            yield l[i:i + n]

    return [x for x in divider(l, n)]