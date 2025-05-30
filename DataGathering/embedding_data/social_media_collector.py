import pandas as pd
from datetime import datetime

def load_csv_data(file_path, source_name):
    try:
        df = pd.read_csv(file_path)
        df['source'] = source_name
        print(f"📁 Loaded {len(df)} records from {file_path}")
        return df
    except Exception as e:
        print(f"❌ Error loading {file_path}: {e}")
        return pd.DataFrame()

def save_to_csv(df, filename_prefix):
    if df.empty:
        print("⚠️ No data to save.")
        return None

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{filename_prefix}_{timestamp}.csv"
    df.to_csv(filename, index=False)
    print(f"💾 Saved {len(df)} records to {filename}")
    return filename

def main():
    # CSV'den verileri yükle
    twitter_df = load_csv_data("aurory_tweets.csv", "twitter")
    news_df = load_csv_data("aurory_news.csv", "aurory_news")

    # Birleştir
    combined_df = pd.concat([twitter_df, news_df], ignore_index=True)

    # CSV olarak kaydet
    combined_file = save_to_csv(combined_df, "aurory_combined_data")

    print("\n📊 Toplam Veri Özeti:")
    print(f"- Twitter: {len(twitter_df)} kayıt")
    print(f"- News: {len(news_df)} kayıt")
    print(f"- Toplam: {len(combined_df)} kayıt")

    if combined_file:
        print(f"\n✅ CSV dosyası kaydedildi: {combined_file}")

if __name__ == "__main__":
    main()
