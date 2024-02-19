#!/usr/bin/env python3
import argparse
import asyncio
import json
import logging
import os
import pprint
import time
from typing import Union, Any

import dotenv
import httpcore
import httpx
import tqdm
import tqdm.asyncio
from eth_typing import ChecksumAddress
from eth_utils import to_checksum_address

import data.constants

from data.constants import ZERO_ADDRESS
from utils import helpers, custom_logger
from utils.color_print import ColorPrint
from utils.helpers import async_load_eth_keys, Acct

cp = None


class ColoredOutput:
    """
    Simple class for colored console output using ANSI escape codes.
    """

    # ANSI escape codes for colors and styles
    RESET = '\033[0m'
    YELLOW = '\033[93m'
    GREEN = '\033[92m'
    RED = '\033[91m'
    BOLD_WHITE = '\033[1;37m'

    @staticmethod
    def attention(message):
        """
        Print message in yellow for attention.
        """
        print(f"{ColoredOutput.YELLOW}[!] ATTENTION: {message}{ColoredOutput.RESET}")

    @staticmethod
    def success(message):
        """
        Print message in green for success.
        """
        print(f"{ColoredOutput.GREEN}[+] {message}{ColoredOutput.RESET}")

    @staticmethod
    def error(message):
        """
        Print message in red for error.
        """
        print(f"{ColoredOutput.RED}[-] ERROR: {message}{ColoredOutput.RESET}")

    @staticmethod
    def notice(message):
        """
        Print message in bold white for notice.
        """
        print(f"{ColoredOutput.BOLD_WHITE}[=] NOTICE: {message}{ColoredOutput.RESET}")


class TokenPrice:
    chain_id: int

    def __init__(self, address: Union[str, ChecksumAddress], _chain_id: int, price: float):
        self.address = address
        self.chain_id = _chain_id
        self.price = price
        self.updated = int(time.time())

    def update_price(self, price: float):
        self.price = price
        self.updated = int(time.time())

    def as_dict(self) -> dict:
        return {
            'address': self.address,
            'cid': self.chain_id,
            'price': self.price,
            'updated': self.updated
        }


