import json
import asyncio
from web3 import Web3
from utils.logger import log

RPC_URL = "https://rpc-testnet.haust.app"
CHAIN_ID = 1523903251
SYMBOL = "HAUST"
BATCH_SIZE = 10 

def load_wallets():
    try:
        with open("wallets_penerima.json", "r") as file:
            wallets_penerima = json.load(file)
        with open("wallets_pengirim.json", "r") as file:
            wallets_pengirim = json.load(file)
        return wallets_pengirim, wallets_penerima
    except FileNotFoundError:
        log("ERROR", "File wallet tidak ditemukan!", "ERROR")
        return [], []

async def send_transaction(web3, sender_wallet, receiver_wallet, amount_wei):
    sender_address = sender_wallet["address"]
    private_key = sender_wallet["privateKey"]
    receiver_address = receiver_wallet["address"]
    
    try:
        balance = web3.eth.get_balance(sender_address)
        if balance < amount_wei:
            log("WARNING", f"Saldo tidak mencukupi di {sender_address}. Melewati wallet ini.", "WARNING")
            return
        
        nonce = web3.eth.get_transaction_count(sender_address)
        tx = {
            "to": receiver_address,
            "value": amount_wei,
            "gas": 21000,
            "gasPrice": web3.eth.gas_price,
            "nonce": nonce,
            "chainId": CHAIN_ID
        }
        
        signed_tx = web3.eth.account.sign_transaction(tx, private_key)
        tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
        log("AUTO_TRANSFER", f"Transaksi terkirim dari {sender_address} ke {receiver_address} dengan hash: {web3.to_hex(tx_hash)}", "SUCCESS")
    except Exception as e:
        log("ERROR", f"Gagal mengirim transaksi dari {sender_address} ke {receiver_address}: {str(e)}", "ERROR")

async def process_batch(web3, batch_pengirim, batch_penerima, amount_wei):
    tasks = [
        send_transaction(web3, sender_wallet, receiver_wallet, amount_wei)
        for sender_wallet, receiver_wallet in zip(batch_pengirim, batch_penerima)
    ]
    await asyncio.gather(*tasks)

async def run():
    """Menjalankan proses auto transfer saat dipilih di menu"""
    log("INFO", "Memulai Auto Transfer...", "INFO")

    web3 = Web3(Web3.HTTPProvider(RPC_URL))

    if not web3.is_connected():
        log("ERROR", "Gagal terhubung ke blockchain.", "ERROR")
        return

    log("SUCCESS", "Berhasil terhubung ke blockchain.", "SUCCESS")

    wallets_pengirim, wallets_penerima = load_wallets()
    
    log("INFO", f"Total wallet penerima terdeteksi: {len(wallets_penerima)}", "INFO")
    log("INFO", f"Total wallet pengirim terdeteksi: {len(wallets_pengirim)}", "INFO")

    if not wallets_pengirim or not wallets_penerima:
        log("ERROR", "Tidak ada wallet yang tersedia untuk transaksi!", "ERROR")
        return

    try:
        amount_per_wallet = float(input("Berapa yang ingin Anda kirim per walletnya: "))
    except ValueError:
        log("ERROR", "Masukkan angka yang valid.", "ERROR")
        return

    amount_wei = web3.to_wei(amount_per_wallet, "ether")
    for i in range(0, len(wallets_pengirim), BATCH_SIZE):
        batch_pengirim = wallets_pengirim[i:i + BATCH_SIZE]
        batch_penerima = wallets_penerima[i:i + BATCH_SIZE]

        log("INFO", f"Memproses batch {i // BATCH_SIZE + 1}...", "INFO")

        await process_batch(web3, batch_pengirim, batch_penerima, amount_wei)
        
        log("INFO", f"Selesai memproses batch {i // BATCH_SIZE + 1}.", "SUCCESS")
    
    log("INFO", "Selesai mengirim semua transaksi.", "SUCCESS")
if __name__ == "__main__":
    asyncio.run(run())