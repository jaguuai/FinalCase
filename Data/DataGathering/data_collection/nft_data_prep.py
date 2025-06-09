import pandas as pd


# CSV yükle
df = pd.read_csv("C:/Users/alice/OneDrive/Masaüstü/P2E-Economy-Assistant-AuroryGame/data_collection/aurory_nfts.csv")

# 1. Önemli sütunlarda boş olan satırları sil
important_cols = ["price_sol", "seller", "timestamp"]
df = df.dropna(subset=important_cols)
df = df[(df["price_sol"] != "") & (df["seller"] != "") & (df["timestamp"] != "")]

# 2. Tamamen boş olan sütunları sil (tüm satırlarda boşsa)
df = df.dropna(axis=1, how="all")          # tümü NaN olanları
df = df.loc[:, ~(df == "").all()]         # tümü boş string olanları

# 3. Timestamp'ı anlamlı bir tarih formatına dönüştür (opsiyonel)
df["timestamp"] = pd.to_datetime(df["timestamp"], unit="s", errors="coerce")
df = df.dropna(subset=["timestamp"])  # timestamp çevirilemeyenleri çıkar

# 4. id sütununu güncelle
df.insert(0, "id", range(1, len(df) + 1))

# 5. Kaydet
df.to_csv("nft_cleaned_final.csv", index=False)

print(f"Temiz veri kaydedildi. Satır sayısı: {len(df)}, Sütun sayısı: {df.shape[1]}")
