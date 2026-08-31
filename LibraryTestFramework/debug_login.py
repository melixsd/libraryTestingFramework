from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

CHROMEDRIVER_PATH = r'C:\Users\melica\.wdm\drivers\chromedriver\win64\151.0.7922.138\chromedriver-win32\chromedriver.exe'

options = Options()
options.add_argument('--headless=new')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--window-size=1280,720')

service = ChromeService(CHROMEDRIVER_PATH)
driver = webdriver.Chrome(service=service, options=options)
driver.implicitly_wait(0)

driver.get('http://localhost:3000')
print('Title:', driver.title)

wait = WebDriverWait(driver, 10)
username_sel = '[data-testid="login-username"]'
password_sel = '[data-testid="login-password"]'
submit_sel = '[data-testid="login-submit"]'

wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, username_sel))).send_keys('member1')
wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, password_sel))).send_keys('Member123!')
wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, submit_sel))).click()

# Wait for nav-home or loading to finish
try:
    wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, '[data-testid="nav-home"]')))
    print('nav-home found')
except:
    print('nav-home NOT found')

# Check for loading spinner
loading = driver.find_elements(By.CSS_SELECTOR, '[data-testid="loading"], .animate-spin, [role="status"]')
print(f'Loading elements: {len(loading)}')

# Check for search input
search = driver.find_elements(By.CSS_SELECTOR, '[data-testid="search-input"]')
print(f'Search input: {len(search)}')

# Check for error
error = driver.find_elements(By.CSS_SELECTOR, '[data-testid="login-error"]')
if error:
    print(f'Error: {error[0].text}')

# Get page source snippet
print('Page source (first 3000 chars):')
print(driver.page_source[:3000])

driver.quit()