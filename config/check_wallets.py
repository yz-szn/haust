import json
import time 
from web3 import Web3
from concurrent.futures import ThreadPoolExecutor
from utils.logger import log
from colorama import Fore, Style, init
import logging
from datetime import datetime

init(autoreset=True)

RPC_URL = "https://rpc-testnet.haust.app"
NFT1_CONTRACT_ADDRESS = "0x6B3f185C4c9246c52acE736CA23170801D636c8E" 
NFT2_CONTRACT_ADDRESS = "0x28e50a3632961dA179b2Afca4675714ea22E7BB7" 
HAUST_TOKEN_DECIMALS = 18

NFT_ABI = [
    {
        "constant": True,
        "inputs": [{"name": "owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "", "type": "uint256"}],
        "type": "function"
    }
]

web3 = Web3(Web3.HTTPProvider(RPC_URL))
if not web3.is_connected():
    log("CHECK", "Gagal terhubung ke RPC!", "ERROR")
    exit()

nft1_contract = web3.eth.contract(address=NFT1_CONTRACT_ADDRESS, abi=NFT_ABI)
nft2_contract = web3.eth.contract(address=NFT2_CONTRACT_ADDRESS, abi=NFT_ABI)

logging.basicConfig(
    format='[ CHECK ] [%(asctime)s] [%(levelname)s] [%(message)s]',
    level=logging.INFO,
    datefmt='%d/%m/%Y %H:%M',
)

def load_wallets():
    try:
        with open("wallets.json", "r") as file:
            return json.load(file)
    except FileNotFoundError:
        log("CHECK", "File wallets.json tidak ditemukan!", "ERROR")
        exit()
    except json.JSONDecodeError:
        log("CHECK", "Format JSON salah di wallets.json!", "ERROR")
        exit()

def process_wallet(wallet):
    address = wallet["address"]

    try:
        balance_nft1 = nft1_contract.functions.balanceOf(address).call()
    except Exception as e:
        log("CHECK", f"Gagal mendapatkan saldo NFT1 untuk {address}: {str(e)}", "ERROR")
        balance_nft1 = 0

    try:
        balance_nft2 = nft2_contract.functions.balanceOf(address).call()
    except Exception as e:
        log("CHECK", f"Gagal mendapatkan saldo NFT2 untuk {address}: {str(e)}", "ERROR")
        balance_nft2 = 0

    try:
        balance_haust = web3.eth.get_balance(address) / (10 ** HAUST_TOKEN_DECIMALS)
    except Exception as e:
        log("CHECK", f"Gagal mendapatkan saldo HAUST untuk {address}: {str(e)}", "ERROR")
        balance_haust = 0

    haust_color = Fore.GREEN if balance_haust > 0 else Fore.RED
    nft1_color = Fore.GREEN if balance_nft1 > 0 else Fore.RED
    nft2_color = Fore.GREEN if balance_nft2 > 0 else Fore.RED

    log("CHECK", f"{Fore.CYAN}{address:<42} | {haust_color}{balance_haust:>1f} HAUST{Style.RESET_ALL} | {nft1_color}{balance_nft1:>1} NFT1{Style.RESET_ALL} | {nft2_color}{balance_nft2:>1} NFT2{Style.RESET_ALL}", "INFO")

    if balance_nft1 > 0 and balance_nft2 > 0 and balance_haust > 0:
        return wallet, "with_balance"
    else:
        return wallet, "without_balance"

async def run():
    wallets = load_wallets()
    log("CHECK", f"{Fore.YELLOW}Total wallet yang diproses: {len(wallets)}{Style.RESET_ALL}", "INFO")

    wallets_with_balance = []
    wallets_without_balance = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(process_wallet, wallets))

    for wallet, status in results:
        if status == "with_balance":
            wallets_with_balance.append(wallet)
        else:
            wallets_without_balance.append(wallet)

    try:
        with open("wallets_with_balance.json", "w") as file:
            json.dump(wallets_with_balance, file, indent=4)

        with open("wallets_without_balance.json", "w") as file:
            json.dump(wallets_without_balance, file, indent=4)

        log("CHECK", f"{Fore.CYAN}Hasil pengecekan telah disimpan.", "INFO")
    except Exception as e:
        log("CHECK", f"Gagal menyimpan file JSON: {str(e)}", "ERROR")

    log("CHECK", f"{Fore.YELLOW}Total wallet dengan saldo HAUST & NFT: {len(wallets_with_balance)}{Style.RESET_ALL}", "INFO")
    log("CHECK", f"{Fore.YELLOW}Total wallet tanpa saldo HAUST & NFT: {len(wallets_without_balance)}{Style.RESET_ALL}", "INFO")

if __name__ == "__main__":
    import asyncio
    asyncio.run(run())