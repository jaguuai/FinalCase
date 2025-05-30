import requests
import csv
import time
from collections import defaultdict

# --- Ayarlar ---
RPC_URL = "https://mainnet.helius-rpc.com/?api-key=af98fdd4-8f1c-4367-8305-8ddd46887fa0"
MINT_ADDRESS = "AURYydfxJib1ZkTir1Jn1J9ECYUtjb6rKQVmtYaixWPP"
DECIMALS = 6
OUTPUT_PREFIX = "aury_data_"

def rpc_request(method, params):
    """Solana RPC isteği gönderir"""
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": method,
        "params": params
    }
    try:
        response = requests.post(RPC_URL, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"RPC hatası: {e}")
        return None

def get_token_holders(mint):
    """Token'ın en büyük sahiplerini getirir"""
    res = rpc_request("getTokenLargestAccounts", [mint])
    if not res or not res.get("result"):
        return []
    
    holders = []
    for account in res["result"]["value"]:
        holders.append({
            "address": account["address"],
            "amount": account["amount"],
            "ui_amount": account["uiAmount"],
            "decimals": account["decimals"]
        })
    return holders

def get_transactions_for_account(account, limit=10):
    """Hesap için işlem geçmişini getirir"""
    sigs = rpc_request("getSignaturesForAddress", [
        account, 
        {"limit": limit, "commitment": "confirmed"}
    ])
    return [tx['signature'] for tx in sigs.get('result', [])] if sigs else []

def get_transaction_detail(signature):
    """İşlem detaylarını getirir"""
    return rpc_request("getTransaction", [
        signature, 
        {"encoding": "jsonParsed", "commitment": "confirmed"}
    ])

def analyze_mint_burn_details(holders, tx_limit_per_account=10):
    """
    Mint ve burn işlemlerini analiz eder
    Neo4j için optimize edilmiş veri yapıları döndürür
    """
    # Veri yapıları
    wallets = {}
    transactions = {}
    events = []
    wallet_tx_counts = defaultdict(int)
    
    for holder in holders:
        account = holder["address"]
        wallets[account] = holder
        
        try:
            signatures = get_transactions_for_account(account, tx_limit_per_account)
            wallet_tx_counts[account] = len(signatures)
            
            for sig in signatures:
                if sig in transactions:
                    continue
                    
                result = get_transaction_detail(sig)
                if not result or not result.get("result"):
                    continue
                
                tx_data = result["result"]
                transactions[sig] = {
                    "signature": sig,
                    "timestamp": tx_data.get("blockTime", None),
                    "slot": tx_data.get("slot", None),
                    "fee": tx_data.get("meta", {}).get("fee", 0)
                }
                
                instructions = tx_data['transaction']['message']['instructions']
                for instr in instructions:
                    parsed = instr.get('parsed', {})
                    if not isinstance(parsed, dict):
                        continue
                    info = parsed.get("info", {})
                    
                    if not isinstance(info, dict) or info.get("mint") != MINT_ADDRESS:
                        continue
                    
                    amount = int(info.get('amount', 0))
                    event_type = None
                    
                    if parsed.get("type") in ['mintTo', 'mintToChecked']:
                        event_type = "mint"
                    elif parsed.get("type") in ['burn', 'burnChecked']:
                        event_type = "burn"
                    
                    if event_type:
                        events.append({
                            "wallet_address": account,
                            "tx_signature": sig,
                            "type": event_type,
                            "amount": amount,
                            "ui_amount": amount / (10**DECIMALS),
                            "timestamp": transactions[sig]["timestamp"]
                        })
                        
            time.sleep(0.2)  # Rate limiting
        
        except Exception as e:
            print(f"Hata (account: {account}): {e}")
    
    return {
        "wallets": wallets,
        "transactions": transactions,
        "events": events,
        "wallet_tx_counts": dict(wallet_tx_counts)  # defaultdict'ı normal dict'e çevir
    }

def save_to_csv(data, entity_type, wallet_tx_counts=None):
    """Veriyi CSV dosyasına kaydeder"""
    filename = f"{OUTPUT_PREFIX}{entity_type}.csv"
    with open(filename, 'w', newline='') as f:
        writer = csv.writer(f)
        
        if entity_type == "wallets":
            writer.writerow(["address:ID", "amount", "ui_amount", "tx_count"])
            for wallet in data.values():
                writer.writerow([
                    wallet["address"],
                    wallet["amount"],
                    wallet["ui_amount"],
                    wallet_tx_counts.get(wallet["address"], 0) if wallet_tx_counts else 0
                ])
                
        elif entity_type == "transactions":
            writer.writerow(["signature:ID", "timestamp", "slot", "fee"])
            for tx in data.values():
                writer.writerow([
                    tx["signature"],
                    tx["timestamp"],
                    tx["slot"],
                    tx["fee"]
                ])
                
        elif entity_type == "events":
            writer.writerow([":START_ID", ":END_ID", "type", "amount", "ui_amount", "timestamp"])
            for event in data:
                writer.writerow([
                    event["wallet_address"],
                    event["tx_signature"],
                    event["type"],
                    event["amount"],
                    event["ui_amount"],
                    event["timestamp"]
                ])
    
    return filename

# ---- Ana Fonksiyon ----
if __name__ == "__main__":
    print("Token sahipleri alınıyor...")
    holders = get_token_holders(MINT_ADDRESS)
    print(f"{len(holders)} token sahibi bulundu")
    
    print("\nİşlemler analiz ediliyor...")
    analysis_data = analyze_mint_burn_details(holders, tx_limit_per_account=15)
    
    print("\n CSV dosyaları yazılıyor...")
    wallet_file = save_to_csv(
        analysis_data["wallets"], 
        "wallets",
        wallet_tx_counts=analysis_data["wallet_tx_counts"]
    )
    tx_file = save_to_csv(analysis_data["transactions"], "transactions")
    events_file = save_to_csv(analysis_data["events"], "events")
    
    print("\nSonuçlar:")
    print(f"- Cüzdanlar: {wallet_file} ({len(analysis_data['wallets'])} kayıt)")
    print(f"- İşlemler: {tx_file} ({len(analysis_data['transactions'])} kayıt)")
    print(f"- Olaylar: {events_file} ({len(analysis_data['events'])} kayıt)")
    
    # Özet istatistikler
    mint_count = sum(1 for e in analysis_data["events"] if e["type"] == "mint")
    burn_count = sum(1 for e in analysis_data["events"] if e["type"] == "burn")
    print(f"\nToplam Mint Olayları: {mint_count}")
    print(f"Toplam Burn Olayları: {burn_count}")
    
    if analysis_data['transactions']:
        avg_events = len(analysis_data['events']) / len(analysis_data['transactions'])
        print(f"İşlem başına ortalama olay: {avg_events:.2f}")
    else:
        print("İşlem başına ortalama olay: 0")