class ScanSession:
    def __init__(self, output_file: str = None, accounts: list[Acct] = None, verbosity: int = 0):
        self.verbosity = verbosity
        self.initiated = time.time().__str__()
        self.output_file = output_file if output_file is not None else f'scan_{self.initiated}.json'
        self.acct_map = {}
        self.native_prices: dict[int, TokenPrice] = {}
        self.token_prices: dict[int, dict[Union[str, ChecksumAddress], TokenPrice]] = {}
        self._acct_list = accounts
        self._accounts: list[Acct] = []

    @classmethod
    async def create(cls, output_file: str, accounts: list[Acct]):
        session = cls(output_file, accounts)
        # await session.initialize_accounts()
        return session

    async def initialize_accounts(self, _cids):
        if len(self._acct_list):
            cp.debug('Initializing %s accounts' % len(self._acct_list))
            await self.create_account_dict(self._accounts, _cids)
            # self.acct_map = self._accounts

    async def create_account_dict(self, accts: list[Acct], _cids: list[int]):
        cp.notice('Creating account dict')
        for acct in accts:
            if acct is not None:
                self.acct_map[acct.address] = {'key': acct.key.hex().__str__(), 'tokens': []}
        for c in _cids:
            self.token_prices[c] = {}

    async def update_wallet(self, data_: dict, _cid: int):
        _cid = int(_cid)
        # print('[debug] update wallet %s' % data_)
        # _cid = data_.get('cid')
        __data = data_.get('result')
        native_amount = int(__data.get('native'))
        tokens = __data.get('tokens')

        addr = data_['address']
        # print('updating acct %s' % addr)
        # print('native: ', native_amount)
        # print('tokens: ', tokens)
        if self.acct_map.get(addr):
            # print('found addr: %s ' % addr)

            # print('tokens: ', self.acct_map[addr].get('tokens'))
            if int(native_amount) > 0:
                tokens.append({'address': ZERO_ADDRESS, 'amount': native_amount, 'cid': _cid})
            if len(tokens):
                self.acct_map[addr]['tokens'].extend(tokens)
        #  print('acct_map_tokens', self.acct_map[addr]['tokens'])

    async def set_token_prices(self, price_list: list[TokenPrice]):
        def needs_update(tp: TokenPrice):
            if self.token_prices.get(tp.chain_id).get(tp.address):
                return not tp.updated >= time.time() - 600
            else:
                return True

        await self._set_token_prices([t for t in price_list if needs_update(t)])

    async def _set_token_prices(self, price_list: list[TokenPrice]):

        for price in price_list:

            # print('setting %s' % price.__dict__)
            if price.address == 'native' or price.address == ZERO_ADDRESS:

                _price_native = TokenPrice(ZERO_ADDRESS, price.chain_id, price.price)
                self.native_prices.update({int(_price_native.chain_id): _price_native})
                # self.token_prices.update({ZERO_ADDRESS: _price_native})
            else:
                # print(price, type(price))
                if self.token_prices.get(price.chain_id) is {}:
                    self.token_prices[price.chain_id] = {to_checksum_address(price.address): price}
                else:
                    self.token_prices[price.chain_id].update({to_checksum_address(price.address): price})
                    # self.token_prices.update({price.chain_id: })

    async def get_token_price(self, token: ChecksumAddress, _chain_id=None) -> tuple[float, int]:
        if token == 'native' or token == ZERO_ADDRESS:
            return self.native_prices.get(_chain_id).price, self.native_prices.get(_chain_id).chain_id
        if self.token_prices.get(_chain_id) is None:
            self.token_prices.update({_chain_id: {}})
            return 0, _chain_id
        else:
            if self.token_prices[_chain_id].get(token) is not None:
                # c = self.token_prices[_chain_id].get(token).chain_id
                return self.token_prices[_chain_id].get(token).price, _chain_id
        return 0, 0

    async def calculate_values(self, ):
        count = 0
        final_report = {}
        report_copy = self.acct_map.copy()
        cp.notice('Calculating dollar values ... ')
        for address, __data in self.acct_map.items():
            # print(address, __data)
            key = __data['key']
            tokens = __data['tokens']
            # cid = __data['cid']
            cp.output('address: %s , data: %s, ' % (address, __data))

            for x, token in enumerate(tokens):
                if token.get('address') in ['native', ZERO_ADDRESS]:
                    eth = int(token.get('amount'))
                    cid = int(token.get('cid'))

                    if eth > 0:
                        price, nada = await self.get_token_price(ZERO_ADDRESS, token['cid'])
                        count += 1
                        bal = int(eth) / (10 ** 18)
                        token_value = float(price) * bal
                        report_copy[address]['tokens'][x].update({'price': price,
                                                                  'balance': bal,
                                                                  'value': token_value,
                                                                  'cid': cid})
                        entry = report_copy[address]['tokens'][x]
                        entry['key'] = key
                        final_report.update({address: entry})
                else:
                    raw_balance = int(token.get('amount'))
                    if raw_balance > 0:
                        price, nothing = await self.get_token_price(token.get('address'), token.get('cid'))
                        cid = token.get('cid')
                        count += 1
                        decimals = int(token.get('decimals'))
                        human_bal = raw_balance / (10 ** decimals)
                        token_value = human_bal * price
                        report_copy[address]['tokens'][x].update(
                            {'price': float(price), 'balance': human_bal, 'value': token_value, 'cid': cid}),
                        entry = report_copy[address]['tokens'][x]
                        entry['key'] = key
                        final_report.update({address: entry})
        self.acct_map = final_report
        return final_report

    async def finalize(self):
        report_copy = await self.calculate_values()
        self.report_setter(report_copy)
        await self.dump()
        return self.report

    async def dump(self):
        await asyncio.sleep(0)
        await helpers.async_dump_json(self.output_file, self.acct_map)

    @property
    def report(self):
        return json.loads(json.dumps(self.acct_map))

    def report_setter(self, report: dict):
        setattr(self, 'acct_map', report)


TASKS = set()


