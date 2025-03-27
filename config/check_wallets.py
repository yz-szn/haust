import json
import time 
from web3 import Web3
from concurrent.futures import ThreadPoolExecutor
from utils.logger import log
from colorama import Fore, Style, init
import logging
from datetime import datetime
import os

init(autoreset=True)

RPC_URL = "https://rpc-testnet.haust.app"
NFT_CONTRACTS = {
    "NFT1": "0x6B3f185C4c9246c52acE736CA23170801D636c8E",
    "NFT2": "0x28e50a3632961dA179b2Afca4675714ea22E7BB7", 
    "NFT3": "0xdaF34a049EfAa3cc9ad4635D8A710Fae819aca5c"
}
HAUST_TOKEN_DECIMALS = 18
MAX_WORKERS = 10 

NFT_ABI = [
    {
        "constant": True,
        "inputs": [{"name": "owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "", "type": "uint256"}],
        "type": "function"
    }
]

def init_web3():
    web3 = Web3(Web3.HTTPProvider(RPC_URL))
    if not web3.is_connected():
        log("CHECK", "Gagal terhubung ke RPC!", "ERROR")
        raise ConnectionError("Koneksi RPC gagal")
    return web3

web3 = init_web3()

contracts = {
    name: web3.eth.contract(address=address, abi=NFT_ABI)
    for name, address in NFT_CONTRACTS.items()
}

logging.basicConfig(
    format='[ CHECK ] [%(asctime)s] [%(levelname)s] [%(message)s]',
    level=logging.INFO,
    datefmt='%d/%m/%Y %H:%M',
)

def load_wallets():
    try:
        with open("wallets.json", "r") as file:
            data = json.load(file)
            if not isinstance(data, list):
                raise ValueError("Format file wallet salah")
            return data
    except FileNotFoundError:
        log("CHECK", "File wallets.json tidak ditemukan!", "ERROR")
        exit(1)
    except (json.JSONDecodeError, ValueError) as e:
        log("CHECK", f"Error membaca wallet: {str(e)}", "ERROR")
        exit(1)

def get_balance_with_retry(contract_func, address, retries=3):
    for attempt in range(retries):
        try:
            return contract_func(address).call()
        except Exception as e:
            if attempt == retries - 1:
                raise
            time.sleep(1)

def process_wallet(wallet):
    address = wallet["address"]
    balances = {}
    
    try:
        balances = {
            name: get_balance_with_retry(contract.functions.balanceOf, address)
            for name, contract in contracts.items()
        }
        balances['HAUST'] = web3.eth.get_balance(address) / (10 ** HAUST_TOKEN_DECIMALS)
        
    except Exception as e:
        log("CHECK", f"Error memproses {address}: {str(e)}", "ERROR")
        return wallet, "error"
    colors = {
        'HAUST': Fore.GREEN if balances['HAUST'] > 0 else Fore.RED,
        'NFT1': Fore.GREEN if balances['NFT1'] > 0 else Fore.RED,
        'NFT2': Fore.GREEN if balances['NFT2'] > 0 else Fore.RED,
        'NFT3': Fore.GREEN if balances['NFT3'] > 0 else Fore.RED
    }

    log_msg = (
        f"{Fore.CYAN}{address:<42} | "
        f"{colors['HAUST']}{balances['HAUST']:>6.3f} HAUST{Style.RESET_ALL} | "
        f"{colors['NFT1']}{balances['NFT1']:>3} NFT1{Style.RESET_ALL} | "
        f"{colors['NFT2']}{balances['NFT2']:>3} NFT2{Style.RESET_ALL} | "
        f"{colors['NFT3']}{balances['NFT3']:>3} NFT3"
    )
    
    log("CHECK", log_msg, "INFO")

    if all(balances[asset] > 0 for asset in ['HAUST', 'NFT1', 'NFT2', 'NFT3']):
        return wallet, "with_balance"
    return wallet, "without_balance"

def save_results(data, filename):
    try:
        with open(filename, "w") as file:
            json.dump(data, file, indent=4)
        log("CHECK", f"{Fore.CYAN}Data tersimpan di {filename}", "INFO")
    except Exception as e:
        log("CHECK", f"Gagal menyimpan {filename}: {str(e)}", "ERROR")

def run():
    try:
        wallets = load_wallets()
        log("CHECK", f"{Fore.YELLOW}Memproses {len(wallets)} wallet...{Style.RESET_ALL}", "INFO")
        
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            results = list(executor.map(process_wallet, wallets))
        categorized = {
            "with_balance": [],
            "without_balance": [],
            "error": []
        }
        
        for wallet, status in results:
            categorized[status].append(wallet)
        save_results(categorized["with_balance"], "wallets_with_balance.json")
        save_results(categorized["without_balance"], "wallets_without_balance.json")
        
        log("CHECK", f"\n{Fore.YELLOW}SUMMARY:{Style.RESET_ALL}")
        log("CHECK", f"Wallet dengan balance: {len(categorized['with_balance'])}")
        log("CHECK", f"Wallet tanpa balance: {len(categorized['without_balance'])}")
        log("CHECK", f"Error: {len(categorized['error'])}")

    except Exception as e:
        log("CHECK", f"Error utama: {str(e)}", "ERROR")
        exit(1)

if __name__ == "__main__":
    run()
