from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
import time

class SeleniumController:
    def run(self):
        options = Options()
        options.add_argument('--headless')
        driver = webdriver.Chrome(service=ChromeService(), options=options)
        driver.get("https://example.com")
        time.sleep(2)
        driver.quit()