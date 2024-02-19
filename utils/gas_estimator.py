# PLEASE GO THROUGH THE README.md FILE BEFORE RUNNING THE CODE ##

# import Web3 class from web3 module
import math
# import the in-built statistics module
import statistics

import web3
from eth_typing import ChecksumAddress
# from eth_defi.token import fetch_erc20_details
from eth_utils import to_wei, from_wei

from data.constants import EIP20_ABI, BEP_ABI


# Setting node endpoint value
# CHAINSTACK_NODE_ENDPOINT = '<NODE_ENDPOINT>'


def gas_estimator(w3: web3.Web3, from_acct: ChecksumAddress, to_account: ChecksumAddress, ether_value: float,
                  priority='low', token_address: ChecksumAddress = None, token_value: int = None):
    print(f'Selected: {priority}')

    if w3.eth.chain_id == 137:
        print('[*] Notice: setting gas priority to 2x normal because polygon is gay.')
        # priority = 'high'
        poly_fix = True
        arb_fix = False
    elif w3.eth.chain_id == 42161:
        arb_fix = True
        poly_fix = False
    else:
        poly_fix = False
        arb_fix = False
    basefee_percentage_multiplier = {
        "low": 1.10,  # 10% increase
        "medium": 1.20,  # 20% increase
        "high": 1.25,  # 25% increase
        "insane": 1.99
    }
    priority_fee_percentage_multiplier = {
        "low": .94,  # 6% decrease
        "medium": .97,  # 3% decrease
        "high": .98,  # 2% decrease
        "insane": .99
    }

    # the minimum PRIORITY FEE that should be paid,
    #  corresponding to the user priority (in WEI denomination)
    minimum_fee = {
        "low": 1000000000,
        "medium": 1500000000,
        "high": 2000000000,
        "insane": 3000000000

    }

    #  a dictionary for storing the sorted priority fee
    fee_by_priority = {
        "low": [],
        "medium": [],
        "high": [],
        "insane": []
    }
    fee_history = w3.eth.fee_history(20, 'latest', [10, 20, 30, 40])

    # get the basefeepergas of the latest block
    latest_base_fee_per_gas = fee_history["baseFeePerGas"][-1]

    # Setting the ether value to be transferred
    # ETH_VALUE = .5
    # Calculating the estimated usage of gas in the following transaction
    if token_address is None:
        estimate_gas_used = w3.eth.estimate_gas(
            {'to': to_account, 'from': from_acct,
             'value': to_wei(float(ether_value), "ether")})
    else:
        assert token_value is not None
        if w3.eth.chain_id == 56:
            _abi = BEP_ABI
        else:
            _abi = EIP20_ABI
        unicorns = w3.eth.contract(address=token_address, abi=_abi)
        # decimals = unicorns.functions.decimals().call()

        # token_details = fetch_erc20_details(web3, contract_address)
        # raw_amount = token_details.convert_to_raw(decimal.Decimal(ETH_VALUE))
        estimate_gas_used = unicorns.functions.transfer(to_account, int(token_value)).estimate_gas(
            {'from': from_acct})
    for feeList in fee_history["reward"]:
        fee_by_priority["low"].append(feeList[0])
        fee_by_priority["medium"].append(feeList[1])
        fee_by_priority["high"].append(feeList[2])
        fee_by_priority["insane"].append(feeList[3])
    for key in fee_by_priority:
        adjusted_base_fee = latest_base_fee_per_gas * basefee_percentage_multiplier[key]
        median_of_fee_list = statistics.median(fee_by_priority[key])
        adjusted_fee_median = (
                median_of_fee_list * priority_fee_percentage_multiplier[key])
        adjusted_fee_median = adjusted_fee_median if adjusted_fee_median > minimum_fee[
            key] else minimum_fee[key]
        suggested_max_priority_fee_per_gas_gwei = from_wei(adjusted_fee_median, "gwei")
        # if poly_fix:
            # Polygon has stupid high fees in terms of gwei vs every other network
            #suggested_max_priority_fee_per_gas_gwei = suggested_max_priority_fee_per_gas_gwei * 5
        # [optional] round the amount
        suggested_max_priority_fee_per_gas_gwei = round(
            math.ceil(suggested_max_priority_fee_per_gas_gwei), 5)
        # calculate the Max fee per gas
        suggested_max_fee_per_gas = (adjusted_base_fee + adjusted_fee_median)
        # convert to gwei denomination
        suggested_max_fee_per_gas_gwei = from_wei(suggested_max_fee_per_gas, "gwei")
        #if poly_fix:
        #    suggested_max_fee_per_gas_gwei = suggested_max_fee_per_gas_gwei * 3
        # [optional] round the amount to the given decimal precision
        suggested_max_fee_per_gas_gwei = round(int(math.ceil(suggested_max_fee_per_gas_gwei)), 9)
        # calculate the total gas fee
        total_gas_fee = suggested_max_fee_per_gas_gwei * estimate_gas_used
        # convert the value to gwei denomination
        total_gas_fee_gwei = from_wei(total_gas_fee, "gwei")
        # [optional] round the amount
        total_gas_fee_gwei = round(total_gas_fee_gwei, 8)
        pr = f"PRIORITY: {key.upper()}\nMAX PRIORITY FEE (GWEI): {suggested_max_priority_fee_per_gas_gwei}"
        pr += (f"\nMAX FEE (GWEI) : {suggested_max_fee_per_gas_gwei}\nGAS PRICE (ETH): {total_gas_fee_gwei}, "
               f"wei: {total_gas_fee}")
        print(pr)
        print("=" * 80)  # guess what this does ?

        if key.upper() == priority.upper():
            # print()
            return (int(float(suggested_max_priority_fee_per_gas_gwei)), int(math.ceil(suggested_max_fee_per_gas_gwei)),
                    int(math.ceil(total_gas_fee)))




