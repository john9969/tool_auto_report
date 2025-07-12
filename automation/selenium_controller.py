from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import TimeoutException, WebDriverException
import time
from urllib.parse import urljoin
import datetime
LINK = 'http://madien2.kttvdb.vn/content/users/login.asp?ret_page=../../content/code/'
LINK_REPORT = "http://madien2.kttvdb.vn/content/code/"
USER = 'tvtrieuduong'
PASS = '91376'
ZALO_CHAT_NAME ="report_tvtrieuduong"

def login(user: str, password: str, link: str):
    """Open Chromium headless, navigate to link, fill credentials, click logon, and return the driver."""
    print(f"[Login] Starting login process for user: {user}")

    options = Options()
    options.binary_location = '/usr/bin/chromium-browser'
    #options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    service = Service('/usr/bin/chromedriver')  # updated path

    print("[Login] Initializing Chromium driver (headless)")
    driver = webdriver.Chrome(service=service, options=options)
    print("[Login] Waiting for driver warmup (2s)")
    time.sleep(2)
    driver.set_page_load_timeout(30)
    print("[Login] Chromium driver initialized")

    try:
        print(f"[Login] Navigating to {link}")
        driver.get(link)
        print("[Login] Page load completed")

        print("[Login] Locating username field")
        el_user = driver.find_element(By.NAME, 'username')
        print("[Login] Clearing username field")
        el_user.clear()
        print("[Login] Entering username")
        el_user.send_keys(user)
        print(f"[Login] Username '{user}' entered")

        print("[Login] Locating password field")
        el_pass = driver.find_element(By.NAME, 'password')
        print("[Login] Clearing password field")
        el_pass.clear()
        print("[Login] Entering password")
        el_pass.send_keys(password)
        print("[Login] Password entered")

        print("[Login] Locating logon button")
        btn = driver.find_element(By.NAME, 'logon')
        print("[Login] Clicking logon button")
        btn.click()
        print("[Login] Logon button clicked")

        print("[Login] Waiting for post-login page to load (3s)")
        time.sleep(3)

        print("[Login] Login successful, returning driver instance")
        return driver,True

    except TimeoutException:
        print(f"[Login] Timeout loading page")
        driver.quit()
        return driver,False
    except WebDriverException as e:
        print(f"[Login] WebDriver error")
        driver.quit()
        return driver,False
    except Exception as e:
        print(f"[Login] Unexpected error")
        driver.quit()
        return driver,False
        
def navigate_to_add_matv(driver):
    try:
        today = datetime.date.today().strftime('%Y/%-m/%-d')
        path = f"add_maTV.asp?page_type=0&idd=104&ngay={today}&ngayxem={today}"
        print(f"path:{path}")
        full_url = urljoin(LINK_REPORT, path)
        print(f"[Navigate] Going to {full_url}")
        driver.get(full_url)
        print("[Navigate] Reached add_maTV page")
        time.sleep(5)
        return driver,True
    except TimeoutException:
        print(f"[Login] Timeout loading page")
        driver.quit()
        return driver,False
    except WebDriverException as e:
        print(f"[Login] WebDriver error")
        driver.quit()
        return driver,False
    except Exception as e:
        print(f"[Login] Unexpected error")
        driver.quit()
        return driver,False

def select_current_hour_and_confirm(driver):
    now = datetime.datetime.now()
    hour = now.hour if now.hour != 0 else 24
    print(f"[Select] Current hour: {hour}")
    try:
        select_el = driver.find_element(By.NAME, 'gio')
        select = Select(select_el)
        select.select_by_value(str(hour))
        time.sleep(5)
        print(f"[Select] Selected hour option: {hour}")
        btn_ok = driver.find_element(By.NAME, 'OK')
        btn_ok.click()
        print("[Select] Clicked OK button")
        return driver,True
    except NoSuchElementException as e:
        print(f"[Select] Element not found: {e}")
        return driver,False

def fill_content_and_submit(driver, content: str):
    try:
        print(f"[Fill] Locating 'noidungmadien' field")
        field = driver.find_element(By.NAME, 'noidungmadien')
        field.clear()
        print(f"[Fill] Entering content: {content}")
        field.send_keys(content)
        print("[Fill] Content entered")

        print("[Fill] Locating 'ma_tr' field")
        ma_tr_el = driver.find_element(By.NAME, 'ma_tr')
        print("[Fill] Locating submit button relative to 'ma_tr'")
        submit_btn = ma_tr_el.find_element(By.XPATH, 'following::input[@type="submit"][1]')
        print("[Fill] Clicking submit button")
        time.sleep(1)
        if content != "checking":
            print("[Fill] Content is not 'checking', clicking submit")
            #submit_btn.click()
        print(f"[fill] not submitting content: {content}")
        return driver,True
    except NoSuchElementException as e:
        print(f"[Fill] Element not found: {e}")
        return driver,False

def send_zalo_message(driver: webdriver.Chrome,message: str):
    print("[Zalo] Navigating to chat.zalo.me")
    driver.get('https://chat.zalo.me')
    time.sleep(5)  # wait for chat list

    print(f"[Zalo] Locating chat item: {ZALO_CHAT_NAME}")
    items = driver.find_elements(By.CLASS_NAME, 'truncate')
    for item in items:
        if item.text.strip() == ZALO_CHAT_NAME:
            item.click()
            print("[Zalo] Chat selected")
            break
    else:
        print("[Zalo] Chat not found")
        return

    time.sleep(3)
    print("[Zalo] Locating message input container")
    input_container = driver.find_element(By.ID, 'chat-input-container-id')
    input_container.click()
    input_container.send_keys(message)
    input_container.send_keys(Keys.ENTER)
    print("[Zalo] Message sent")
    
def selenium_controller(ma_dien_bao:str):
    print("[Main] Starting script")
    driver,stt = login(USER, PASS, LINK)
    if stt == False:
        send_zalo_message("[Web Error]:" + ma_dien_bao)
        return 
    driver,stt = navigate_to_add_matv (driver)
    if stt == False:
        send_zalo_message("[Web Error]:" + ma_dien_bao)
        return 
    driver,stt = select_current_hour_and_confirm(driver)
    if stt == False:
        send_zalo_message("[Web Error]:" + ma_dien_bao)
        return 
    driver,stt = fill_content_and_submit(driver, content= ma_dien_bao)
    if stt == False:
        send_zalo_message("[Web Error]:" + ma_dien_bao)
        return
    
    print("[Main] Script completed, quitting driver")
    driver.quit()
