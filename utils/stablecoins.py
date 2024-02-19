from typing import Union

from eth_utils import to_checksum_address


class StableContract:
    ethereum = eth = to_checksum_address('0x6B175474E89094C44Da98b954EedeAC495271d0F')
    arbitrum = to_checksum_address('0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1')
    polygon = to_checksum_address('0x8f3Cf7ad23Cd3CaDbD9735AFf958023239c6A063')
    bnb = bsc = binance = to_checksum_address('0x1AF3F329e8BE154074D8769D1FFa4eE058B1DBc3')
    optimism = to_checksum_address('0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1')
    avalanche = to_checksum_address('0xd586E7F844cEa2F87f50152665BCbc2C279D8d70')
    fantom = to_checksum_address('0x8D11eC38a3EB5E956B052f67Da8Bdc9bef8Abf3E')
    aurora = to_checksum_address('0xe3520349f477a5f6eb06107066048508498a291b')

    ethereum_alt = eth_alt = to_checksum_address('0xdAC17F958D2ee523a2206206994597C13D831ec7')
    arbitrum_alt = to_checksum_address('0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9')
    polygon_alt = to_checksum_address('0xc2132D05D31c914a87C6611C10748AEb04B58e8F')
    bnb_alt = bsc_alt = binance_alt = to_checksum_address('0x55d398326f99059fF775485246999027B3197955')
    optimism_alt = to_checksum_address('0x94b008aA00579c1307B0EF2c499aD98a8ce58e58')
    avalanche_alt = to_checksum_address('0xde3A24028580884448a5397872046a019649b084')
    fantom_alt = to_checksum_address('0x1B27A9dE6a775F98aaA5B90B62a4e2A0B84DbDd9')
    aurora_alt = to_checksum_address('0x368ebb46aca6b8d0787c96b2b20bd3cc3f2c45f7')


    def __init__(self):
        self.__all__ = []
        for x in self.__dir__():
            if '__' in x or '_alt' in x:
                pass
            elif x in ['dai', 'alt', 'check_net_supported']:
                pass
            else:
                self.__all__.append(x)
    def dai(self, network: str):
        try:
            return getattr(self, network)
        except AttributeError:
            return None

    def alt(self, network: str):
        return getattr(self, f'{network}_alt')

    def check_net_supported(self, network: str) -> bool:
        for x in self.__all__:
            if x.lower() == network.lower():
                return True
        return False


