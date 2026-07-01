import argparse
import getpass
import os
from pathlib import Path
from urllib.parse import quote

import yaml
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.ui import WebDriverWait


DEFAULT_URL = "https://www.xn--labalana-y0a.cat"
ROOT = Path(__file__).resolve().parent


def load_dotenv(path):
    if not path.exists():
        return

    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("'\"")
        os.environ.setdefault(key, value)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Fill a La Balanca shopping cart from products.yaml."
    )
    parser.add_argument(
        "--config",
        default=ROOT / "products.yaml",
        type=Path,
        help="Path to the YAML grocery list.",
    )
    parser.add_argument(
        "--url",
        default=os.environ.get("BALANCA_URL", DEFAULT_URL),
        help="Shop base URL.",
    )
    parser.add_argument(
        "--keep-open",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Keep Chrome open when the cart is ready.",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run Chrome in headless mode.",
    )
    return parser.parse_args()


def load_config(path):
    with path.open("r") as file:
        config = yaml.safe_load(file)

    products = config.get("products", [])
    shopping_list = config.get("list", [])
    product_by_id = {product["id"]: product for product in products}
    missing = [product_id for product_id in shopping_list if product_id not in product_by_id]
    if missing:
        raise ValueError("Shopping list has unknown products: " + ", ".join(missing))

    return [product_by_id[product_id] for product_id in shopping_list]


def credentials():
    username = os.environ.get("BALANCA_USERNAME") or input("Username: ")
    password = os.environ.get("BALANCA_PASSWORD") or getpass.getpass("Password: ")
    if not username or not password:
        raise ValueError("BALANCA_USERNAME and BALANCA_PASSWORD are required.")
    return username, password


def create_driver(headless=False):
    options = webdriver.ChromeOptions()
    options.page_load_strategy = "eager"
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--disable-notifications")

    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(30)
    return driver


class Shopper:
    def __init__(self, driver, base_url):
        self.driver = driver
        self.base_url = base_url.rstrip("/")
        self.wait = WebDriverWait(driver, 20)

    def login(self, username, password):
        print("Logging in...")
        self.driver.get(f"{self.base_url}/el-meu-compte/")
        self.wait.until(EC.element_to_be_clickable((By.ID, "username"))).send_keys(username)
        password_field = self.wait.until(EC.element_to_be_clickable((By.ID, "password")))
        password_field.send_keys(password + Keys.RETURN)
        self.wait.until(
            lambda driver: driver.find_elements(By.CSS_SELECTOR, ".woocommerce-MyAccount-navigation")
            or driver.find_elements(By.CSS_SELECTOR, ".woocommerce-error")
        )
        errors = self.driver.find_elements(By.CSS_SELECTOR, ".woocommerce-error")
        if errors:
            raise RuntimeError(errors[0].text)

    def clear_cart(self):
        print("Clearing cart...")
        self.driver.get(f"{self.base_url}/cistella/")

        while True:
            remove_buttons = self.driver.find_elements(By.CSS_SELECTOR, "a.remove")
            if not remove_buttons:
                return

            button = remove_buttons[0]
            self.driver.execute_script("arguments[0].click();", button)
            self.wait.until(EC.staleness_of(button))

    def add_product(self, product):
        product_id = product["id"]
        amount = product["amount"]
        product_type = product["type"]

        print(f"Adding {product_id}...")
        self.open_product(product_id)
        if product_type == "units":
            self.set_quantity(amount)
        elif product_type == "weight":
            self.set_weight(amount)
        else:
            raise ValueError(f"Unknown product type for {product_id}: {product_type}")

        self.submit_product()

    def open_product(self, product_id):
        self.driver.get(f"{self.base_url}/productes/{quote(product_id, safe='')}/")
        self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "form.cart")))

    def set_quantity(self, amount):
        field = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "form.cart input[name='quantity']")))
        field.clear()
        field.send_keys(str(amount))

    def set_weight(self, amount):
        selector = "form.cart select[name='editar_pes'], form.cart #weight_needed"
        select = Select(self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector))))
        select.select_by_value(str(amount))

    def submit_product(self):
        button = self.wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "form.cart button[name='add-to-cart']"))
        )
        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
        button.click()
        self.wait_for_cart_update(button)

    def wait_for_cart_update(self, button):
        def cart_updated(driver):
            if is_stale(button):
                return True
            if driver.find_elements(By.CSS_SELECTOR, ".woocommerce-message, .xoo-wsc-notice-success"):
                return True
            return False

        self.wait.until(cart_updated)


def is_stale(element):
    try:
        element.is_enabled()
        return False
    except Exception:
        return True


def main():
    load_dotenv(ROOT / ".env")
    args = parse_args()
    username, password = credentials()
    products = load_config(args.config)

    print("Opening Chrome...")
    driver = create_driver(args.headless)
    shopper = Shopper(driver, args.url)
    try:
        shopper.login(username, password)
        shopper.clear_cart()
        for product in products:
            shopper.add_product(product)

        driver.get(f"{args.url.rstrip('/')}/cistella/")
        if args.keep_open:
            input("Cart is ready. Press Enter to close Chrome...")
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
