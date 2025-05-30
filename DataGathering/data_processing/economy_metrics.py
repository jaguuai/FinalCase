import pandas as pd

class DataEnhancer:
    def __init__(self):
        pass

    def enhance_token_data(self, price_data, transaction_data):
        """Add technical indicators to price data"""
        df = pd.DataFrame(price_data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp')
        
        # Add moving averages
        df['7d_ma'] = df['price_usd'].rolling(window=7).mean()
        df['30d_ma'] = df['price_usd'].rolling(window=30).mean()
        
        # Add volatility
        df['daily_return'] = df['price_usd'].pct_change()
        df['volatility_7d'] = df['daily_return'].rolling(window=7).std()
        
        # Merge with transaction data
        if not transaction_data.empty:
            transaction_data['timestamp'] = pd.to_datetime(transaction_data['timestamp'])
            df = df.merge(
                transaction_data.groupby(pd.Grouper(key='timestamp', freq='D')).size().reset_index(name='tx_count'),
                on='timestamp',
                how='left'
            )
            df['tx_count'] = df['tx_count'].fillna(0)
        
        return df.to_dict('records')

    def enhance_nft_data(self, nft_data, holder_data):
        """Enrich NFT data with holder information"""
        enhanced = {}
        
        for collection, stats in nft_data.items():
            # Add market cap estimation
            stats['estimated_mcap'] = stats['floor_price_SOL'] * stats.get('total_supply', 10000)
            
            # Add holder concentration (if holder data available)
            if not holder_data.empty:
                whales = holder_data[holder_data['ui_amount'] > holder_data['ui_amount'].quantile(0.95)]
                stats['whale_held_pct'] = len(whales) / len(holder_data) if not holder_data.empty else 0
            
            enhanced[collection] = stats
        
        return enhanced

    def tag_dao_proposals(self, dao_data):
        """Categorize DAO proposals based on keywords"""
        if dao_data.empty:
            return dao_data
        
        categories = {
            'economy': ['token', 'reward', 'inflation', 'staking'],
            'governance': ['vote', 'proposal', 'election', 'council'],
            'technical': ['upgrade', 'bug', 'feature', 'security'],
            'partnership': ['collab', 'partner', 'integration']
        }
        
        def categorize(title):
            title_lower = title.lower()
            for cat, keywords in categories.items():
                if any(kw in title_lower for kw in keywords):
                    return cat
            return 'other'
        
        dao_data['category'] = dao_data['title'].apply(categorize)
        return dao_data

if __name__ == "__main__":
    # Example usage
    enhancer = DataEnhancer()
    
    # Load sample data
    price_data = [{"timestamp": "2023-01-01", "price_usd": 1.50}, 
                 {"timestamp": "2023-01-02", "price_usd": 1.55}]
    
    enhanced_price = enhancer.enhance_token_data(price_data, pd.DataFrame())
    print("Enhanced Price Data:")
    for item in enhanced_price:
        print(item)