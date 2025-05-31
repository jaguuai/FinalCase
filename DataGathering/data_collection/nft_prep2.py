import pandas as pd

# 1. CSV dosyasını oku
df = pd.read_csv("C:/Users/alice/OneDrive/Masaüstü/P2E-Economy-Assistant-AuroryGame/data_collection/nft_cleaned_final.csv")  # Dosya adını kendi dosyana göre değiştir

# 2. 'price_usd' sütununu sil
if 'price_usd' in df.columns:
    df = df.drop(columns=['price_usd'])
else:
    print("'price_usd' sütunu bulunamadı.")

# 3. Temizlenmiş veriyi yeni bir CSV dosyasına kaydet
df.to_csv("veri_sade.csv", index=False)

# 4. Kontrol için ilk 5 satırı yazdır
print(df.head())
