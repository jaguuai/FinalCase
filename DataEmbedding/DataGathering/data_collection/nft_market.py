import requests
import time
import csv
from datetime import datetime

# Koleksiyon tanımları
AURORY_COLLECTIONS = {
    "aurorians": "aurory",
    "accessories": "aurory_accessories",
    "missions": "aurory_missions"
}

def get_magic_eden_stats(collection_symbol):
    base_url = f"https://api-mainnet.magiceden.dev/v2/collections/{collection_symbol}"
    stats = {
        "collection": collection_symbol,
        "floor_price_SOL": None,
        "trade_volume_SOL": None,
        "mint_rate_events_per_sec": None,
        "last_mint_time": None
    }

    try:
        # 1. Floor price ve volume bilgisi
        stats_resp = requests.get(f"{base_url}/stats", timeout=10)
        stats_resp.raise_for_status()
        stats_data = stats_resp.json()
        
        stats["floor_price_SOL"] = stats_data.get("floorPrice", stats_data.get("floor_price")) or None
        if stats["floor_price_SOL"] is not None:
            stats["floor_price_SOL"] /= 1e9  # SOL'e çevir
            
        stats["trade_volume_SOL"] = stats_data.get("volumeAll", stats_data.get("volume")) or None
        if stats["trade_volume_SOL"] is not None:
            stats["trade_volume_SOL"] /= 1e9  # SOL'e çevir

        # 2. Mint aktiviteleri (daha güvenilir yöntem)
        listings_resp = requests.get(
            f"{base_url}/listings?offset=0&limit=100",
            timeout=15
        )
        listings_resp.raise_for_status()
        listings = listings_resp.json()
        
        mint_times = []
        for item in listings:
            if item.get('mintAddress') and item.get('createdAt'):
                try:
                    # Timestamp'i datetime'a çevir
                    mint_time = datetime.strptime(item['createdAt'], '%Y-%m-%dT%H:%M:%S.%fZ').timestamp()
                    mint_times.append(mint_time)
                except:
                    continue
        
        # Mint oranını hesapla
        if len(mint_times) >= 2:
            mint_times.sort()
            time_diffs = [mint_times[i] - mint_times[i-1] for i in range(1, len(mint_times))]
            avg_interval = sum(time_diffs) / len(time_diffs)
            stats["mint_rate_events_per_sec"] = 1 / avg_interval if avg_interval > 0 else 0
            stats["last_mint_time"] = datetime.fromtimestamp(mint_times[-1]).isoformat()
        elif mint_times:
            stats["last_mint_time"] = datetime.fromtimestamp(mint_times[0]).isoformat()
            
    except Exception as e:
        print(f"⛔ API hatası ({collection_symbol}): {str(e)[:80]}")

    return stats

def save_to_csv(data, filename="aurory_nft_stats.csv"):
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ["collection", "floor_price_SOL", "trade_volume_SOL", 
                      "mint_rate_events_per_sec", "last_mint_time", "timestamp"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        current_time = datetime.utcnow().isoformat()
        for collection, stats in data.items():
            row = {
                "collection": collection,
                "floor_price_SOL": stats.get("floor_price_SOL"),
                "trade_volume_SOL": stats.get("trade_volume_SOL"),
                "mint_rate_events_per_sec": stats.get("mint_rate_events_per_sec"),
                "last_mint_time": stats.get("last_mint_time"),
                "timestamp": current_time
            }
            writer.writerow(row)
    
    print(f"\n💾 Veriler {filename} dosyasına kaydedildi")

def format_stat_value(value, format_str=".4f"):
    if value is None:
        return "Veri Yok"
    try:
        return format(value, format_str)
    except:
        return str(value)

if __name__ == "__main__":
    # Tüm Aurory koleksiyonları için veriyi çek
    all_stats = {}
    
    for collection_name, collection_symbol in AURORY_COLLECTIONS.items():
        print(f"⏳ {collection_name} verisi alınıyor...")
        stats = get_magic_eden_stats(collection_symbol)
        if stats:
            all_stats[collection_name] = stats
        time.sleep(1.5)  # Rate limit koruması
    
    # CSV olarak kaydet
    save_to_csv(all_stats)
    
    # Konsola rapor yazdır
    print("\n" + "="*50)
    print("Aurory NFT İstatistik Raporu")
    print("="*50)
    
    for name, stats in all_stats.items():
        print(f"\n🔹 {name.upper()} ({stats['collection']})")
        
        floor_fmt = format_stat_value(stats.get('floor_price_SOL'))
        volume_fmt = format_stat_value(stats.get('trade_volume_SOL'), ".2f")
        mint_rate_fmt = format_stat_value(stats.get('mint_rate_events_per_sec'))
        last_mint = stats.get('last_mint_time', 'Veri Yok')
        
        mint_per_hour = "Veri Yok"
        if stats.get('mint_rate_events_per_sec') is not None:
            mint_per_hour = format_stat_value(stats['mint_rate_events_per_sec'] * 3600, ".1f")
        
        print(f"   - Floor Fiyat: {floor_fmt} SOL")
        print(f"   - 24s Hacim: {volume_fmt} SOL")
        print(f"   - Son Mint Zamanı: {last_mint}")
        print(f"   - Mint Hızı: {mint_rate_fmt} NFT/saniye")
        print(f"      (≈ {mint_per_hour} NFT/saat)")