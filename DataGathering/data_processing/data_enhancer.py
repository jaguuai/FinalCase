import pandas as pd

def label_entities(wallets: pd.DataFrame, transactions: pd.DataFrame) -> pd.DataFrame:
    """Add behavioral labels to wallets."""
    # Merge with transaction data
    enriched = wallets.merge(
        transactions.groupby('wallet').agg(
            last_active=('timestamp', 'max'),
            tx_count=('transaction_id', 'count')
        ),
        on='wallet'
    )
    
    # Apply labels based on rules
    enriched['label'] = 'retail'
    enriched.loc[enriched['balance'] > 10000, 'label'] = 'whale'
    enriched.loc[enriched['tx_count'] > 200, 'label'] = 'active_trader'
    return enriched

def add_price_features(token_data: pd.DataFrame) -> pd.DataFrame:
    """Enhance price data with technical indicators."""
    return token_data.assign(
        moving_avg_7d=token_data['price'].rolling(7).mean(),
        volatility=token_data['price'].rolling(24).std()
    )

def link_nft_owner_market(nft_owners: pd.DataFrame, market_data: pd.DataFrame) -> pd.DataFrame:
    """Combine NFT ownership with market listings."""
    return nft_owners.merge(
        market_data[['asset_id', 'last_sale_price', 'listed']],
        on='asset_id',
        how='left'
    ).fillna({'listed': False})