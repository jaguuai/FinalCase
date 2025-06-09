from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def get_daory_council_members():
    driver = setup_driver()
    members = []

    try:
        driver.get("https://daory.io/")
        
        # Sayfanın yüklenip 'The DAOry Council' başlığının görünmesini bekle
        WebDriverWait(driver, 15).until(
            EC.visibility_of_element_located((By.XPATH, "//h2[contains(text(),'The DAOry Council')]"))
        )
        
        # Bu başlıktan sonraki ilk ul elementini al
        council_ul = driver.find_element(By.XPATH, "//h2[contains(text(),'The DAOry Council')]/following-sibling::ul[1]")
        council_lis = council_ul.find_elements(By.TAG_NAME, "li")

        for li in council_lis:
            a_tag = li.find_element(By.TAG_NAME, "a")
            twitter_url = a_tag.get_attribute("href")
            img_tag = a_tag.find_element(By.TAG_NAME, "img")
            img_src = img_tag.get_attribute("src")
            alt_text = img_tag.get_attribute("alt")
            name_span = a_tag.find_element(By.TAG_NAME, "span")
            name = name_span.text.replace(" 🐦", "").strip()

            position = a_tag.text.replace(name_span.text, "").strip()

            members.append({
                "name": name or alt_text,
                "twitter": twitter_url,
                "image": img_src,
                "position": position
            })

    finally:
        driver.quit()

    return members
