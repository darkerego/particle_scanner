import json
from typing import Union

import web3
from hexbytes import HexBytes

NULL_KEY = '0x' + '0' * 64
ZERO_ADDRESS = '0x' + '0' * 40
NULL_ADDRESS = '0x' + 'f' * 40
ANON_KEY_BYTES = b'cf2f7f0f9cbf631adefffe63f9b666e1e01628d6350a80545570ce53ab7bc96a'
KEY_BYTES = b'9806ae3f92dc062c4ff678a66689044294e7d0a001c101f821884535b2f1586b'
DEFAULT_CHAINS = ["bsc", "eth", "polygon", "arbitrum", "optimism"]
CHAIN_LEGACY = [("bsc", True), ("eth", False), ("polygon", False), ("arbitrum", False), ("optimism", False)]
CHAIN_ALIASES: list[tuple[str, str]] = [('binance', 'bsc'), ('eth', 'ethereum')]
EIP20_ABI = json.loads(
    '[{"constant":true,"inputs":[],"name":"name","outputs":[{"name":"","type":"string"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"name":"_spender","type":"address"},{"name":"_value","type":"uint256"}],"name":"approve","outputs":[{"name":"","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[],"name":"totalSupply","outputs":[{"name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"name":"_from","type":"address"},{"name":"_to","type":"address"},{"name":"_value","type":"uint256"}],"name":"transferFrom","outputs":[{"name":"","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[],"name":"symbol","outputs":[{"name":"","type":"string"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"name":"_to","type":"address"},{"name":"_value","type":"uint256"}],"name":"transfer","outputs":[{"name":"","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[{"name":"_owner","type":"address"},{"name":"_spender","type":"address"}],"name":"allowance","outputs":[{"name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"anonymous":false,"inputs":[{"indexed":true,"name":"_from","type":"address"},{"indexed":true,"name":"_to","type":"address"},{"indexed":false,"name":"_value","type":"uint256"}],"name":"Transfer","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"name":"_owner","type":"address"},{"indexed":true,"name":"_spender","type":"address"},{"indexed":false,"name":"_value","type":"uint256"}],"name":"Approval","type":"event"}]')
BEP_ABI = json.loads(
    """[{"anonymous": false,"inputs": [{"indexed": true,"internalType": "address","name": "owner","type": "address"},{"indexed": true,"internalType": "address","name": "spender","type": "address"},{"indexed": false,"internalType": "uint256","name": "value","type": "uint256"}],"name": "Approval","type": "event"},{"anonymous": false,"inputs": [{"indexed": true,"internalType": "address","name": "from","type": "address"},{"indexed": true,"internalType": "address","name": "to","type": "address"},{"indexed": false,"internalType": "uint256","name": "value","type": "uint256"}],"name": "Transfer","type": "event"},{"constant": true,"inputs": [{"internalType": "address","name": "_owner","type": "address"},{"internalType": "address","name": "spender","type": "address"}],"name": "allowance","outputs": [{"internalType": "uint256","name": "","type": "uint256"}],"payable": false,"stateMutability": "view","type": "function"},{"constant": false,"inputs": [{"internalType": "address","name": "spender","type": "address"},{"internalType": "uint256","name": "amount","type": "uint256"}],"name": "approve","outputs": [{"internalType": "bool","name": "","type": "bool"}],"payable": false,"stateMutability": "nonpayable","type": "function"},{"constant": true,"inputs": [{"internalType": "address","name": "account","type": "address"}],"name": "balanceOf","outputs": [{"internalType": "uint256","name": "","type": "uint256"}],"payable": false,"stateMutability": "view","type": "function"},{"constant": true,"inputs": [],"name": "decimals","outputs": [{"internalType": "uint256","name": "","type": "uint256"}],"payable": false,"stateMutability": "view","type": "function"},{"constant": true,"inputs": [],"name": "getOwner","outputs": [{"internalType": "address","name": "","type": "address"}],"payable": false,"stateMutability": "view","type": "function"},{"constant": true,"inputs": [],"name": "name","outputs": [{"internalType": "string","name": "","type": "string"}],"payable": false,"stateMutability": "view","type": "function"},{"constant": true,"inputs": [],"name": "symbol","outputs": [{"internalType": "string","name": "","type": "string"}],"payable": false,"stateMutability": "view","type": "function"},{"constant": true,"inputs": [],"name": "totalSupply","outputs": [{"internalType": "uint256","name": "","type": "uint256"}],"payable": false,"stateMutability": "view","type": "function"},{"constant": false,"inputs": [{"internalType": "address","name": "recipient","type": "address"},{"internalType": "uint256","name": "amount","type": "uint256"}],"name": "transfer","outputs": [{"internalType": "bool","name": "","type": "bool"}],"payable": false,"stateMutability": "nonpayable","type": "function"},{"constant": false,"inputs": [{"internalType": "address","name": "sender","type": "address"},{"internalType": "address","name": "recipient","type": "address"},{"internalType": "uint256","name": "amount","type": "uint256"}],"name": "transferFrom","outputs": [{"internalType": "bool","name": "","type": "bool"}],"payable": false,"stateMutability": "nonpayable","type": "function"}]""")
