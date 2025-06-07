import requests
import pandas as pd

# Bearer Token (v2 API için)
BEARER_TOKEN = "AAAAAAAAAAAAAAAAAAAAAJl22AEAAAAAynFpbMGMyU05QIH%2BliafNNATEu0%3DfOgZ02T4qPRJWlcHFph2VEfWxhxOc50adiIw2y92lK1Vb8K8oW"

# Başlıklar (Authentication için)
headers = {
    "Authorization": f"Bearer {BEARER_TOKEN}"
}

# Arama sorgusu
query = "aurory -is:retweet lang:en"

# API URL (son 7 günü getirir, 100 tweet'e kadar)
url = f"https://api.twitter.com/2/tweets/search/recent"
params = {
    "query": query,
    "max_results": 100,
    "tweet.fields": "created_at,author_id"
}

# API isteği
response = requests.get(url, headers=headers, params=params)

# Hata kontrolü
if response.status_code != 200:
    raise Exception(f"Request failed: {response.status_code} {response.text}")

# JSON verisini al
data = response.json()

# Eğer tweet bulunamadıysa
if 'data' not in data:
    print("Tweet bulunamadı.")
    exit()

# Verileri DataFrame'e aktar
df = pd.json_normalize(data['data'])

# Kolon adlarını düzenle
df = df.rename(columns={
    "text": "text",
    "created_at": "created_at",
    "id": "id",
    "author_id": "author_id"
})

# CSV dosyasına kaydet
df.to_csv("aurory_tweets_v2.csv", index=False, encoding='utf-8')

print("✅ Tweetler başarıyla CSV dosyasına kaydedildi: aurory_tweets_v2.csv")