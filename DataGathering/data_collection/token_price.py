import requests
import json
import csv
from datetime import datetime
import os

class CryptoPriceFetcher:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json',
            'Connection': 'keep-alive'
        }
        self.csv_file = "currrent_aurory_price.csv"

    def get_price_from_yahoo(self):
        """Try Yahoo Finance as data source"""
        print("Checking Yahoo Finance...")

        try:
            url = "https://query1.finance.yahoo.com/v8/finance/chart/AURY-USD"
            response = requests.get(url, headers=self.headers, timeout=10)

            if response.status_code == 200:
                data = response.json()
                result = data.get("chart", {}).get("result", [{}])[0]
                price = result.get("meta", {}).get("regularMarketPrice")
                if price:
                    print(f" Yahoo Finance: ${price}")
                    return price
        except Exception as e:
            print(f" Failed: {str(e)[:50]}...")

        return None

    def log_price(self, price):
       
        if price is None:
            return

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = {
            "timestamp": timestamp,
            "symbol": "AURY",
            "price_usd": price,
            "source": "Yahoo Finance"
        }

     

        # Save to CSV file
        try:
            file_exists = os.path.isfile(self.csv_file)
            with open(self.csv_file, 'a', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=log_entry.keys())
                if not file_exists:
                    writer.writeheader()
                writer.writerow(log_entry)
        except Exception as e:
            print(f" CSV write failed: {e}")

       

    def fetch_price(self):
        print(" AURY Price Fetcher (Yahoo Only)")
        print("=" * 50)
        price = self.get_price_from_yahoo()

        if price:
            self.log_price(price)
            print(f"\n FINAL RESULT: AURY = ${price:.6f} USD")
        else:
            print("\n Unable to fetch AURY price.")

if __name__ == "__main__":
    fetcher = CryptoPriceFetcher()
    fetcher.fetch_price()