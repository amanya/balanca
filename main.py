from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import yaml
import time

from selenium.webdriver.support.select import Select

url = "https://www.xn--labalana-y0a.cat"
username = ""
password = ""

with open("products.yaml", "r") as file:
    config = yaml.load(file, Loader=yaml.FullLoader)

product_list = config["products"]
shopping_list = config["list"]

driver = webdriver.Chrome()
driver.implicitly_wait(10)

def login():
    driver.get(f"{url}/el-meu-compte")
    driver.find_element(By.ID, "username").send_keys(username)
    driver.find_element(By.ID, "password").send_keys(password + Keys.RETURN)

def clear_cart():
    driver.get(f"{url}/cistella")
    elements = driver.find_elements(By.CSS_SELECTOR, 'a[class*="remove"]')
    for element in elements:
        driver.execute_script("arguments[0].click();", element)
        driver.implicitly_wait(10)

def add_to_cart_by_unit(product_id, amount):
    driver.get(f"{url}/productes/{product_id}")
    field = driver.find_element(By.NAME, "quantity")
    field.clear()
    field.send_keys(amount)
    button = driver.find_element(By.NAME, "add-to-cart")
    button.click()

def add_to_cart_by_weight(product_id, amount):
    driver.get(f"{url}/productes/{product_id}")
    select = Select(driver.find_element(By.ID, "editar_pes"))
    select.select_by_value(str(amount))
    button = driver.find_element(By.NAME, "add-to-cart")
    button.click()

login()
clear_cart()
for product in product_list:
    if product["id"] not in shopping_list:
        continue
    if product["type"] == "units":
        add_to_cart_by_unit(product["id"], product["amount"])
    if product["type"] == "weight":
        add_to_cart_by_weight(product["id"], product["amount"])

driver.get(f"{url}/cistella")

while True:
    pass
