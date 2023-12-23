from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
import time
import os
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import NoSuchElementException
from amazoncaptcha import AmazonCaptcha
from selenium import webdriver
import json
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By


# starting the service using chrome web driver
service = Service(executable_path="F:\\university\\amazon crawler\\chromedriver.exe")
options = webdriver.ChromeOptions()
driver = webdriver.Chrome(service=service, options=options)
driver.get("https://www.amazon.com")
time.sleep(5)
# handling Amazon captcha
captcha = AmazonCaptcha.fromdriver(driver)
solution = captcha.solve()

time.sleep(5) # turn to 30 if neeeded

# get to 'video games' page
driver.get("https://www.amazon.com/s?rh=n%3A16225016011&fs=true&ref=lp_16225016011_sar")

time.sleep(30)

output_file_path = "scraped_data.json"

def findInformation():
    product_info = {
        "name": None, "rating": None, "rate_count": None, "image_src": None, "price": None, "reviews": None, "descrption": None
    }
    # product name
    try:
        product_info["name"] = driver.find_element(By.ID, "productTitle").text
    except NoSuchElementException as e:
        print("no name")

    # product rating
    try:
        product_info["rating"] = driver.find_element(By.CSS_SELECTOR, "#averageCustomerReviews_feature_div > div:nth-child(2) > span:nth-child(1) > span:nth-child(1) > span:nth-child(1) > a:nth-child(1) > span:nth-child(1)").text
    except NoSuchElementException as e:
        print("no rating")
    
    # product number of rates
    try:
        product_info["rate_count"] = driver.find_element(By.ID, "acrCustomerReviewText").text
    except NoSuchElementException as e:
        print("no rate count")

    # product image source
    try:    
        product_info["image_src"] = driver.find_element(By.ID, "landingImage").get_attribute("src")
    except NoSuchElementException as e:
        print("no image")

    # product price
    try:    
        product_info["price"] = driver.find_element(By.CSS_SELECTOR, "#corePriceDisplay_desktop_feature_div > div.a-section.a-spacing-none.aok-align-center > span.a-price.aok-align-center.reinventPricePriceToPayMargin.priceToPay > span:nth-child(2) > span.a-price-whole").text
    except NoSuchElementException as e:
        print("no price")

    # if description has further information, click on 'see more' button
    try:
        see_more_btn = driver.find_element(By.CSS_SELECTOR, "#poToggleButton > a:nth-child(2) > span:nth-child(2)")
        see_more_btn.click()
    except NoSuchElementException as e:
        print("no element") 

    # product information from table
    try:
        td_text = ""
        table = driver.find_element(By.CSS_SELECTOR, "table.a-spacing-micro")
        td_elements = table.find_elements(By.TAG_NAME, "td")
        for td_element in td_elements:
            td_text = td_text + td_element.text + " "
    except NoSuchElementException as e:
        print("no table data") 

    # product information from list
    try:
        li_text = ""
        product_ul = driver.find_element(By.CSS_SELECTOR, "ul.a-unordered-list:nth-child(3)")
        li_elements = product_ul.find_elements(By.TAG_NAME, "li")
        
        for li_element in li_elements:
            li_text = li_text + li_element.text + " "
    except NoSuchElementException as e:
        print("no list data") 

    # concating two collected informations
    print("List Item Text:", li_text)
    product_info["description"] = td_text + " " + li_text
    
    try:
        # click on review button to go to review page
        reviews_btn = driver.find_element(By.CSS_SELECTOR, "#reviews-medley-footer > div:nth-child(2) > a:nth-child(2)")
        reviews_btn.click()
        time.sleep(5)

        # find review section
        reviews = driver.find_elements(By.CSS_SELECTOR, 'span[data-hook="review-body"] span')
        review_text = []
        for rev in reviews:
            review_text.append(rev.text)

        product_info["reviews"] = review_text 

        # get back from review page to product page
        driver.back() 
    except NoSuchElementException as e:
        print("no reviews")    
    
    return product_info


