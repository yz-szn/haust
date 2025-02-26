import json
import aiohttp
import asyncio
import random
from utils.logger import log

FAUCET_URL = "https://faucet.haust.app/api/claim"
MAX_RETRIES = 3
CONCURRENT_REQUESTS = 5
GREEN = '\033[32m'  
RED = '\033[31m'
YELLOW = '\033[33m'
RESET = '\033[0m'  
CYAN = '\033[36m'

async def read_wallets():
    try:
        with open("wallets.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        log("FAUCET", f"{RED}Tidak ada file wallets.json{RESET}", "ERROR")
        return []
    except json.JSONDecodeError:
        log("FAUCET", f"{RED}Format wallets.json tidak valid!{RESET}", "ERROR")
        return []

async def read_proxies():
    try:
        with open("proxy.txt", "r") as f:
            return [line.strip() for line in f.readlines() if line.strip()]
    except FileNotFoundError:
        log("FAUCET", f"{YELLOW}Tidak ada file proxy.txt. Request akan berjalan tanpa proxy.{RESET}", "WARN")
        return []

async def claim_faucet(session, address, proxies):
    attempt = 0
    used_proxies = set()

    while attempt < MAX_RETRIES:
        available_proxies = [p for p in proxies if p not in used_proxies]
        proxy = random.choice(available_proxies) if available_proxies else None
        proxy_dict = {"http": proxy, "https": proxy} if proxy else None

        if proxy:
            log("FAUCET", f"{CYAN}Menggunakan proxy baru untuk {address}: {proxy}{RESET}", "INFO")
            used_proxies.add(proxy)

        try:
            async with session.post(FAUCET_URL, json={"address": address}, proxy=proxy, timeout=10) as response:
                if response.status == 200:
                    json_response = await response.json()

                    log("FAUCET", f"{GREEN}Berhasil klaim untuk {address}{RESET}", "SUCCESS")
                    return True
                else:
                    log("FAUCET", f"{RED}Gagal klaim untuk {address}. Status: {response.status}, Response: {await response.text()}{RESET}", "ERROR")

        except Exception as e:
            log("FAUCET", f"{RED}Error klaim untuk {address} dengan proxy {proxy}: {e}{RESET}", "ERROR")

        attempt += 1
        log("FAUCET", f"{YELLOW}Retry {attempt}/{MAX_RETRIES} untuk {address} dengan proxy lain...{RESET}", "INFO")
        await asyncio.sleep(random.uniform(2, 4))

    log("FAUCET", f"{RED}Gagal klaim faucet untuk {address} setelah {MAX_RETRIES} percobaan.{RESET}", "ERROR")
    return False

async def run():
    wallets = await read_wallets()
    proxies = await read_proxies()

    if not wallets:
        log("FAUCET", f"{YELLOW}Tidak ada wallet untuk diproses.{RESET}", "WARN")
        return

    async with aiohttp.ClientSession() as session:
        tasks = []
        for wallet in wallets:
            tasks.append(claim_faucet(session, wallet["address"], proxies))

            if len(tasks) >= CONCURRENT_REQUESTS:
                await asyncio.gather(*tasks)
                tasks = []

        if tasks:
            await asyncio.gather(*tasks)

    log("FAUCET", f"{GREEN}Semua wallet telah diproses!{RESET}", "SUCCESS")

if __name__ == "__main__":
    asyncio.run(run())
