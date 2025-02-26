import json
import time
import random
import threading
from colorama import init, Fore, Style
from web3 import Web3
from utils.logger import log
from urllib.parse import urlparse

RPC_URL = "https://rpc-testnet.haust.app"
NFT1_CONTRACT_ADDRESS = "0x6B3f185C4c9246c52acE736CA23170801D636c8E"
NFT2_CONTRACT_ADDRESS = "0x28e50a3632961dA179b2Afca4675714ea22E7BB7"
NFT_ABI = [
    {"inputs": [], "name": "safeMint", "outputs": [], "stateMutability": "nonpayable", "type": "function"},
    {"inputs": [{"internalType": "address", "name": "owner", "type": "address"}], "name": "balanceOf", "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"}
]

MAX_RETRIES = 2
TIMEOUT_SECONDS = 60
THREAD_COUNT = 5  # Jumlah thread yang akan digunakan

class LogColor:
    GREEN = "\033[32m"
    RED = "\033[31m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    RESET = "\033[0m"

def read_wallets():
    try:
        with open("wallets.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        log("MINT_NFT", "Tidak ada file wallets.json", "ERROR")
        return []
    except json.JSONDecodeError:
        log("MINT_NFT", "Format wallets.json tidak valid!", "ERROR")
        return []

def read_proxies():
    try:
        with open("proxy.txt", "r") as f:
            return [line.strip() for line in f.readlines() if line.strip()]
    except FileNotFoundError:
        log("MINT_NFT", "Tidak ada file proxy.txt. Request akan berjalan tanpa proxy.", "WARN")
        return []

def parse_proxy(proxy_str):
    """Parse proxy untuk mendukung berbagai format (ip:port, protocol://ip:port, http, socks5, socks4)."""
    parsed = urlparse(proxy_str)
    if parsed.scheme in ['http', 'https', 'socks5', 'socks4']:
        return {parsed.scheme: proxy_str}
    return {'http': proxy_str, 'https': proxy_str}

def log_colored(action, message, status):
    if status == "SUCCESS":
        color = LogColor.GREEN
    elif status == "ERROR":
        color = LogColor.RED
    elif status == "INFO":
        color = LogColor.YELLOW
    else:
        color = LogColor.BLUE
    log(action, f"{color}{message}{LogColor.RESET}", status)

def check_nft_balance(address, web3, contract_address):
    try:
        contract = web3.eth.contract(address=contract_address, abi=NFT_ABI)
        balance = contract.functions.balanceOf(address).call()
        log_colored("MINT_NFT", f"Saldo NFT untuk {address}: {balance}", "INFO")
        return balance
    except Exception as e:
        log_colored("MINT_NFT", f"Error saat memeriksa saldo NFT: {str(e)}", "ERROR")
        return 0

def mint_nft(wallet, proxies, contract_address, web3_cache={}):
    address = wallet["address"]
    private_key = wallet["privateKey"]

    #log_colored("MINT_NFT", f"Memulai proses minting untuk {address}", "INFO")

    # Cek saldo NFT sebelum melakukan minting
    web3 = web3_cache.get(None, Web3(Web3.HTTPProvider(RPC_URL)))
    balance = check_nft_balance(address, web3, contract_address)
    if balance > 0:
        log_colored("MINT_NFT", f"NFT sudah ada di wallet {address}. Proses minting dibatalkan.", "INFO")
        return None

    retries = 0
    while retries < MAX_RETRIES:
        proxy = random.choice(proxies) if proxies else None
        proxy_dict = parse_proxy(proxy) if proxy else {}

        try:
            if proxy not in web3_cache:
                web3_cache[proxy] = Web3(Web3.HTTPProvider(RPC_URL, request_kwargs={"proxies": proxy_dict}))
            
            web3 = web3_cache[proxy]

            if not web3.is_connected():
                log_colored("MINT_NFT", f"Gagal terhubung ke RPC dengan proxy {proxy}, mencoba ulang...", "WARN")
                retries += 1
                continue

            contract = web3.eth.contract(address=contract_address, abi=NFT_ABI)
            account = web3.eth.account.from_key(private_key)

            gas_price = int(web3.eth.gas_price * 1.25)

            transaction = contract.functions.safeMint().build_transaction({
                "from": account.address,
                "gas": 250000,
                "gasPrice": gas_price,
                "nonce": web3.eth.get_transaction_count(account.address),
            })

            signed_tx = web3.eth.account.sign_transaction(transaction, private_key)

            tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)

            log_colored("MINT_NFT", f"Transaksi dikirim: {tx_hash.hex()} dengan proxy {proxy}", "SUCCESS")

            receipt = web3.eth.wait_for_transaction_receipt(tx_hash, timeout=TIMEOUT_SECONDS)
            
            if receipt.status == 1:
                log_colored("MINT_NFT", f"NFT berhasil dimint! Tx: {tx_hash.hex()}", "SUCCESS")
                balance = check_nft_balance(address, web3, contract_address)
                if balance > 0:
                    log_colored("MINT_NFT", f"NFT berhasil ditambahkan ke wallet {address}", "SUCCESS")
                else:
                    log_colored("MINT_NFT", f"NFT tidak ditemukan di wallet {address}", "ERROR")

                return tx_hash.hex()
            else:
                log_colored("MINT_NFT", f"Transaksi gagal! Retrying dengan proxy baru...", "WARN")

        except Exception as e:
            if "insufficient funds" in str(e).lower():
                log_colored("MINT_NFT", f"Saldo HAUST tidak mencukupi untuk {address}. Transaksi dibatalkan.", "ERROR")
                return None 
            else:
                log_colored("MINT_NFT", f"Error saat minting NFT dengan proxy {proxy}: {str(e)}", "ERROR")

        retries += 1
        log_colored("MINT_NFT", f"Mencoba ulang ({retries}/{MAX_RETRIES}) untuk {address}...", "INFO")
        time.sleep(1)  # Mengurangi waktu sleep untuk mempercepat percobaan ulang

    log_colored("MINT_NFT", f"Semua percobaan gagal - NFT tidak berhasil dimint untuk {address}.", "ERROR")
    return None

def process_wallet_batch(wallets, proxies, contract_address):
    threads = []
    for wallet in wallets:
        thread = threading.Thread(target=mint_nft, args=(wallet, proxies, contract_address))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

def run():
    wallets = read_wallets()
    proxies = read_proxies()

    if not wallets:
        log_colored("MINT_NFT", "Tidak ada wallet untuk diproses.", "WARN")
        return

    if proxies:
        log_colored("MINT_NFT", f"Ditemukan {len(proxies)} proxy, akan digunakan secara acak.", "INFO")
    else:
        log_colored("MINT_NFT", "Tidak ada proxy yang tersedia, menjalankan tanpa proxy.", "WARN")

    log_colored("MINT_NFT", f"Ditemukan {len(wallets)} wallet, memulai proses mint NFT...", "INFO")

    print(Fore.YELLOW + "\n[=== PILIH NFT ===]")
    print(Fore.CYAN + "1. NFT1")
    print(Fore.CYAN + "2. NFT2")
    choice = input(Fore.GREEN + "Masukkan pilihan (1-2): ").strip()

    if choice == "1":
        contract_address = NFT1_CONTRACT_ADDRESS
        log_colored("MINT_NFT", "Anda memilih NFT1", "INFO")
    elif choice == "2":
        contract_address = NFT2_CONTRACT_ADDRESS
        log_colored("MINT_NFT", "Anda memilih NFT2", "INFO")
    else:
        log_colored("MINT_NFT", "Pilihan tidak valid! Mohon pilih antara 1-2.", "ERROR")
        return

    for i in range(0, len(wallets), THREAD_COUNT):
        wallet_batch = wallets[i:i + THREAD_COUNT]
        process_wallet_batch(wallet_batch, proxies, contract_address)

    log_colored("MINT_NFT", "Semua proses mint NFT selesai.", "SUCCESS")
    log_colored("MINT_NFT", "Kembali ke menu utama...", "INFO")

if __name__ == "__main__":
    run()