# the crawling function
def crawlProduct(page):
    try:
        with open(output_file_path, "r", encoding="utf-8") as existing_file:
            existing_data = json.load(existing_file)
    except FileNotFoundError:
        existing_data = []

    for i in range(16):        
        # click on each product
        product = driver.find_element(By.XPATH, f"/html/body/div[1]/div[1]/div[1]/div[1]/div/span[1]/div[1]/div[{i+2}]/div/div/span/div/div/div/div[1]/div/div[2]/div/span/a")
        product.click()
        
        product_info = findInformation()
        
        # constructing the json of the crawled product
        product_data = {
                    "Product Name": product_info["name"],
                    "Product Price": product_info["price"],
                    "Product Rating": product_info["rating"],
                    "Product Number of Rates": product_info["rate_count"],
                    "Product Image Address": product_info["image_src"],
                    "Product Description": product_info["description"],
                    "Product Reviews": {},
                    "Related Products": []
                }

        # adding each review to the json file
        for j, review in enumerate(product_info["reviews"], start=1):
            product_data["Product Reviews"][str(j)] = review        

        # adding product index and data to json file
        existing_data.append({
            "Product Index": (page * 16) + i + 1,
            "Product Data": product_data
        })
        
        time.sleep(30)
        
        # find related products
        # from selenium.webdriver.common.keys import Keys
        # header_element = driver.find_element(By.XPATH, '//*[text()="Products related to this item"]')
        # driver.execute_script("arguments[0].scrollIntoView(true);", header_element)
        
        delay = 15
        related_products_table = None
        try:
            related_products_table = WebDriverWait(driver, delay).until(
                EC.presence_of_element_located((By.ID, 'anonCarousel1'))
            )
            print("Element is present in the DOM now")
        except TimeoutException or NoSuchElementException:
            print("Element did not show up")

        try:
            related_products_table = WebDriverWait(driver, delay).until(
                EC.presence_of_element_located((By.ID, 'anonCarousel3'))
            )
            print("Element is present in the DOM now")
        except TimeoutException or NoSuchElementException:
            print("Element did not show up")
        
        try:
            related_products_table = WebDriverWait(driver, delay).until(
                EC.presence_of_element_located((By.ID, 'anonCarousel6'))
            )
            print("Element is present in the DOM now")
        except TimeoutException or NoSuchElementException:
            print("Element did not show up")
        
        if related_products_table is not None:
            related_products = related_products_table.find_elements(By.TAG_NAME, "li")
            related_links = []
            for index, rp in enumerate(related_products):
                if index == 2:
                    break
                related_links.append(rp.find_element(By.CLASS_NAME, "a-link-normal").get_attribute("href"))
            print(related_links)
            
            # crawl related products
            for link in related_links:
                driver.get(link)
                related_product_info = findInformation()
                related_product_data = {
                        "Product Name": related_product_info["name"],
                        "Product Price": related_product_info["price"],
                        "Product Rating": related_product_info["rating"],
                        "Product Number of Rates": related_product_info["rate_count"],
                        "Product Image Address": related_product_info["image_src"],
                        "Product Description": related_product_info["description"],
                        "Product Reviews": {}
                    }
                # adding each review to the json file
                if related_product_info["reviews"] is not None:
                    for k, review in enumerate(related_product_info["reviews"], start=1):
                        related_product_data["Product Reviews"][str(k)] = review        

                product_data["Related Products"].append(related_product_data) 
                driver.back()

                time.sleep(5)

        print()

        with open(output_file_path, "w", encoding="utf-8") as json_file:
            json.dump(existing_data, json_file, ensure_ascii=False, indent=4)

        driver.back()

        time.sleep(4)

# a for loop with 7 iterations to get near 100 products
for page in range(7):
    if page != 0:        
        # find 'next' button to change page
        next_btn = driver.find_element(By.CSS_SELECTOR, "a.s-pagination-item:nth-child(8)")
        next_btn.click()

    crawlProduct(page)


driver.quit()