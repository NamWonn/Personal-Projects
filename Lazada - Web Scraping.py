import csv
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

edge_options = Options()
edge_options.add_argument("--headless")
edge_options.add_argument("--disable-gpu")
service = Service(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedgedriver.exe")
driver = webdriver.Edge(service=service, options=edge_options)

try:
    url = "https://www.lazada.vn/catalog/?spm=a2o4n.homepage.search.d_go&q=iphone"
    driver.get(url)

    wait = WebDriverWait(driver, 5)
    product_elements = wait.until(
        EC.presence_of_all_elements_located((By.CLASS_NAME, "RfADt"))
    )
    price_elements = wait.until(
        EC.presence_of_all_elements_located((By.CLASS_NAME, "aBrP0"))
    )

    product_names = [element.text for element in product_elements]
    product_prices = [element.text for element in price_elements]

    print("Product Details:")
    for name, price in zip(product_names, product_prices):
        print(f"{name} - {price}")

    with open("Lazada_Iphone_Dataset.csv", mode="w", newline="", encoding="utf-8-sig") as file:
        writer = csv.writer(file)
        writer.writerow(["Product Name", "Price"])  
        for name, price in zip(product_names, product_prices):
            writer.writerow([name, price])  

    print("\nData has been written to 'lazada_products.csv'.")

except Exception as e:
    print(f"An error occurred: {e}")

finally:
    driver.quit()
