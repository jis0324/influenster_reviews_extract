# -*- coding: utf-8 -*-
import os
import re
import time
import traceback
import json
import csv
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.remote_connection import LOGGER
from selenium.webdriver.chrome.service import Service

LOGGER.setLevel(logging.WARNING)
base_dir = os.path.dirname(os.path.abspath(__file__))


def set_driver(arg):
    try:
        # user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_3) AppleWebKit/537.36 (KHTML, like Gecko) ' \
        #         'Chrome/80.0.3987.132 Safari/537.36'
        # chrome_options = webdriver.ChromeOptions()
        # chrome_options.add_argument('headless')
        # chrome_options.add_argument("--start-maximized")
        # chrome_options.add_argument('--no-sandbox')
        # chrome_options.add_argument('--disable-dev-shm-usage')
        # chrome_options.add_argument('--ignore-certificate-errors')
        # chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        # chrome_options.add_argument(f'user-agent={user_agent}')

        # if arg in ["category", "product"]:
        #     pass
        # else:
        #     chrome_options.add_argument('--headless')

        # experimentalFlags = ['same-site-by-default-cookies@1','cookies-without-same-site-must-be-secure@1']
        # chromeLocalStatePrefs = { 'browser.enabled_labs_experiments' : experimentalFlags}
        # chrome_options.add_experimental_option('localState',chromeLocalStatePrefs)
        # chrome_options.add_argument('--headless')
        driver = webdriver.Chrome(options=chrome_options)
        
        return driver

    except:
        print(traceback.print_exc())
        return None


