import asyncio
import json
import time
from typing import Union

import aiofiles
import web3
from eth_typing import ChecksumAddress
from eth_utils import to_checksum_address
from hexbytes import HexBytes

from utils.helpers import Acct


class ScanSessionReport:
    def __init__(self, output_file: str, target_list: list[Acct] = None, loop: asyncio.AbstractEventLoop = None):
        if loop is None:
            self.loop = asyncio.get_running_loop()
        self.targets = target_list
        self.output_file = output_file
        self.report = []
        self.total = 0
        self.initiated = time.time()
        if self.output_file is None:
            self.output_file = 'reports/unnamed_%s.json' % self.initiated
        self.current_batch = 0
        assert self.targets is not None

    def get_report(self):
        return self.report

    async def add_wallet(self, assets: list):
        if not assets:
            return
        for token in assets:
            if token.get('balanceUsd'):
                self.total += float(token.get('balanceUsd'))
                self.report.append(token)
            if token.get('tokenId'):
                self.report.append(token)
        await self.dump()

    async def find_key(self, address: Union[str, ChecksumAddress]):
        def is_key(_key: HexBytes, _address: ChecksumAddress) -> bool:
            if to_checksum_address(web3.Account.from_key(_key).address) == to_checksum_address(_address):
                return True
            return False
        for key in self.targets:
            if is_key(key.key, address):
                return key

    async def dump(self):
        async with aiofiles.open(f'{self.output_file}', 'w') as f:
            await f.write(json.dumps(self.report))

    async def load(self):
        async with aiofiles.open(f'{self.output_file}', 'r') as f:
            return await json.loads(await f.read())