class ParticleApi:
    def __init__(self, _project_id: str, _project_server_key: str):
        self.project_id = _project_id
        self.project_server_key = _project_server_key
        self.base_url = f"https://rpc.particle.network/evm-chain"
        self.headers = {'Content-Type': 'application/json'}
        self.auth = (_project_id, _project_server_key)
        self.client = httpx.AsyncClient(auth=self.auth, headers=self.headers)
        self.price_map: dict[int, TokenPrice] = {}
        self.logger: logging.Logger = self.setup_logger

    @property
    def setup_logger(self):
        return custom_logger.get_logger()

    def get_url_by_chain_id(self, _chain_id: int):
        return self.base_url + f"?chainId={_chain_id}"

    async def make_request(self, _chain_id: int, method: str, params: list[Any] = [],
                           sleep_for_attempt: float = 1.5) -> Any:
        ret_val = None
        sleep_for_attempt += sleep_for_attempt
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": 1,
        }
        for x in range(3):
            try:
                response = await self.client.post(self.get_url_by_chain_id(_chain_id), json=payload)
            except (httpx.ReadTimeout, httpx.ReadError) as err:
                self.logger.error('Http Error making request: %s, sleeping for %s' % (err, sleep_for_attempt))
                await asyncio.sleep(sleep_for_attempt)
            except (httpx.ConnectTimeout, httpx.HTTPStatusError, httpcore.ConnectError) as err:
                self.logger.error('Http conn timeout: %s' % err)
                await asyncio.sleep(sleep_for_attempt)
            except Exception as err:
                self.logger.error(f'Unknown exception: %s, sleeping for %s' % (err, sleep_for_attempt))
                await asyncio.sleep(sleep_for_attempt)
            else:
                if response.status_code == 200:
                    ret_val = response.json().get('result')
                else:
                    self.logger.error('Http Status %s' % response.status_code)
            finally:
                if ret_val:
                    return ret_val
                if sleep_for_attempt > 1.3:
                    return None
                return await self.make_request(_chain_id, method, params, sleep_for_attempt)

    async def eth_get_block(self, _chain_id: int, block: Union[int, str]):
        return await self.make_request(_chain_id, 'eth_getBlockByNumber', [block])

    async def eth_get_balance(self, addresses: list[Union[str, ChecksumAddress]], _chain_id: int):
        return int(await self.make_request(_chain_id, 'eth_getBalance', [
            addresses,
            "latest",
        ]), 16)

    async def get_tokens(self, address: Union[str, ChecksumAddress, Union[list[str, ChecksumAddress]]], _chain_id: int):
        if type(address) is not list:
            address = [address]
        return await self.make_request(_chain_id, 'particle_getTokens', params=address)

    async def _get_price(self, _tokens: list[Union[ChecksumAddress, str]], _chain_id: int):
        params = [_tokens, ['usd']]
        return await self.make_request(int(_chain_id), 'particle_getPrice', params=params)

    async def get_price(self, tokens: list[Union[ChecksumAddress, str]], _chain_id: int) -> None | list[TokenPrice]:
        result_prices = []
        tokens = list(sorted(set(tokens)))
        ret_dict: list[ChecksumAddress, str] = await self._get_price(tokens, _chain_id)
        if not ret_dict:
            return None
        else:
            if len(ret_dict):
                for x, res in enumerate(ret_dict):
                    cp.debug('Price %s, %s' % (x, res))
                    if res['address'] in ['native', ZERO_ADDRESS]:
                        address = ZERO_ADDRESS
                        price = res['currencies'][0]['price']
                    else:
                        address = to_checksum_address(res['address'])
                        price = res['currencies'][0]['price']
                    if float(price) > 0:
                        token_price_obj = TokenPrice(address=address, _chain_id=_chain_id, price=price)
                        result_prices.append(token_price_obj)
        return result_prices


def cli_args() -> argparse.Namespace:
    _args = argparse.ArgumentParser()
    _args.add_argument('-b', '--batch', type=int, default=100, help='Probably do not change this')
    _args.add_argument('-v', '--verbosity', action='count', default=0, help='Increase the output verbosity')
    subparsers = _args.add_subparsers(dest='command')
    single = subparsers.add_parser('single')
    single.add_argument('address', type=str, help='ethereum key or address')
    single.add_argument('chain_id', type=int, help='List of chain IDs. Supply `0` for all supported chains.')
    file_list = subparsers.add_parser('file_list')
    file_list.add_argument('file', type=str, help='Name of file or list')
    file_list.add_argument('chain_id', type=int, help='list')
    file_list.add_argument('output_file', type=str, help='json output')

    return _args.parse_args()


def divide_chunks(l: list, n: int):
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


async def log_result(out_file: str, _result: Union[dict, str]):
    try:
        await helpers.async_dump_json(out_file, _result)
    finally:
        await asyncio.sleep(0)


async def single_main(_address: Union[str, ChecksumAddress], _cid: int):
    result = {}
    cp.output(f'Running {_address}')
    api = ParticleApi(project_id, project_server_key)
    tokens_ret = await api.get_tokens(_address, _cid)
    result.update({'tokens': tokens_ret})
    return result


async def wrap_get_tokens(_api, acct: Acct, _cid: int, _out: str,
                          _scan_session: ScanSession) -> dict[Any, dict[str, Any]] | bool:
    success = False
    res = {}
    sleep_for = 0.3
    if acct is None:
        return False

    for x in range(3):
        try:
            tokens_ret = await _api.get_tokens(acct.address, _cid)
        except httpx.ReadTimeout as err:
            cp.warning('Try: %s/3 Timed out: %s' % (x + 1, err))
            await asyncio.sleep(sleep_for)
            sleep_for += sleep_for
            if x > 2:
                break
        else:
            if tokens_ret is not None:
                TOKENS: list[dict] = tokens_ret.get('tokens')
                if len(TOKENS) > 0:
                    [t.update({'cid': _cid}) for t in TOKENS]
                if int(tokens_ret.get('native')) > 0 or len(tokens_ret.get('tokens')) > 0:
                    success = True
                    # res = {acct.address: {}}
                    res = {'key': str(acct.key.hex()), 'address': str(acct.address), 'result': tokens_ret, 'cid': _cid}
                    await _scan_session.update_wallet(res, _cid)
                    # await log_result(_out, result)
            if success and res:
                return res
        return False