class InfluensterCrawler:

    # init
    def __init__(self):
        # init web driver
        self.driver = None
        self.accepted_cookie_flag = False
        self.processed_count = 0
        
        # get config
        self.config = json.load(open(base_dir + "/config.json",))
        if "sleep_value" not in self.config:
            self.config["sleep_value"] = 2
        print(json.dumps(self.config, indent=4))

    # scroll down
    def scroll_event(self): 
        try:
            # page height before scroll down
            before_height = self.driver.execute_script("return document.body.scrollHeight")

            # scroll down to the bottom.
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            self.driver.implicitly_wait((int(before_height / 5000) + 1) * 10)
            # page height after scroll down
            after_height = self.driver.execute_script("return document.body.scrollHeight")

            print(before_height,"/",after_height)

            if after_height > before_height:
                before_height = after_height
                print('----- Scrolled Down -----')
                return True
            else:
                return False
        except:
            print(traceback.print_exc())
            return False

    # main function
    def start(self):
        # iterate websites
        category_urls = self.config["categories"]

        for category_url in category_urls:
            category_name = category_url.rsplit("/", 1)[1]
            output_csv_path = "{}/result-{}.csv".format(base_dir, category_name)

            # delete old result csv file 
            file_exist = os.path.isfile(output_csv_path)
            if file_exist:
                os.remove(output_csv_path)

            try:
                # create web driver
                self.driver = set_driver("category")
                
                if self.driver is None:
                    print("Can Not Create Driver. Please Try Again.")
                    return

                # get inventory url
                self.driver.get(category_url)
                amount_ele = WebDriverWait(self.driver, 1200).until(lambda driver: driver.find_element_by_xpath("//div[@class='column-results-title']/h2/strong[1]"))
                amount = re.search(r'^\d+', amount_ele.text).group()
                page_count = int(int(amount) / 18) + 1
                print("----- Found {} products, and {} listing pages From '{}' Category Page".format(amount, page_count, category_url.rsplit("/", 1)[1]))

                for index in range(page_count):
                    try:
                        request_url = "{}?page={}".format(category_url, index+1)
                        self.driver.get(request_url)

                        review_values = WebDriverWait(self.driver, 120).until(lambda driver: driver.find_elements_by_xpath("//div[@class='category-product-stars']/div[@data-stars]"))

                        if review_values[0].get_attribute("@data-stars") == "0.0":
                            break

                        products = self.driver.find_elements_by_xpath("//a[@class='category-product'][@href]")
                        print("---------------------")
                        print("Found {} products from {}".format(len(products), request_url))

                        products_list = list()
                        for product in products:
                            product_attr = dict()
                            try:
                                product_url = product.get_attribute("href").strip()
                                product_attr["product_url"] = product_url
                            except:
                                product_attr["product_url"] = ""
                            
                            try:
                                product_attr["product_name"] = product.find_element_by_xpath(".//div[@class='category-product-title']").text.strip()
                            except:
                                product_attr["product_name"] = ""
                            
                            try:
                                product_attr["product_brand"] = re.sub(r'by\s*', '', product.find_element_by_xpath(".//div[@class='category-product-brand']").text.strip(), flags=re.I)
                            except:
                                product_attr["product_brand"] = ""
                            
                            try:
                                product_attr["rating"] = product.find_element_by_xpath(".//div[@class='category-product-stars']/div[@data-stars]").get_attribute("data-stars")
                            except:
                                product_attr["rating"] = ""

                            products_list.append(product_attr)

                        for product in products_list:
                            try:
                                self.processed_count = 0
                                self.driver.get(product["product_url"] + "/media")
                                print('Start Getting "{}" Product Reviews'.format(product["product_url"].rsplit("/", 1)[1]))

                                while True:
                                    WebDriverWait(self.driver, 120).until(lambda driver: driver.find_elements_by_xpath("//div[@class='list']/div[contains(@class, 'item')]/div[1]"))
                                    self.driver.implicitly_wait(10)
                                    time.sleep(self.config["sleep_value"])
                                    review_elements = WebDriverWait(self.driver, 120).until(lambda driver: driver.find_elements_by_xpath("//div[@class='list']/div[contains(@class, 'item')]/div[1]"))
                                    new_review_elements = review_elements[self.processed_count:]
                                    print("Found {} / {} New Review Elements.".format(len(new_review_elements), len(review_elements)))

                                    for element in new_review_elements:
                                        try:
                                            self.processed_count += 1

                                            if self.processed_count > self.config["limit_review_count"]:
                                                break
                                            else:

                                                if not self.accepted_cookie_flag:
                                                    try:
                                                        accept_cookie_btn = self.driver.find_element_by_xpath("//button[@id='onetrust-accept-btn-handler']")
                                                        if accept_cookie_btn:
                                                            accept_cookie_btn.click()
                                                            print("Accepted Cookie.")
                                                            self.driver.implicitly_wait(3)
                                                            time.sleep(self.config["sleep_value"])
                                                            self.accepted_cookie_flag = True
                                                    except:
                                                        pass
                                                
                                                record = product.copy()
                                                try:
                                                    element.click()
                                                    print("Clicked {}th Review Element.".format(self.processed_count))

                                                except:
                                                    time.sleep(self.config["sleep_value"] / 4)
                                                    pass

                                                user_name_ele = WebDriverWait(self.driver, 120).until(lambda driver: driver.find_element_by_xpath("//div[contains(@class, 'ReactModal__Content')]/div/div[2]/div/div[1]/a[@href]"))
                                                self.driver.implicitly_wait(5)
                                                time.sleep(self.config["sleep_value"])

                                                try:
                                                    record["user_name"] = user_name_ele.text
                                                except:
                                                    record["user_name"] = ""
                                                
                                                try:
                                                    record["user_url"] = user_name_ele.get_attribute("href")
                                                except:
                                                    record["user_url"] = ""
                                                
                                                try:
                                                    record["comment"] = self.driver.find_element_by_xpath("//div[contains(@class, 'ReactModal__Content')]/div/div[3]/div[2]/div[last()]/div[last()]").text
                                                except:
                                                    record["comment"] = ""
                                                
                                                try:
                                                    record["user_img"] = self.driver.find_element_by_xpath("//div[contains(@class, 'ReactModal__Content')]/div/div[2]/a//img").get_attribute("src")
                                                except:
                                                    record["user_img"] = ""
                                            
                                                try:
                                                    rating_class_list = ["gRUygt", "MVvhW", "bDvYHg", "iibyyi", "dQneJo", "cXTpuH", "NgMdV", "eegwjt", "NTulO", "fBLuLO", "eSuKgz", "gEfMYN", "eBQXmq"]

                                                    rating_class_vs_value = {
                                                        "gRUygt": 1,
                                                        "MVvhW": 0.6,
                                                        "iibyyi": 0.6,
                                                        "cXTpuH": 0.6,
                                                        "NgMdV": 0.6,
                                                        "bDvYHg": 0.4,
                                                        "dQneJo": 0.4,
                                                        "gEfMYN": 0.4,
                                                        "eSuKgz": 0.3,
                                                        "NTulO": 0.2,
                                                        "eegwjt": 0.1,
                                                        "fBLuLO": 0,
                                                        "eBQXmq": 0

                                                    }
                                                    rating = 0
                                                    rating_elements = self.driver.find_elements_by_xpath("//div[contains(@class, 'ReactModal__Content')]/div/div[3]/div[2]/div[3]/div[1]/div")
                                                    if len(rating_elements):
                                                        for item in rating_elements:
                                                            classes = item.get_attribute("class")
                                                            for class_item in rating_class_list:
                                                                if class_item in classes:
                                                                    if class_item in rating_class_vs_value:
                                                                        rating += rating_class_vs_value[class_item]
                                                                    else:
                                                                        rating += 1
                                                                    break
                                                    
                                                        record["rating"] = rating
                                                except:
                                                    pass
                                                
                                                try:
                                                    record["img_url"] = self.driver.find_element_by_xpath("//div[contains(@class, 'ReactModal__Content')]/div/div[3]/div[1]//img").get_attribute("src")
                                                except:
                                                    record["img_url"] = ""

                                                try:
                                                    record["video_url"] = self.driver.find_element_by_xpath("//div[contains(@class, 'ReactModal__Content')]/div/div[3]/div[1]//div[contains(@class, 'jwplayer')]").get_attribute("id").strip()
                                                except:
                                                    record["video_url"] = ""

                                                try:
                                                    if record["video_url"]:
                                                        record["video_or_photo"] = "video"
                                                    elif record["img_url"]:
                                                        record["video_or_photo"] = "photo"
                                                    else:
                                                        record["video_or_photo"] = ""
                                                except:
                                                    record["video_or_photo"] = ""
                                                
                                                try:
                                                    record["post_url"] = self.driver.current_url
                                                except:
                                                    record["post_url"] = ""

                                                try:
                                                    record["user_location"] = self.driver.find_element_by_xpath("//div[contains(@class, 'ReactModal__Content')]/div/div[2]/div/div[last()]").text.split("-", 1)[0]
                                                    if "review" in record["user_location"]:
                                                        record["user_location"] == ""
                                                except:
                                                    record["user_location"] = ""
                                                
                                                record["user_intro"] = ""
                                                if self.config["user_intro_flag"]:
                                                    if record["user_url"]:
                                                        try:
                                                            user_driver = None
                                                            user_driver = set_driver("user")
                                                            user_driver.get(record["user_url"])
                                                            about_ele = WebDriverWait(user_driver, 120).until(lambda driver: driver.find_element_by_xpath("//div[@class='about']"))
                                                            record["user_intro"] = about_ele.text
                                                        except:
                                                            pass
                                                        finally:
                                                            if user_driver is not None:
                                                                user_driver.quit()

                                                try:
                                                    close_btn = self.driver.find_element_by_xpath("//div[contains(@class, 'ReactModal__Content')]/div/div[1]/a/*[name()='svg']")
                                                    close_btn.click()
                                                    self.driver.implicitly_wait(2)
                                                    time.sleep(self.config["sleep_value"] / 2)
                                                except:
                                                    next_btn = self.driver.find_element_by_xpath("//div[contains(@class, 'ReactModal__Content')]/div/*[name()='svg']")
                                                    next_btn.click()
                                                    self.driver.implicitly_wait(2)
                                                    time.sleep(self.config["sleep_value"] / 2)

                                                print("----------------------")
                                                print(json.dumps(record, indent=4))

                                                file_exist = os.path.exists(output_csv_path)
                                                with open(output_csv_path, "a", encoding="utf-8", errors="ignore", newline="") as f:
                                                    fieldnames = ['user_name', 'user_url', 'user_intro', 'product_name', 'product_url', 'comment', 'product_brand', 'user_img', 'user_location', 'rating', 'img_url', 'video_url', 'video_or_photo', 'post_url']
                                                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                                                    if not file_exist:
                                                        writer.writeheader()
                                                    writer.writerow(record)
                                            
                                        except:
                                            print(traceback.print_exc())
                                            time.sleep(self.config["sleep_value"])
                                            continue
                                    
                                            
                                    if self.processed_count > self.config["limit_review_count"]:
                                        break
                                    
                                    self.scroll_event()
                            except:
                                print(traceback.print_exc())
                                continue
                            
                    except:
                        print(traceback.print_exc())
                        continue

            except:
                print(traceback.print_exc())
                continue
            finally:
                if self.driver is not None:
                    self.driver.quit()
                    self.driver = None
                

if __name__ == "__main__":
    
    influenster_crawler = InfluensterCrawler()
    influenster_crawler.start()
    
