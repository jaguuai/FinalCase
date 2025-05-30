import requests
from bs4 import BeautifulSoup
import csv
from datetime import datetime
import re
import json
import time
from urllib.parse import urljoin

def clean_text(text):
    """Metni temizleme ve gereksiz boşlukları kaldırma"""
    if not text:
        return ""
    text = re.sub(r'\s+', ' ', text).strip()
    text = re.sub(r'\[.*?\]', '', text)  # Köşeli parantez içindekileri kaldır
    return text

def get_page_content(url, max_retries=3):
    """Sayfayı çek, retry mekanizması ile"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            return response
        except Exception as e:
            print(f"Deneme {attempt + 1} başarısız: {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(2)
            else:
                raise e

def extract_news_from_aurory():
    """Aurory news sayfasından haberleri çıkar - multiple methods"""
    base_url = "https://aurory.io/news/"
    
    try:
        response = get_page_content(base_url)
        soup = BeautifulSoup(response.text, 'html.parser')
        news_items = []
        
        print("Sayfa başarıyla yüklendi, haber aranıyor...")
        
        # Method 1: Standard HTML yapısını kontrol et
        possible_selectors = [
            'article',
            '.news-card',
            '.post-card',
            '.article-card',
            '[class*="news"]',
            '[class*="post"]',
            '[class*="article"]',
            'div[class*="card"]',
            'a[href*="/news/"]'
        ]
        
        found_elements = []
        for selector in possible_selectors:
            elements = soup.select(selector)
            if elements:
                print(f"'{selector}' ile {len(elements)} element bulundu")
                found_elements.extend(elements)
        
        # Method 2: Text-based extraction (fetch sonucundan gelen metinleri kullan)
        page_text = response.text
        
        # Next.js data extraction
        if '__NEXT_DATA__' in page_text:
            try:
                next_data_start = page_text.find('__NEXT_DATA__') + len('__NEXT_DATA__":')
                next_data_end = page_text.find('</script>', next_data_start)
                next_data_json = page_text[next_data_start:next_data_end]
                # JSON parsing attempts would go here
                print("Next.js data yapısı bulundu")
            except:
                pass
        
        # Method 3: Link-based extraction 
        news_links = soup.find_all('a', href=re.compile(r'/news/'))
        print(f"Haber linki bulundu: {len(news_links)}")
        
        for link in news_links[:10]:  # İlk 10 linki al
            try:
                href = link.get('href', '')
                if not href.startswith('http'):
                    href = urljoin(base_url, href)
                
                title = clean_text(link.get_text())
                if not title:
                    # Parent elementten title aramaya çalış
                    parent = link.parent
                    if parent:
                        title = clean_text(parent.get_text())
                
                if title and len(title) > 10:  # Anlamlı bir title varsa
                    news_items.append({
                        'title': title,
                        'date': "Date extraction needed",
                        'excerpt': "Content extraction needed",
                        'image_url': "Image extraction needed",
                        'link': href,
                        'scrape_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    })
            except Exception as e:
                print(f"Link işleme hatası: {str(e)}")
        
        # Method 4: Text pattern matching (bilinen haber başlıklarını yakala)
        known_patterns = [
            r'Loyalty-Based Expeditions',
            r'Blessings Will Impact',
            r'Dodorex',
            r'Easter Event',
            r'Challenges',
            r'Worldmap',
            r'PvP rewards',
            r'Valentine\'s Day',
            r'Red Packet Pursuit',
            r'Chest Eggs',
            r'Halloween Event',
            r'Chroma system',
            r'Neftie Skins',
            r'Collection Score'
        ]
        
        for pattern in known_patterns:
            if re.search(pattern, page_text, re.IGNORECASE):
                news_items.append({
                    'title': pattern.replace(r'\\', ''),
                    'date': "Pattern match - Date TBD",
                    'excerpt': f"Found pattern: {pattern}",
                    'image_url': "Pattern match - No image",
                    'link': base_url,
                    'scrape_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
        
        # Method 5: Eğer hiçbir yöntem çalışmadıysa, manuel parsing
        if not news_items:
            print("Manuel text parsing deneniyor...")
            # Daha basit text tabanlı çıkarım
            text_content = soup.get_text()
            lines = text_content.split('\n')
            
            potential_news = []
            for line in lines:
                line = clean_text(line)
                if (len(line) > 20 and len(line) < 200 and 
                    any(keyword in line.lower() for keyword in ['new', 'update', 'patch', 'event', 'introducing'])):
                    potential_news.append(line)
            
            for i, news in enumerate(potential_news[:10]):
                news_items.append({
                    'title': news,
                    'date': "Manual extraction - Date TBD",
                    'excerpt': "Extracted from page text",
                    'image_url': "Manual extraction - No image",
                    'link': base_url,
                    'scrape_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
        
        return news_items
        
    except Exception as e:
        print(f"Haber çıkarma hatası: {str(e)}")
        return []

def save_to_csv(news_items, filename):
    """Haberleri CSV dosyasına kaydet"""
    if not news_items:
        print("Kaydedilecek haber bulunamadı.")
        return
    
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['title', 'date', 'excerpt', 'image_url', 'link', 'scrape_date']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for item in news_items:
            writer.writerow(item)
    
    print(f"{len(news_items)} haber başarıyla {filename} dosyasına kaydedildi.")

def scrape_aurory_news():
    """Ana scraping fonksiyonu"""
    try:
        print("Aurory haberleri çekiliyor...")
        news_items = extract_news_from_aurory()
        
        if news_items:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"aurory_news_{timestamp}.csv"
            save_to_csv(news_items, filename)
            
            # Sonuçları göster
            print(f"\n=== BULUNAN HABERLER ({len(news_items)}) ===")
            for i, item in enumerate(news_items[:5], 1):
                print(f"{i}. {item['title'][:80]}...")
                print(f"   Link: {item['link']}")
                print()
        else:
            print("Haber bulunamadı. Site yapısı değişmiş olabilir.")
            
    except Exception as e:
        print(f"Genel hata: {str(e)}")

if __name__ == "__main__":
    scrape_aurory_news()