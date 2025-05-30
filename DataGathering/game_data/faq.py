from bs4 import BeautifulSoup
import csv

html_content = """
<div style="padding-top: 80px">
               <div class="max-w-6xl max-w-7xl mx-auto px-4 lg:px-8" style="text-align: center; margin-top: 60px; margin-bottom: 60px;" id="faq">
                  <h2 class="text-5xl  text-white">
                     <span class=" font-bold block text-left tracking-wider text-lg text-color-light"></span>
                     FAQ    
                  </h2>
               </div>
               <div class="faqs ">
                  <details class="MuiPaper-root-593 jss523 MuiPaper-elevation0-596 MuiPaper-rounded-594">
                     <summary class=".jss518" style="font-size: 18px;">What is Aurory?</summary>
                     <p class=".jss518"><br>AURORY is a free-to-play, tactical, turn-based JRPG built on the Solana blockchain. Players are invited to explore a rich and diverse universe where they will travel across the worlds of Antik and Tokané as they complete quests, discover lost relics, defeat enemies, and compete against other players using creatures called "Nefties". These magical creatures can be hatched, evolved,
                        traded, used to battle, and have been designed as non-
                        fungible tokens (NFTs). They will accompany players
                        as they embark on their adventure through a variety of
                        immersive game modes in this compelling JRPG.
                     </p>
                  </details>
                  <details class="MuiPaper-root-593 jss523 MuiPaper-elevation0-596 MuiPaper-rounded-594">
                     <summary class=".jss518" style="font-size: 18px;">What is DAOry?</summary>
                     <p class=".jss518"><br>The DAOry is a decentralized
                        autonomous organization (DAO)
                        for Aurory and is entirely run by the
                        community. This means that the
                        Aurory team will not interfere or
                        make decisions for DAOry. Aurorian
                        holders are in control of DAOry,
                        which is funded with:<br><br>
                        • 1,000 SOL provided by the team from the initial sale.<br>
                        • 1.75% of Aurorian sales via the NFT marketplace royalties.<br>
                        • 5% of the total $AURY supply over a period of time.<br>
                        • A percentage (TBD) of in-game marketplace fees.
                     </p>
                  </details>
                  <details class="MuiPaper-root-593 jss523 MuiPaper-elevation0-596 MuiPaper-rounded-594">
                     <summary class=".jss518" style="font-size: 18px;">What are the Aurorian Holders benefits?</summary>
                     <p class=".jss518"><br>Aurorian NFTs provide benefits in and outside of the game, and go well beyond the scope of most NFT projects. 
                        Some of these benefits consist of:<br><br>
                        - Aurorians are unique playable characters in the game (non-holders will use a default Sam skin).<br>
                        - Early access for future game modes and priority access to the closed beta. Non-holders will have access to the open beta as player capacity increases. <br>
                        - Early access to land sales. More details will be revealed in due time.<br>
                        - Boosted rewards in select game modes. Balance and fairness will be prioritized at all times to avoid pay-to-win mechanics.<br>
                        - Free NFT airdrops of both collectible and functional in-game item NFTs during the game's development. The team will not announce the snapshot or the contents of the airdrops. These will be distributed as surprises to NFT holders who have their Aurorians delisted. Sometimes, airdrops will also be given to eligible $AURY holders who do not have their coins on exchanges.<br>
                        - Option to send Aurorians on timed expeditions for a chance to earn $AURY, collectibles, and in-game items.<br>
                        - Each Aurorian is backed by 1/10,000th of the DAO treasury.<br>
                        - Aurorian holders will be allowed to vote in the DAOry's decision-making process, including treasury distributions to holders, council elections, marketing initiatives, community events, investment ventures, and more.
                     </p>
                  </details>
                  <details class="MuiPaper-root-593 jss523 MuiPaper-elevation0-596 MuiPaper-rounded-594">
                     <summary class=".jss518" style="font-size: 18px;">How can I join DAOry?</summary>
                     <p class=".jss518"><br>You can join DAOry and enjoy all of the Aurorian holders benefits by obtaining an Aurorian. <br><br>It can be easily done through Aurory Marketplace or through some of the Solana decentralized exchanges like MagicEden or SolanArt</p>
                  </details>
               </div>
            </div>
"""

soup = BeautifulSoup(html_content, 'html.parser')

def extract_faq():
    faq_data = []
    
    # SSS başlığını bul (text içindeki FAQ kelimesini kontrol et)
    faq_header = None
    for h2 in soup.find_all('h2'):
        if 'FAQ' in h2.get_text(strip=True):
            faq_header = h2
            break
    
    if not faq_header:
        return faq_data
    
    # SSS container'ını bul
    faq_container = faq_header.find_next('div', class_='faqs')
    
    if not faq_container:
        return faq_data
    
    # Tüm detayları al
    for details in faq_container.find_all('details'):
        # Soruyu çıkar
        summary = details.find('summary')
        question = summary.get_text(strip=True) if summary else ''
        
        # Cevabı çıkar
        answer_paragraph = details.find('p')
        if answer_paragraph:
            # <br> etiketlerini yeni satıra dönüştür
            for br in answer_paragraph.find_all('br'):
                br.replace_with('\n')
            
            answer = answer_paragraph.get_text()
            answer = answer.strip()
        else:
            answer = ''
        
        faq_data.append({
            'Question': question,
            'Answer': answer
        })
    
    return faq_data


# CSV dosyasına yaz
def write_to_csv(filename, data):
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['Question', 'Answer']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

# Verileri çıkar ve CSV'ye yaz
faq_data = extract_faq()
if faq_data:
    write_to_csv('faq.csv', faq_data)
    print("FAQ CSV oluşturuldu: faq.csv")
    
    # Önizleme göster
    print("\nÖrnek Kayıtlar:")
    for i, item in enumerate(faq_data[:2], 1):
        print(f"\n{i}. Soru:")
        print(item['Question'])
        print("\nCevap:")
        print(item['Answer'][:100] + "..." if len(item['Answer']) > 100 else item['Answer'])
else:
    print("SSS verisi bulunamadı!")