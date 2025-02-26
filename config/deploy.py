import json
import time
import random
from web3 import Web3
from solcx import compile_source
from utils.logger import log

RPC_URL = "https://haust-network-testnet-rpc.eu-north-2.gateway.fm"
w3 = Web3(Web3.HTTPProvider(RPC_URL))

CONTRACT_SOURCE = """
pragma solidity ^0.8.0;

contract Token {
    string public name = "Haust Token";
    string public symbol = "HAUS";
    uint8 public decimals = 18;
    uint256 public totalSupply;

    mapping(address => uint256) public balanceOf;

    event Transfer(address indexed from, address indexed to, uint256 value);
    event Mint(address indexed to, uint256 value);

    constructor(uint256 _initialSupply) {
        balanceOf[msg.sender] = _initialSupply;
        totalSupply = _initialSupply;
        emit Transfer(address(0), msg.sender, _initialSupply);
    }

    function transfer(address _to, uint256 _value) public returns (bool success) {
        require(balanceOf[msg.sender] >= _value, "Insufficient balance");
        balanceOf[msg.sender] -= _value;
        balanceOf[_to] += _value;
        emit Transfer(msg.sender, _to, _value);
        return true;
    }

    function mint(address _to, uint256 _value) public {
        totalSupply += _value;
        balanceOf[_to] += _value;
        emit Mint(_to, _value);
    }
}
"""

def compile_contract():
    compiled_sol = compile_source(CONTRACT_SOURCE, solc_version="0.8.0")
    contract_id, contract_interface = compiled_sol.popitem()
    return contract_interface["abi"], contract_interface["bin"]

def read_wallets():
    try:
        with open("wallets.json", "r") as f:
            wallets = json.load(f)
            valid_wallets = []
            for wallet in wallets:
                if "address" in wallet and "privateKey" in wallet:
                    wallet["address"] = Web3.to_checksum_address(wallet["address"])
                    valid_wallets.append(wallet)
                else:
                    log("DEPLOY", f"Wallet {wallet} tidak valid!", "ERROR")
            return valid_wallets
    except FileNotFoundError:
        log("DEPLOY", "Tidak ada file wallets.json", "ERROR")
        return []

def deploy_contract(wallet, abi, bytecode):
    try:
        log("DEPLOY", f"Mulai deploy kontrak untuk {wallet['address']}", "INFO")

        contract = w3.eth.contract(abi=abi, bytecode=bytecode)

        tx = contract.constructor(w3.to_wei(1_000_000, "ether")).build_transaction({
            "from": wallet["address"],
            "gasPrice": w3.to_wei("5", "gwei"),
            "nonce": w3.eth.get_transaction_count(wallet["address"]),
        })

        tx["gas"] = w3.eth.estimate_gas(tx)

        signed_tx = w3.eth.account.sign_transaction(tx, wallet["privateKey"])
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)

        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

        contract_address = receipt.contractAddress
        log("DEPLOY", f"Kontrak berhasil dideploy di {contract_address}", "SUCCESS")

        return contract_address

    except Exception as e:
        log("DEPLOY", f"Gagal deploy contract untuk {wallet['address']}: {str(e)}", "ERROR")
        return None

async def deploy_contracts_to_all_wallets():
    log("DEPLOY", "Memulai proses deploy ke semua wallet...", "WARN")

    wallets = read_wallets()
    if not wallets:
        log("DEPLOY", "Tidak ada wallet yang tersedia!", "ERROR")
        return

    abi, bytecode = compile_contract()

    for wallet in wallets:
        contract_address = deploy_contract(wallet, abi, bytecode)
        if contract_address:
            wallet["contractAddress"] = contract_address

    with open("wallets.json", "w") as f:
        json.dump(wallets, f, indent=2)

    log("DEPLOY", "Semua kontrak berhasil dideploy dan disimpan.", "INFO")

async def run():
    await deploy_contracts_to_all_wallets()

if __name__ == "__main__":
    import asyncio
    asyncio.run(run())