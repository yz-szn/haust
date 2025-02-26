import os
import sys
import asyncio
from config import faucet, mint_nft, deploy, auto_transfer, check_wallets, proxy_checker, create_wallets, base
from colorama import init, Fore, Style

init(autoreset=True)

def welcome():
    print(
        f"""
        {Fore.GREEN + Style.BRIGHT}
         /$$   /$$ /$$$$$$$$        /$$$$$$$ /$$$$$$$$ /$$$$$$$     
        | $$  | $$|____ /$$/       /$$_____/|____ /$$/| $$__  $$    
        | $$  | $$   /$$$$/       |  $$$$$$    /$$$$/ | $$  \ $$    
        | $$  | $$  /$$__/         \____  $$  /$$__/  | $$  | $$   
        |  $$$$$$$ /$$$$$$$$       /$$$$$$$/ /$$$$$$$$| $$  | $$    
         \____  $$|________/      |_______/ |________/|__/  |__/    
        /$$  | $$ ______________________________________________                                                  
       |  $$$$$$/ ============ Nothing's Impossible !! =========                                  
        \______/                                   
            """
    )

welcome()
print(f"{Fore.CYAN}{'=' * 21}")
print(Fore.CYAN + "HAUST NETWORK TESTNET")
print(f"{Fore.CYAN}{'=' * 21}")

async def main():
    while True:
        print(Fore.YELLOW + "\n[=== PILIH MENU ===]")
        print(Fore.CYAN + "1. Faucet")
        print(Fore.CYAN + "2. Mint NFT")
        print(Fore.CYAN + "3. Deploy Contract " + Fore.RED + "#Dalam Pengembangan")
        print(Fore.CYAN + "4. Auto Send HAUST")
        print(Fore.CYAN + "5. Cek Wallet")
        print(Fore.CYAN + "6. Proxy Checker")
        print(Fore.CYAN + "7. Create Wallets")
        print(Fore.CYAN + "8. Cek NFT BASE")
        print(Fore.CYAN + "9. Keluar")

        choice = input(Fore.GREEN + "Masukkan pilihan (1-8): ").strip()

        if choice == "1":
            print(Fore.BLUE + "Memulai proses faucet...")
            await faucet.run()
        elif choice == "2":
            print(Fore.BLUE + "Memulai proses mint NFT...")
            await mint_nft.run()
        elif choice == "3":
            print(Fore.BLUE + "Memulai deploy contract...")
            await deploy.run()
        elif choice == "4":
            print(Fore.BLUE + "Memulai auto send...")
            await auto_transfer.run()
        elif choice == "5":
            print(Fore.BLUE + "Cek wallet...")
            await check_wallets.run()
        elif choice == "6":
            print(Fore.BLUE + "Cek proxy...")
            await proxy_checker.run()
        elif choice == "7":
            print(Fore.BLUE + "Membuat wallets baru...")
            await create_wallets.run()
        elif choice == "8":
            print(Fore.BLUE + "Cek NFT BASE...")
            await base.run()
        elif choice == "9":
            print(Fore.RED + "Keluar dari program...")
            return 
        else:
            print(Fore.RED + "Pilihan tidak valid! Mohon pilih antara 1-8.")

if __name__ == "__main__":
    asyncio.run(main())
