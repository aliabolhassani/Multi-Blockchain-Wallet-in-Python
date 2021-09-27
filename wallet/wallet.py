# Import dependencies
import subprocess
import json
import os
from dotenv import load_dotenv

# Import constants.py and necessary functions from bit and web3
from constants import *
from web3 import Web3
import bit
from eth_account import Account
from web3.auto.gethdev import w3
from web3.middleware import geth_poa_middleware
from bit.network import NetworkAPI

# Loading and setting environment variables
load_dotenv()
mnemonic = os.getenv("mnemonic")

# Function `derive_wallets` makes wallets out of a given mnemonic for any given coin
def derive_wallets(coin, mnemonic=mnemonic, numderive=3):
    command = f'php ./derive -g --mnemonic="{mnemonic}" --coin="{coin}" --numderive={numderive} --format=json'

    # Calling a system command to run a PHP program HD-Wallet
    p = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
    output, err = p.communicate()
    p_status = p.wait()

    # Parsing the output as JSON format
    return json.loads(output)


# Function `priv_key_to_account` converts privkey strings to account objects and making them ready to make transactions.
def priv_key_to_account(coin, priv_key):
    if coin == ETH:
        # Converting privkey strings to account object for Ethereum
        return Account.privateKeyToAccount(priv_key)
    elif coin == BTCTEST:
        # Converting privkey strings to account object for Bitcoin Test
        return bit.PrivateKeyTestnet(priv_key)
    else:
        # Raising exception error otherwise
        raise BaseException(f'Coin {coin} is not supported!')


# Function `create_tx` creates an unsigned transaction appropriate metadata.
def create_tx(coin, account, to, amount):
    if coin == ETH:
        # Creating an unsigned transaction appropriate metadata for Ethereum
        gas_estimate = w3.eth.estimateGas(
            {'from': account.address, 'to': to, 'value': amount}
        )
        return {
            'from': account.address,
            'to': to,
            'value': amount,
            'gasPrice': w3.eth.gasPrice,
            'gas': gas_estimate,
            'nonce': w3.eth.getTransactionCount(account.address),
            "chainId": 1111
        }

    elif coin == BTCTEST:
        # Creating an unsigned transaction appropriate metadata for Bitcoin Test
        return bit.PrivateKeyTestnet.prepare_transaction(account.address, [(to, amount, BTC)])
    else:
        # Raising exception error otherwise
        raise BaseException(f'Coin {coin} is not supported!')


# Function `send_tx` calls `create_tx`, signs and sends the transaction.
def send_tx(coin, account, to, amount):
    raw_tx = create_tx(coin, account, to, amount)

    # Signing the transactions
    signed = account.sign_transaction(raw_tx)

    if coin == ETH:
        # Sending the transactions for Ethereum
        return w3.eth.sendRawTransaction(signed.rawTransaction)
    elif coin == BTCTEST:
        # Sending the transactions for Bitcoin Test
        return NetworkAPI.broadcast_tx_testnet(signed)
    else:
        # Raising exception error otherwise
        raise BaseException(f'Coin {coin} is not supported!')


# Creating a dictionary object (coins) to store the output from `derive_wallets`.
coins = {
    ETH: derive_wallets(ETH),
    BTCTEST: derive_wallets(BTCTEST)
}

print(json.dumps(coins, indent=4, sort_keys=True))

########################
# BTC Test Transaction #
########################

# Taking a BTCTEST Private Key from generated key pairs
priv_key = coins[BTCTEST][0]['privkey']
# Setting up my accaount (Sender)
my_account = priv_key_to_account(BTCTEST, priv_key)
# Recepient's address assignment
to_address = coins[BTCTEST][2]['address']
send_result = send_tx(BTCTEST, my_account, to_address, 0.0001)

########################
# ETH Test Transaction #
########################

# Hooking up to the local PoA Ethereum RPC provider using Web3
w3 = Web3(Web3.HTTPProvider('http://127.0.0.1:8545'))
w3.middleware_onion.inject(geth_poa_middleware, layer=0)

# Taking an ETH Private Key from generated key pairs
priv_key = coins[ETH][0]['privkey']
# Setting up my accaount (Sender)
my_account = priv_key_to_account(ETH, priv_key)
# Recepient's address assignment
to_address = coins[ETH][2]['address']

# 1 Ether buterin = 10^-18 ETH (https://www.investopedia.com/terms/g/gwei-ethereum.asp)
# Sending 0.001 ETH
send_result = send_tx(ETH, my_account, to_address, 1_000_000_000_000_000)

# Converting ByteArray to Hex and print (https://stackoverflow.com/questions/19210414/byte-array-to-hex-string)
print('ETH Transaction id: 0x' + ''.join(format(x, '02x')
      for x in send_result))
