# tools/price_api.py
import requests
import streamlit as st
from typing import Dict, Optional, List
import json
from datetime import datetime

class TokenPriceAPI:
    def __init__(self):
        # CoinGecko API (ücretsiz tier)
        self.coingecko_base_url = "https://api.coingecko.com/api/v3"
        
        # Token mapping (CoinGecko ID'leri ile eşleştirme)
        self.token_mapping = {
            'AURY': 'aurory',
            'XAURY': 'xaurory',  # Eğer CoinGecko'da varsa
            'NERITE': 'nerite',  # Eğer CoinGecko'da varsa
            'EMBER': 'ember-token',  # Genel token ismi
            'WISDOM': 'wisdom-token'  # Genel token ismi
        }
    
    def get_token_price(self, token_symbol: str) -> Dict:
        """
        Belirtilen token için fiyat bilgilerini getirir
        """
        try:
            token_symbol = token_symbol.upper()
            
            if token_symbol not in self.token_mapping:
                return {
                    "error": f"Token {token_symbol} not supported",
                    "supported_tokens": list(self.token_mapping.keys())
                }
            
            coingecko_id = self.token_mapping[token_symbol]
            
            # CoinGecko API çağrısı
            url = f"{self.coingecko_base_url}/simple/price"
            params = {
                'ids': coingecko_id,
                'vs_currencies': 'usd,btc,eth',
                'include_24hr_change': 'true',
                'include_24hr_vol': 'true',
                'include_market_cap': 'true',
                'include_last_updated_at': 'true'
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if coingecko_id not in data:
                return {"error": f"Price data not found for {token_symbol}"}
            
            token_data = data[coingecko_id]
            
            return {
                "token": token_symbol,
                "price_usd": token_data.get('usd', 'N/A'),
                "price_btc": token_data.get('btc', 'N/A'),
                "price_eth": token_data.get('eth', 'N/A'),
                "market_cap_usd": token_data.get('usd_market_cap', 'N/A'),
                "volume_24h_usd": token_data.get('usd_24h_vol', 'N/A'),
                "change_24h_percent": token_data.get('usd_24h_change', 'N/A'),
                "last_updated": datetime.fromtimestamp(token_data.get('last_updated_at', 0)).strftime('%Y-%m-%d %H:%M:%S') if token_data.get('last_updated_at') else 'N/A'
            }
            
        except requests.exceptions.RequestException as e:
            return {"error": f"API request failed: {str(e)}"}
        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}"}
    
    def get_multiple_token_prices(self, token_symbols: List[str]) -> Dict:
        """
        Birden fazla token için fiyat bilgilerini getirir
        """
        results = {}
        for token in token_symbols:
            results[token] = self.get_token_price(token)
        return results
    
    def get_aurory_ecosystem_prices(self) -> Dict:
        """
        Tüm Aurory ekosistem token'ları için fiyat bilgilerini getirir
        """
        aurory_tokens = ['AURY', 'XAURY', 'NERITE', 'EMBER', 'WISDOM']
        return self.get_multiple_token_prices(aurory_tokens)

# Token price tool instance
price_api = TokenPriceAPI()

def get_token_price(query: str) -> str:
    """
    Token fiyat sorgularını işler
    Query formatları:
    - "AURY price" 
    - "AURY"
    - "price of AURY"
    - "all aurory tokens"
    """
    try:
        query = query.strip().upper()
        
        # Tüm Aurory token'ları isteniyor mu?
        if 'ALL' in query and ('AURORY' in query or 'ECOSYSTEM' in query):
            results = price_api.get_aurory_ecosystem_prices()
            
            response = "🎮 **Aurory Ecosystem Token Prices** 💰\n\n"
            
            for token, data in results.items():
                if 'error' in data:
                    response += f"❌ **{token}**: {data['error']}\n"
                else:
                    response += f"🪙 **{token}**:\n"
                    response += f"   💵 Price: ${data['price_usd']}\n"
                    if data['change_24h_percent'] != 'N/A':
                        change_emoji = "📈" if float(data['change_24h_percent']) > 0 else "📉"
                        response += f"   {change_emoji} 24h Change: {data['change_24h_percent']:.2f}%\n"
                    if data['volume_24h_usd'] != 'N/A':
                        response += f"   📊 24h Volume: ${data['volume_24h_usd']:,.0f}\n"
                    response += f"   🕒 Updated: {data['last_updated']}\n\n"
            
            return response
        
        # Tek token sorgusu
        # Token adını çıkar
        token_symbols = ['AURY', 'XAURY', 'NERITE', 'EMBER', 'WISDOM']
        found_token = None
        
        for token in token_symbols:
            if token in query:
                found_token = token
                break
        
        if not found_token:
            return ("❓ Token not recognized. Supported tokens: " + 
                   ", ".join(token_symbols) + 
                   "\n\nTry: 'AURY price' or 'all aurory tokens'")
        
        result = price_api.get_token_price(found_token)
        
        if 'error' in result:
            return f"❌ Error fetching {found_token} price: {result['error']}"
        
        response = f"🎮 **{result['token']} Token Price** 💰\n\n"
        response += f"💵 **Current Price**: ${result['price_usd']}\n"
        
        if result['change_24h_percent'] != 'N/A':
            change = float(result['change_24h_percent'])
            change_emoji = "📈" if change > 0 else "📉"
            response += f"{change_emoji} **24h Change**: {change:.2f}%\n"
        
        if result['volume_24h_usd'] != 'N/A':
            response += f"📊 **24h Volume**: ${result['volume_24h_usd']:,.0f}\n"
        
        if result['market_cap_usd'] != 'N/A':
            response += f"🏦 **Market Cap**: ${result['market_cap_usd']:,.0f}\n"
        
        response += f"🕒 **Last Updated**: {result['last_updated']}\n"
        
        # Fiyat analizi
        if result['change_24h_percent'] != 'N/A':
            change = float(result['change_24h_percent'])
            if change > 5:
                response += "\n🚀 **Analysis**: Strong upward momentum!"
            elif change > 0:
                response += "\n📊 **Analysis**: Positive price movement."
            elif change > -5:
                response += "\n⚖️ **Analysis**: Relatively stable price."
            else:
                response += "\n⚠️ **Analysis**: Significant price decline."
        
        return response
        
    except Exception as e:
        return f"❌ Error processing price query: {str(e)}"

# Alternative API sources (Backup)
class AlternativePriceAPIs:
    """
    Backup API sources for token prices
    """
    
    @staticmethod
    def get_from_dexscreener(token_address: str):
        """
        DEXScreener API - Solana token'ları için
        """
        try:
            url = f"https://api.dexscreener.com/latest/dex/tokens/{token_address}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    @staticmethod
    def get_from_jupiter(token_mint: str):
        """
        Jupiter API - Solana token'ları için
        """
        try:
            url = f"https://price.jup.ag/v4/price?ids={token_mint}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}