async def load_accounts_from_file(file_path: str):
    return await async_load_eth_keys(file_path)


async def file_list_main(file_: str, _cid: int, output_file: str = None, _batch_size: int = 100, cp=None):
    if output_file is None:
        output_file = 'scans/particle_scan_%s.json' % time.time()
    if _cid == 0:
        chain_id_list = []
        for cid in data.constants.PARTICLE_SUPPORTED:
            chain_id_list.append(cid[0])

    else:
        chain_id_list = [_cid]
    if cp is None:
        cp = ColorPrint(args.verbosity)
    cp.output(chain_id_list)
    cp.output('Logging results to %s' % output_file)
    api = ParticleApi(project_id, project_server_key)

    eth_accounts = await load_accounts_from_file(file_)
    scan_session = await ScanSession(args.output_file, eth_accounts).create(args.output_file, eth_accounts)

    # await scan_session.__ainit__()
    # scan_session.create_account_dict(eth_accounts)
    chain_id_list_len = chain_id_list.__len__()
    # call_count = _batch_size * chain_id_list_len
    await scan_session.create_account_dict(eth_accounts, chain_id_list)
    # pprint.pprint(scan_session.acct_map)

    #print('Chain id len:  %s' % chain_id_list_len)
    # print('Calls: ', call_count)
    cp.output('Loaded %s accounts, %s chains' % (len(eth_accounts), chain_id_list_len))
    # call_count = (batch_size_ * chain_id_list_len)
    if len(eth_accounts) > _batch_size:
        batches = divide_chunks(eth_accounts, batch_size)
        cp.notice('We have %s batches of %s accounts' % (len(batches), _batch_size))
    else:
        batches = [eth_accounts]
    progress = tqdm.tqdm(batches)

    for cn, c in enumerate(chain_id_list):
        cp.output('Running chain: %s' % c)

        for x, batch in enumerate(progress):
            cp.output('Batch %s/%s, chain: %s/%s' % (x + 1, len(batches), cn, len(chain_id_list)))
            tasks = set()
            price_tasks = set()
            token_list = []
            # tokens_ret = await api.get_tokens(acct.address, _cid)
            for acct in batch:
                if acct:
                    task = asyncio.create_task(wrap_get_tokens(api, acct, c, output_file, scan_session))
                    task.add_done_callback(tasks.discard)
                    tasks.add(task)
            batch_results = [await _ret for _ret in asyncio.as_completed(tasks)]
            cp.output('Found %s results' % batch_results.__len__())
            cp.debug(batch_results)
            res_len = 0
            tasks.clear()
            await asyncio.sleep(0.1)

            for z, br in enumerate(batch_results):
                if br:
                    # print(br)
                    res_len += 1
                    _addr = br.get('address')
                    _key = br.get('key')

                    tokens: list[dict] = br.get('result').get('tokens')
                    native_qty = int(br.get('result').get('native'))
                    br.get('result').pop('native')
                    if native_qty > 0 or len(tokens):
                        # print(tokens, native_qty, c)
                        tokens.append({'address': 'native', 'amount': native_qty, 'decimals': 18, 'cid': c})
                        if tokens:
                            task = asyncio.create_task(api.get_price([token['address'] for token in tokens], c))
                            task.add_done_callback(price_tasks.discard)
                            price_tasks.add(task)
            cp.output('Found %s results' % res_len)
            price_results = [await _ret for _ret in asyncio.as_completed(price_tasks)]

            if len(price_results):
                for _tokens in price_results:
                    # print(_tokens)
                    if _tokens:
                        for k, tp in enumerate(_tokens):
                            tp: Union[TokenPrice, None]
                            if tp is not None:
                                token_list.append(tp)
                    await scan_session.set_token_prices(token_list)
            price_tasks.clear()
            token_list.clear()
            # batches.clear()
        await scan_session.dump()
        await asyncio.sleep(0)

    return await scan_session.finalize()


if __name__ == '__main__':
    cp = ColorPrint(0)
    dotenv.load_dotenv()
    project_id = os.environ.get('PROJECT_ID')
    project_server_key = os.environ.get('PROJECT_SERVER_KEY')

    # api = ParticleApi(project_id, project_server_key)
    args = cli_args()

    if args.command == 'single':
        chain_id = args.chain_id
        _address = helpers.load_keys(args.address)
        cp.output(f'Check: {_address}')
        ret = asyncio.run(single_main(_address[0].address, chain_id))
        pprint.pprint(json.dumps(ret))
    if args.command == 'file_list':
        chain_id = args.chain_id
        file = args.file
        _output_file = args.output_file
        batch_size = args.batch
        ret = asyncio.run(file_list_main(file, chain_id, _output_file, batch_size))
        if ret:
            pprint.pprint(ret)
