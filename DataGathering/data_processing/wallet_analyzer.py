import csv
import pandas as pd
from collections import defaultdict

class WalletAnalyzer:
    def __init__(self):
        self.holders = self.load_holder_data()
        self.transactions = self.load_transaction_data()

    def load_holder_data(self):
        try:
            return pd.read_csv("C:/Users/alice/OneDrive/Masaüstü/P2E-Economy-Assistant-AuroryGame/data_collection/aury_data_wallets.csv")
        except FileNotFoundError:
            print("⚠️ Holder data not found. Run on_chain_data.py first.")
            return pd.DataFrame()

    def load_transaction_data(self):
        try:
            return pd.read_csv("C:/Users/alice/OneDrive/Masaüstü/P2E-Economy-Assistant-AuroryGame/data_collection/aury_data_transactions.csv")
        except FileNotFoundError:
            print("⚠️ Transaction data not found. Run on_chain_data.py first.")
            return pd.DataFrame()

    def identify_whales(self, threshold=0.01):
        """Identify large token holders (whales)"""
        if self.holders.empty:
            return []
        
        total_supply = self.holders['ui_amount'].sum()
        whale_threshold = total_supply * threshold
        
        whales = self.holders[self.holders['ui_amount'] > whale_threshold]
        return whales[['address:ID', 'ui_amount']].to_dict('records')

    def analyze_wallet_activity(self):
        """Analyze wallet transaction patterns"""
        if self.transactions.empty:
            return {}
        
        # Group transactions by wallet
        wallet_activity = defaultdict(lambda: {
            'tx_count': 0,
            'last_active': None,
            'avg_fee': 0
        })
        
        for _, row in self.transactions.iterrows():
            wallet = row[':START_ID']  # Assuming format from on_chain_data.py
            wallet_activity[wallet]['tx_count'] += 1
            wallet_activity[wallet]['avg_fee'] = (
                wallet_activity[wallet]['avg_fee'] * (wallet_activity[wallet]['tx_count'] - 1) + row['fee']
            ) / wallet_activity[wallet]['tx_count']
            
            # Update last active timestamp
            if not wallet_activity[wallet]['last_active'] or row['timestamp'] > wallet_activity[wallet]['last_active']:
                wallet_activity[wallet]['last_active'] = row['timestamp']
                
        return dict(wallet_activity)

    def calculate_holder_distribution(self):
        """Calculate token distribution metrics"""
        if self.holders.empty:
            return {}
        
        sorted_holders = self.holders.sort_values('ui_amount', ascending=False)
        sorted_holders['cumulative'] = sorted_holders['ui_amount'].cumsum()
        total_supply = sorted_holders['ui_amount'].sum()
        
        # Calculate top percentile holdings
        top_1_pct = sorted_holders[sorted_holders['cumulative'] <= total_supply * 0.01]
        top_10_pct = sorted_holders[sorted_holders['cumulative'] <= total_supply * 0.10]
        
        return {
            "total_holders": len(sorted_holders),
            "supply_top_1%": top_1_pct['ui_amount'].sum() / total_supply,
            "supply_top_10%": top_10_pct['ui_amount'].sum() / total_supply,
            "median_balance": sorted_holders['ui_amount'].median()
        }

if __name__ == "__main__":
    analyzer = WalletAnalyzer()
    
    print("\nToken Holder Distribution:")
    print("=" * 50)
    distribution = analyzer.calculate_holder_distribution()
    for metric, value in distribution.items():
        name = metric.replace('_', ' ').title()
        print(f"{name}: {value:.4f}")
    
    print("\nTop Whales:")
    print("=" * 50)
    for whale in analyzer.identify_whales()[:5]:
        print(f"{whale['address:ID'][:12]}...: {whale['ui_amount']:,.2f} AURY")