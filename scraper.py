# scraper.py
import requests
from bs4 import BeautifulSoup
import json
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

options = Options()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-gpu")
options.add_argument("--window-size=1920,1080")

driver = webdriver.Chrome(options=options)
BASE_URL = "https://e-yaygin.meb.gov.tr/pagePrograms.aspx"

def get_detail_data(detail_url):
    driver.get(detail_url)
    wait = WebDriverWait(driver, 10)
    wait.until(EC.presence_of_element_located((By.CLASS_NAME, "modal-content")))

    soup = BeautifulSoup(driver.page_source, 'html.parser')
    modal = soup.find("div", class_="modal-content")

    sure = "Bilgi yok"
    giris = "Bilgi yok"
    egitici = "Bilgi yok"
    icerik = "Bilgi yok"

    if modal:
        sure_tag = modal.find("strong", string="Kurs Süresi:")
        if sure_tag:
            sure = sure_tag.find_next(text=True).strip()

        def get_section(header_text):
            header = modal.find("h5", string=header_text)
            return header.find_next("div").get_text(strip=False).strip() if header else "Bilgi yok"

        giris = get_section("Programa Giriş Koşulları")
        egitici = get_section("Eğitici Niteliği")
        icerik = get_section("Program Süresi ve İçeriği")

    return {"sure": sure, "girisKosullari": giris, "egiticiNiteligi": egitici, "programIcerik": icerik}

def main():
    driver.get(BASE_URL)
    time.sleep(5)

    soup = BeautifulSoup(driver.page_source, 'html.parser')
    items = soup.find_all("div", class_="program-item")

    all_data = {}

    for item in items:
        try:
            title = item.find("h5", class_="program-title").get_text(strip=True)
            detail_link = item.get("data-link")
            detail_url = f"https://e-yaygin.meb.gov.tr/{detail_link}" if detail_link else None

            if detail_url:
                details = get_detail_data(detail_url)
            else:
                details = {"sure": "", "girisKosullari": "", "egiticiNiteligi": "", "programIcerik": ""}

            # Kategori çıkar (MEB’deki gerçek alanlara göre)
            category = "Diğer"
            category_keywords = {
                "Ahşap Teknolojisi": ["ahşap", "mobilya", "talika"],
                "Bilişim": ["web", "python", "bilgisayar", "programlama"],
                "Dil Eğitimi": ["ingilizce", "almanca", "dil", "yabancı dil"],
                "Spor": ["voleybol", "basketbol", "spor", "futbol"],
                "Mesleki ve Teknik Eğitim": ["elektrik", "tesisat", "motor", "mekatronik"],
                "İşletme ve Yönetim": ["muhasebe", "işletme", "ticaret"],
                "Görsel ve İşitsel Sanatlar": ["resim", "müzik", "fotoğraf"],
                "Kişisel Gelişim": ["zihinsel", "performans", "beyin", "hafıza"],
                "El Sanatları": ["el sanatları", "örgü", "boncuk", "el yapımı"],
                "Yaratıcı Sanatlar Atölyeleri": ["drama", "oyun", "tiyatro"],
                "Zihinsel Oyunlar": ["satranç", "zeka", "oyun"],
            }
            for cat, keys in category_keywords.items():
                if any(k in title.lower() for k in keys):
                    category = cat
                    break

            kurs = {
                "ad": title,
                "sure": details["sure"],
                "girisKosullari": details["girisKosullari"],
                "egiticiNiteligi": details["egiticiNiteligi"],
                "programIcerik": details["programIcerik"]
            }

            if category not in all_data:
                all_data[category] = []
            all_data[category].append(kurs)

            logging.info(f"Kurs eklendi: {title} → {category}")

        except Exception as e:
            logging.error(f"Kurs işlenemedi: {e}")
            continue

    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)

    logging.info(f"✅ {len(all_data)} alan, {sum(len(v) for v in all_data.values())} kurs kaydedildi.")
    driver.quit()

if __name__ == "__main__":
    main()