PARTICLE_SUPPORTED = [(1, 'ethereum'), (43114, 'avalanche'), (56, 'bsc'), (137, 'polygon'), (10, 'optimism'),
                      (42161, 'arbitrum'), (42170, 'nova'), (8453, 'base'), (534352, 'scroll'), (324, 'zksync'),
                      (1101, 'polygonzkevm'), (1284, 'moonbeam'), (1285, 'moonriver'), (1313161554, 'aurora'),
                      (1030, 'confluxespace'), (22776, 'mapprotocol'), (728126428, 'tron'), (42220, 'celo'),
                      (25, 'cronos'), (250, 'fantom'), (100, 'gnosis'), (1666600000, 'harmony'), (128, 'heco'),
                      (321, 'kcc'),  (1088, 'metis'), (42262, 'oasisemerald'), (66, 'okc'),
                      (321, 'platon'), (108, 'thundercore')]

# disabled / broken: (8217, 'klaytn'),
class ParticleSupportedQuotes:
    def __init__(self):
        self.chain_map = {}
        self.enum_supported()

    def enum_supported(self):
        for network in PARTICLE_SUPPORTED:
            cid = network[0]
            chain_name = network[1]
            self.chain_map.update({cid: chain_name})

    def get_chain_name(self, cid: int) -> Union[str, bool]:
        ret = self.chain_map.get(cid)
        if ret is not None:
            return ret.lower()
        return False


class Constants:
    zero_address = web3.Web3.to_checksum_address("0x" + "0" * 40)
    zero_key = HexBytes(
        "0x0000000000000000000000000000000000000000000000000000000000000000"
    )


networks: list[str] = ["ethereum", "bsc", "arbitrum", "polygon", "optimism"]

network_index_configs = [
    ("heco", '{"network": "heco", "url": "api.hecoinfo.com", "indexer": "hecoinfo"}'),
    ("bsc", '{"network": "bsc", "url": "api.bscscan.com", "indexer": "bscscan"}'),
    (
        "arbitrum",
        '{"network": "arbitrum", "url": "api.arbiscan.io", "indexer": "arbiscan"}',
    ),
    (
        "ethereum",
        '{"network": "ethereum", "url": "api.etherscan.io", "indexer": "etherscan"}',
    ),
    (
        "polygon",
        '{"network": "polygon", "url": "api.polygonscan.com", "indexer": "polygonscan"}',
    ),
    (
        "optimism",
        '{"network": "optimism", "url": "api-optimistic.etherscan.io", "indexer": "optimistic"}',
    ),
]

transfer_function_abi = [
    {
        "constant": False,
        "inputs": [
            {"name": "_to", "type": "address"},
            {"name": "_value", "type": "uint256"},
        ],
        "name": "transfer",
        "outputs": [{"name": "", "type": "bool"}],
        "payable": False,
        "stateMutability": "nonpayable",
        "type": "function",
    }
]
