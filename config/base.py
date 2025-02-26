import json
import time 
from web3 import Web3
from concurrent.futures import ThreadPoolExecutor
from utils.logger import log
from colorama import Fore, Style, init
import logging
from datetime import datetime

init(autoreset=True)

RPC_URL = "https://mainnet.base.org" 
NFT_CONTRACT_ADDRESS = "0x6a53b52e6bE1fa6E0098A2d1546aEfFa058a6Adc"

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

nft_contract = web3.eth.contract(address=NFT_CONTRACT_ADDRESS, abi=NFT_ABI)

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
        balance_nft = nft_contract.functions.balanceOf(address).call()
    except Exception as e:
        log("CHECK", f"Gagal mendapatkan saldo NFT untuk {address}: {str(e)}", "ERROR")
        balance_nft1 = 0

    nft_color = Fore.GREEN if balance_nft > 0 else Fore.RED

    log("CHECK", f"{Fore.CYAN}{address:<42} | {nft_color}{balance_nft:>1} NFT{Style.RESET_ALL} ", "INFO")

    if balance_nft > 0:
        return wallet, "with_balance"
    else:
        return wallet, "without_balance"

async def run():
    wallets = load_wallets()
    log("CHECK", f"{Fore.YELLOW}Total wallet yang diproses: {len(wallets)}{Style.RESET_ALL}", "INFO")

    wallets_with_balance = []
    wallets_without_balance = []
    max_workers = 4  
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(process_wallet, wallets))

    for wallet, status in results:
        if status == "with_balance":
            wallets_with_balance.append(wallet)
        else:
            wallets_without_balance.append(wallet)

    try:
        with open("wallets_with_NFT_BASE.json", "w") as file:
            json.dump(wallets_with_balance, file, indent=4)

        log("CHECK", f"{Fore.CYAN}Hasil pengecekan telah disimpan.", "INFO")
    except Exception as e:
        log("CHECK", f"Gagal menyimpan file JSON: {str(e)}", "ERROR")

    log("CHECK", f"{Fore.YELLOW}Total wallet dengan saldo NFT: {len(wallets_with_balance)}{Style.RESET_ALL}", "INFO")
    log("CHECK", f"{Fore.YELLOW}Total wallet tanpa saldo NFT: {len(wallets_without_balance)}{Style.RESET_ALL}", "INFO")

if __name__ == "__main__":
    import asyncio
    asyncio.run(run())