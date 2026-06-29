from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import yaml

from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.ui import WebDriverWait

url = "https://www.xn--labalana-y0a.cat"
username = "nadala"
password = "#&zP5aaFpe4D0"

with open("products.yaml", "r") as file:
    config = yaml.load(file, Loader=yaml.FullLoader)

product_list = config["products"]
shopping_list = config["list"]

options = webdriver.ChromeOptions()
# The store keeps loading some assets for a long time. Selenium's default
# "normal" page load strategy waits for every asset before returning from
# driver.get(), so the script can sit there before typing credentials.
# "eager" returns as soon as the HTML is loaded, then explicit waits below
# wait only for the controls we actually need.
options.page_load_strategy = "eager"

print("Opening Chrome...")
driver = webdriver.Chrome(options=options)
driver.set_page_load_timeout(20)
wait = WebDriverWait(driver, 15)

def login():
    print("Logging in...")
    driver.get(f"{url}/el-meu-compte")
    wait.until(EC.element_to_be_clickable((By.ID, "username"))).send_keys(username)
    wait.until(EC.element_to_be_clickable((By.ID, "password"))).send_keys(password + Keys.RETURN)
    wait.until(lambda d: not d.find_elements(By.ID, "password"))

def clear_cart():
    print("Clearing cart...")
    driver.get(f"{url}/cistella")

    while True:
        elements = driver.find_elements(By.CSS_SELECTOR, 'a[class*="remove"]')
        if not elements:
            break

        element = elements[0]
        driver.execute_script("arguments[0].click();", element)
        wait.until(EC.staleness_of(element))

def add_to_cart_by_unit(product_id, amount):
    driver.get(f"{url}/productes/{product_id}")
    field = wait.until(EC.element_to_be_clickable((By.NAME, "quantity")))
    field.clear()
    field.send_keys(amount)
    wait.until(EC.element_to_be_clickable((By.NAME, "add-to-cart"))).click()

def add_to_cart_by_weight(product_id, amount):
    driver.get(f"{url}/productes/{product_id}")
    select = Select(wait.until(EC.element_to_be_clickable((By.ID, "editar_pes"))))
    select.select_by_value(str(amount))
    wait.until(EC.element_to_be_clickable((By.NAME, "add-to-cart"))).click()

try:
    login()
    clear_cart()
    for product in product_list:
        if product["id"] not in shopping_list:
            continue
        print(f"Adding {product['id']}...")
        if product["type"] == "units":
            add_to_cart_by_unit(product["id"], product["amount"])
        if product["type"] == "weight":
            add_to_cart_by_weight(product["id"], product["amount"])

    driver.get(f"{url}/cistella")
    input("Cart is ready. Press Enter to close Chrome...")
finally:
    driver.quit()
