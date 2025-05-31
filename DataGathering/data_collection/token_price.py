# fetcher_main.py

import requests
import time
import csv
from datetime import datetime
from typing import Optional, Tuple, Dict, Any
import os

class CoinFetcher:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'Mozilla/5.0'})

        self.exchange_rates = {
            "try": 34.2,
            "eur": 0.93,
            "jpy": 149.5,
            "gbp": 0.79
        }

        self.coin_types = {
            "aurory": "Solana", "aury": "Solana",
            "bonk": "Solana", "jup": "Solana", "pyth": "Solana",
            "wif": "Solana", "jto": "Solana", "ray": "Solana",
            "orca": "Solana", "msol": "Solana", "sol": "Solana",
            "bitcoin": "Bitcoin", "ethereum": "Ethereum",
            "usdc": "Multi-chain", "usdt": "Multi-chain"
        }

        self.solana_coins = {
            "aurory": "aury-aurory",
            "bonk": "bonk-bonk",
            "jup": "jup-jupiter-exchange",
            "pyth": "pyth-pyth-network",
            "wif": "wif-dogwifhat",
            "jto": "jto-jito-governance-token",
            "ray": "ray-raydium",
            "orca": "orca-orca",
            "msol": "msol-marinade-staked-sol",
            "solana": "sol-solana"
        }

    def get_coin_type(self, coin_name: str) -> str:
        for known_coin, blockchain in self.coin_types.items():
            if known_coin in coin_name.lower():
                return blockchain
        return "Unknown"

    def get_exchange_rates(self):
        try:
            url = "https://api.exchangerate-api.com/v4/latest/USD"
            response = self.session.get(url, timeout=5)
            if response.status_code == 200:
                rates = response.json()["rates"]
                self.exchange_rates.update({
                    "try": rates.get("TRY", self.exchange_rates["try"]),
                    "eur": rates.get("EUR", self.exchange_rates["eur"]),
                    "jpy": rates.get("JPY", self.exchange_rates["jpy"]),
                    "gbp": rates.get("GBP", self.exchange_rates["gbp"])
                })
                print("💱 Döviz kurları güncellendi.")
        except Exception as e:
            print(f"⚠️ Döviz kurları alınamadı: {e}")

    def fetch_from_coinpaprika(self, coin_id: str) -> Tuple[Optional[Dict], Optional[str]]:
        try:
            url = f"https://api.coinpaprika.com/v1/tickers/{coin_id}"
            response = self.session.get(url, timeout=10)
            data = response.json()
            usd_price = data["quotes"]["USD"]["price"]
            coin_name = data["name"].lower().replace(" ", "_")

            result = {
                coin_name: {
                    "usd": usd_price,
                    "try": usd_price * self.exchange_rates["try"],
                    "eur": usd_price * self.exchange_rates["eur"],
                    "jpy": usd_price * self.exchange_rates["jpy"],
                    "gbp": usd_price * self.exchange_rates["gbp"],
                    "market_cap_usd": data["quotes"]["USD"].get("market_cap"),
                    "volume_24h_usd": data["quotes"]["USD"].get("volume_24h"),
                    "percent_change_24h": data["quotes"]["USD"].get("percent_change_24h"),
                    "last_updated": data.get("last_updated")
                }
            }
            return result, "CoinPaprika"
        except Exception as e:
            print(f"❌ CoinPaprika hatası ({coin_id}): {e}")
            return None, None

    def save_to_csv(self, data: Dict[str, Any], source: str, filename: str):
        headers = [
            "coin", "coin_type", "source", "timestamp",
            "usd", "try", "eur", "jpy", "gbp",
            "market_cap_usd", "volume_24h_usd", "percent_change_24h"
        ]
        now = datetime.utcnow().isoformat()
        rows = []

        for coin, values in data.items():
            blockchain = self.get_coin_type(coin)
            rows.append([
                coin, blockchain, source, now,
                values.get("usd"), values.get("try"), values.get("eur"),
                values.get("jpy"), values.get("gbp"),
                values.get("market_cap_usd"),
                values.get("volume_24h_usd"),
                values.get("percent_change_24h")
            ])

        try:
            write_header = not os.path.exists(filename) or os.stat(filename).st_size == 0
            with open(filename, mode="a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                if write_header:
                    writer.writerow(headers)
                writer.writerows(rows)
            print(f"✅ {filename} dosyasına kaydedildi.")
        except Exception as e:
            print(f"❌ CSV yazım hatası: {e}")

    def fetch_multiple_solana_coins(self) -> Tuple[Dict[str, Any], str]:
        print("🚀 Solana coinleri çekiliyor...")
        self.get_exchange_rates()
        all_data = {}

        for coin, coin_id in self.solana_coins.items():
            data, source = self.fetch_from_coinpaprika(coin_id)
            if data:
                all_data.update(data)
                print(f"✅ {coin.upper()} verisi çekildi.")
            else:
                print(f"⚠️ {coin.upper()} verisi alınamadı.")
            time.sleep(0.5)

        return all_data, "CoinPaprika"

# Ana kullanım
if __name__ == "__main__":
    fetcher = CoinFetcher()

    print("🎯 Seçenekler:")
    print("1️⃣ Sadece AURY")
    print("2️⃣ Tüm Solana Coinleri")

    secim = input("Seçiminiz (1/2): ").strip()
    if secim == "2":
        data, source = fetcher.fetch_multiple_solana_coins()
        filename = "solana_coins.csv"
    else:
        data, source = fetcher.fetch_from_coinpaprika("aury-aurory")
        filename = "aurory_data.csv"

    if data:
        fetcher.save_to_csv(data, source, filename)
        print("📈 Alınan coin verileri:")
        for coin, val in data.items():
            print(f"🪙 {coin.upper()} | USD: ${val['usd']:.6f} | TRY: ₺{val['try']:.2f} | 24h: {val.get('percent_change_24h', 0):+.2f}%")
    else:
        print("❌ Veri alınamadı.")
