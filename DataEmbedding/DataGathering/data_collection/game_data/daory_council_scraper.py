from bs4 import BeautifulSoup
import csv
import re

html_content = """
<section class="bg-gradient-to-b from-gray-900 to-transparent py-10 lg:py-24">
               <div class="max-w-7xl mx-auto px-4 lg:px-8">
                  <div class="max-w-6xl" style="text-align: center;">
                     <h2 class="text-5xl  text-white">
                        <span class=" font-bold block text-left tracking-wider text-lg text-color-light"></span>
                        The DAOry Council
                     </h2>
                     <br>
                     <p class="text-xl font-light mt-4">
                        Aurorian holders community chooses its Council every 6 months through transparent elections held in Discord and soon on our own onchain voting solution.
                     </p>
                     <br>
                     <br>
                  </div>
                  <ul class="grid gap-4 sm:gap-6 md:grid-cols-4 md:gap-8 xl:gap-12 mt-14">
                     <li class="text-center "><a href="https://twitter.com/joenaes_" target="_blank">
                        <img src="./DAOry_files/Joenaes.jpg" alt="Joenaes" loading="lazy" class="rounded-3xl mb-3 shadow-xl shadow-gray-800 imageCouncil">
                        <span class="text-white text-xl block">
                        Joenaes <i class="fa fa-twitter"></i>
                        </span>Head of Council</a>
                        <span class="font-medium text-brand-gold-light tracking-tight">
                        </span>
                     </li>
                     <li class="text-center "><a href="https://twitter.com/MVB_gg" target="_blank">
                        <img src="./DAOry_files/MVB.jpg" alt="MVB" loading="lazy" class="rounded-3xl mb-3 shadow-xl shadow-gray-800 imageCouncil">
                        <span class="text-white text-xl block">
                        MVB <i class="fa fa-twitter"></i>
                        </span>Community &amp; Outreach</a>
                        <span class="font-medium text-brand-gold-light tracking-tight">
                        </span>
                     </li>
                     <li class="text-center "><a href="https://twitter.com/chocoo_web3" target="_blank">
                        <img src="./DAOry_files/chocoopanda.jpg" alt="webtricks" loading="lazy" class="rounded-3xl mb-3 shadow-xl shadow-gray-800 imageCouncil">
                        <span class="text-white text-xl block">
                        Chocoopanda <i class="fa fa-twitter"></i>
                        </span>Structure &amp; Document.</a>
                        <span class="font-medium text-brand-gold-light tracking-tight">
                        </span>
                      </li>
                      <li class="text-center "><a href="https://twitter.com/R________101" target="_blank">
                        <img src="./DAOry_files/R.jpg" alt="Nikki" loading="lazy" class="rounded-3xl mb-3 shadow-xl shadow-gray-800 imageCouncil">
                        <span class="text-white text-xl block">
                        R <i class="fa fa-twitter"></i>
                        </span>Infra &amp; Development</a>
                        <span class="font-medium text-brand-gold-light tracking-tight">
                        </span>
                     </li>
                      <li class="text-center "><a href="https://twitter.com/metafi_" target="_blank">
                        <img src="./DAOry_files/Martin.jpg" alt="Martin | MetaFi" loading="lazy" class="rounded-3xl mb-3 shadow-xl shadow-gray-800 imageCouncil">
                        <span class="text-white text-xl block">
                        Martin <i class="fa fa-twitter"></i>
                        </span>Finance &amp; Investments</a>
                        <span class="font-medium text-brand-gold-light tracking-tight">
                        </span>
                     </li>
                  </ul>
               </div>
               <br>
               <br>
               <br>
               
               <div class="max-w-7xl mx-auto px-4 lg:px-8">
                  <div class="max-w-6xl" style="text-align: center;">
                     <h2 class="text-5xl  text-white">
                        <span class=" font-bold block text-left tracking-wider text-lg text-color-light"></span>
                        Advisors
                     </h2>
                  </div>
                  <ul class="grid gap-4 sm:gap-6 md:grid-cols-4 md:gap-8 xl:gap-12 mt-14">
                     <li class="text-center "><a href="" target="_blank">
                        <img src="" loading="lazy" class="rounded-3xl mb-3 shadow-xl shadow-gray-800 imageCouncil">
                        <span class="text-white text-xl block">
                        
                        </span></a>
                        <span class="font-medium text-brand-gold-light tracking-tight">
                        </span>
                     </li>
                     <li class="text-center "><a href="https://twitter.com/crypto_sigmund" target="_blank">
                        <img src="./DAOry_files/Poochi.jpg" alt="Poochi" loading="lazy" class="rounded-3xl mb-3 shadow-xl shadow-gray-800 imageCouncil">
                        <span class="text-white text-xl block">
                        Poochi <i class="fa fa-twitter"></i>
                        </span></a>
                        <span class="font-medium text-brand-gold-light tracking-tight">
                        </span>
                     </li>  
                     <li class="text-center "><a href="https://twitter.com/Afka_XBT" target="_blank">
                        <img src="./DAOry_files/Afka.jpg" alt="Afka" loading="lazy" class="rounded-3xl mb-3 shadow-xl shadow-gray-800 imageCouncil">
                        <span class="text-white text-xl block">
                        Afka <i class="fa fa-twitter"></i>
                        </span></a>
                        <span class="font-medium text-brand-gold-light tracking-tight">
                        </span>
                     </li>
                     <li class="text-center "><a href="" target="_blank">
                        <img src="./DAOry_files/northstrider1.jpg" alt="Northstrider" loading="lazy" class="rounded-3xl mb-3 shadow-xl shadow-gray-800 imageCouncil">
                        <span class="text-white text-xl block">
                        Northstrider
                        </span></a>
                        <span class="font-medium text-brand-gold-light tracking-tight">
                        </span>
                     </li>
                  </ul>
               </div>
            </section>
"""

