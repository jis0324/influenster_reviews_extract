# -*- coding: utf-8 -*-
import os
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

LOGGER.setLevel(logging.WARNING)
base_dir = os.path.dirname(os.path.abspath(__file__))
output_csv_path = base_dir + "/result.csv"


def set_driver():
    try:
        chrome_option = webdriver.ChromeOptions()
        chrome_option.add_argument('--no-sandbox')
        chrome_option.add_argument('--disable-dev-shm-usage')
        chrome_option.add_argument('--ignore-certificate-errors')
        chrome_option.add_argument("--disable-blink-features=AutomationControlled")
        chrome_option.add_argument('user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_3) AppleWebKit/537.36 (KHTML, like Gecko) ' \
            'Chrome/80.0.3987.132 Safari/537.36')
        # chrome_option.headless = True

        driver = webdriver.Chrome(options = chrome_option)
        return driver

    except:
        return None


class InfluensterCrawler:

    # init
    def __init__(self):
        # init web driver
        self.driver = None
        self.accepted_cookie_flag = False
        self.processed_count = 0

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
        try:
            search_url = "https://www.influenster.com/reviews/search?sort=prod_media"

            # create web driver
            self.driver = set_driver()
            
            if self.driver is None:
                print("Can Not Create Driver. Please Try Again.")
                return

            # get inventory url
            self.driver.get(search_url)

            
            while True:
                try:
                    elements = WebDriverWait(self.driver, 30).until(lambda driver: driver.find_elements_by_xpath("//div[contains(@class, 'results-wrapper')]/div[last()]/div/a[contains(@class,'grid-item')]"))
                    self.driver.implicitly_wait(3)

                    elements = elements[self.processed_count:]

                    for element in elements:
                        try:
                            self.processed_count += 1
                            record = dict()
                            if not self.accepted_cookie_flag:
                                try:
                                    accept_cookie_btn = self.driver.find_element_by_xpath("//button[@id='onetrust-accept-btn-handler']")
                                    if accept_cookie_btn:
                                        accept_cookie_btn.click()
                                        print("Accepted Cookie.")
                                        self.driver.implicitly_wait(3)
                                        self.accepted_cookie_flag = True
                                except:
                                    pass
                            
                            try:
                                element.click()
                            except:
                                continue
                            
                            user_name_ele = WebDriverWait(self.driver, 30).until(lambda driver: driver.find_element_by_xpath("//div[contains(@class, 'ReactModal__Content')]/div/div[2]/div/div[1]/a"))
                            self.driver.implicitly_wait(5)
                            
                            
                            try:
                                record["user_name"] = user_name_ele.text
                            except:
                                record["user_name"] = ""
                            
                            try:
                                record["user_url"] = user_name_ele.get_attribute("href")
                            except:
                                record["user_url"] = ""
                            
                            try:
                                record["product_name"] = self.driver.find_element_by_xpath("//div[contains(@class, 'ReactModal__Content')]/div/div[2]/div/div[@class='media-title']/a").text
                            except:
                                record["product_name"] = ""
                            
                            try:
                                record["product_url"] = self.driver.find_element_by_xpath("//div[contains(@class, 'ReactModal__Content')]/div/div[2]/div/div[@class='media-title']/a").get_attribute("href")
                            except:
                                record["product_url"] = ""
                            
                            try:
                                record["comment"] = self.driver.find_element_by_xpath("//div[contains(@class, 'ReactModal__Content')]/div/div[3]/div[2]/div[1]/div[2]").text
                            except:
                                record["comment"] = ""
                            
                            try:
                                record["product_brand"] = self.driver.find_element_by_xpath("//div[contains(@class, 'ReactModal__Content')]/div/div[3]/div[2]/div[2]/div/div/a[1]").get_attribute("href").rsplit("/", 1)[1]
                            except:
                                record["product_brand"] = ""
                            
                            try:
                                record["user_img"] = self.driver.find_element_by_xpath("//div[contains(@class, 'ReactModal__Content')]/div/div[2]/a//img").get_attribute("src")
                            except:
                                record["user_img"] = ""
                        
                            try:
                                record["user_location"] = self.driver.find_element_by_xpath("//div[contains(@class, 'ReactModal__Content')]/div/div[2]/div/div[last()]").text.split("-", 1)[0]
                                if "review" in record["user_location"]:
                                    record["user_location"] == ""
                            except:
                                record["user_location"] = ""
                            
                            try:
                                rating_class_list = ["gRUygt", "MVvhW", "bDvYHg", "iibyyi", "dQneJo", "cXTpuH", "NgMdV", "eegwjt", "NTulO", "fBLuLO", "eSuKgz", "gEfMYN"]

                                rating_class_vs_value = {
                                    "gRUygt": 1,
                                    "MVvhW": 0.6,
                                    "bDvYHg": 0.4,
                                    "iibyyi": 0.6,
                                    "dQneJo": 0.4,
                                    "cXTpuH": 0.6,
                                    "NgMdV": 0.6,
                                    "eegwjt": 0.1,
                                    "NTulO": 0.2,
                                    "fBLuLO": 0,
                                    "eSuKgz": 0.3,
                                    "gEfMYN": 0.4,

                                }
                                rating = 0
                                rating_elements = self.driver.find_elements_by_xpath("//div[contains(@class, 'ReactModal__Content')]/div/div[3]/div[2]/div[3]/div[1]/div")
                                if len(rating_elements):
                                    for item in rating_elements:
                                        classes = item.get_attribute("class")
                                        print("*******************", classes)
                                        for class_item in rating_class_list:
                                            if class_item in classes:
                                                if class_item in rating_class_vs_value:
                                                    rating += rating_class_vs_value[class_item]
                                                else:
                                                    rating += 1
                                                break

                                    record["rating"] = rating
                            except:
                                print(traceback.print_exc())
                                record["rating"] = ""
                            
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
                                close_btn = self.driver.find_element_by_xpath("//div[contains(@class, 'ReactModal__Content')]/div/div[1]/a/*[name()='svg']")
                                close_btn.click()
                                self.driver.implicitly_wait(2)
                            except:
                                pass

                            print("----------------------")
                            print(json.dumps(record, indent=4))

                            file_exist = os.path.exists(output_csv_path)
                            with open(output_csv_path, "a", encoding="utf-8", errors="ignore", newline="") as f:
                                fieldnames = ['user_name', 'user_url', 'product_name', 'product_url', 'comment', 'product_brand', 'user_img', 'user_location', 'rating', 'img_url', 'video_url', 'video_or_photo', 'post_url']
                                writer = csv.DictWriter(f, fieldnames=fieldnames)
                                if not file_exist:
                                    writer.writeheader()
                                writer.writerow(record)

                        except:
                            print(traceback.print_exc())
                            continue
                    
                    self.scroll_event()

                except:
                    break
        except:
            print(traceback.print_exc())
        finally:
            if self.driver is not None:
                self.driver.quit()
                self.driver = None
            

if __name__ == "__main__":
    # delete result csv file 
    file_exist = os.path.isfile(output_csv_path)
    if file_exist:
        os.remove(output_csv_path)

    influenster_crawler = InfluensterCrawler()
    influenster_crawler.start()
    