soup = BeautifulSoup(html_content, 'html.parser')

# Council verilerini çıkar (görsel olmadan)
def extract_council():
    council_data = []
    
    # Esnek başlık arama
    council_header = soup.find(lambda tag: tag.name == 'h2' and 'DAOry Council' in tag.text)
    
    if not council_header:
        return council_data
    
    council_ul = council_header.find_next('ul')
    
    for li in council_ul.find_all('li'):
        a_tag = li.find('a')
        if not a_tag:
            continue
            
        # İsim bilgisi
        name_span = a_tag.find('span', class_='text-white')
        name = name_span.get_text(strip=True).replace('\n', '') if name_span else ''
        
        # Rol bilgisi (görsel olmadan)
        role_text = ''.join([text for text in a_tag.contents if isinstance(text, str)]).strip()
        
        twitter_url = a_tag.get('href', '')
        
        council_data.append({
            'Name': name,
            'Role': role_text,
            'Twitter URL': twitter_url
        })
    
    return council_data

# Advisor verilerini çıkar (görsel olmadan)
def extract_advisors():
    advisors_data = []
    
    # Esnek başlık arama
    advisors_header = soup.find(lambda tag: tag.name == 'h2' and 'Advisors' in tag.text)
    
    if not advisors_header:
        return advisors_data
    
    advisors_ul = advisors_header.find_next('ul')
    
    for li in advisors_ul.find_all('li'):
        a_tag = li.find('a')
        if not a_tag:
            continue
            
        # İsim bilgisi
        name_span = a_tag.find('span', class_='text-white')
        name = name_span.get_text(strip=True).replace('\n', '') if name_span else ''
        
        twitter_url = a_tag.get('href', '')
        
        # Boş kayıtları atla
        if name or twitter_url:
            advisors_data.append({
                'Name': name,
                'Twitter URL': twitter_url
            })
    
    return advisors_data

# CSV dosyalarına yaz
def write_to_csv(filename, data, fieldnames):
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

# Verileri çıkar ve CSV'ye yaz
council_data = extract_council()
if council_data:
    write_to_csv('council.csv', council_data, 
                ['Name', 'Role', 'Twitter URL'])
    print("Council CSV oluşturuldu: council.csv")
else:
    print("Council verisi bulunamadı!")

advisors_data = extract_advisors()
if advisors_data:
    write_to_csv('advisors.csv', advisors_data, 
                ['Name', 'Twitter URL'])
    print("Advisors CSV oluşturuldu: advisors.csv")
else:
    print("Advisors verisi bulunamadı!")

print("\nÇıktı Örnekleri:")
if council_data:
    print("\nCouncil Örnek Kayıt:")
    print(council_data[0])
    
if advisors_data:
    print("\nAdvisors Örnek Kayıt:")
    print(advisors_data[0])