import json
import time
from pathlib import Path

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from tqdm import tqdm

import defaults
from utils import satisfiesConstraints

def check_exists_by_class(driver, class_name):
    try:
        driver.find_element(By.CLASS_NAME, class_name)
    except NoSuchElementException:
        return False
    return True

TARGET_URL_END = "&collection=cow"
TARGET_URL = ["HOL/Page?handle=hein.cow/", "/HOL/Page?collection=cow&handle=hein.cow/"]
def get_correct_link_and_title(items):
    for item in items:
        url = item.get_attribute("href")
        print(url, item.text)
        if TARGET_URL[0] in url or TARGET_URL[1] in url:
            return url, item.text
    return None, None

TEXT_TYPE = "&type=text"
ORIGINAL_KEY = "Original Text"
MARC_RECORD = "MARC Record"

def constitution_scrape_links(
    country_name, 
    country_code, 
    max_year = defaults.MAX_YEAR, 
    all_files = False, 
    output_dir = "output",
    off_campus = False
    ):
   
    print("Scraping links for: ", country_name)

    s = Service(defaults.DRIVER)
    driver = webdriver.Chrome(service=s)

    URL = defaults.OFF_CAMPUS_URL if off_campus else defaults.BASE_URL
    country_url = URL + defaults.END_URL.format(code=country_code)

    print("At url: ", country_url)
    driver.get(country_url)
    time.sleep(1)

    if off_campus:
        try:
            element_present = EC.presence_of_element_located((By.XPATH, '//*[@id="top_hier"]/ul/a[2]'))
            WebDriverWait(driver, 60).until(element_present)
        except TimeoutException:
            print("Timed out waiting for page to load!")
    
    constitutionSection = driver.find_element("xpath", '//*[@id="top_hier"]/ul/a[2]')
    constitutionSection.click()

    time.sleep(1)

    html_list = driver.find_element(By.CLASS_NAME, "list_hier")

    items = [list_item for list_item in html_list.find_elements(By.TAG_NAME, "li") \
            if list_item.text != "" and satisfiesConstraints(list_item.text.strip(), max_year, all_files)]
    
    print("Documents to retrive versions: ", len(items))

    terminal_docs = []
    DocumentsDict = {
        "country": {
            "name": country_name,
            "code": country_code, 
            "url": country_url,
            "max_year" : int(max_year),
            "all_files": str(all_files)
            },
        "documents": {}
        }

    for item in tqdm(items, total=len(items), desc="Processing document links..."):
        doc_title = item.text.strip()
        terminal_docs.append(doc_title)

        DocumentsDict["documents"][doc_title] = []
        item.find_element(By.CLASS_NAME, "dt_link").click()
        time.sleep(1)
        list_heir = item.find_element(By.CLASS_NAME, "list_hier")
        li_items = [it for it in list_heir.find_elements(By.TAG_NAME, "li")]

        for li_item in li_items:
            if li_item.text != "" and ORIGINAL_KEY in li_item.text:
                terminal_docs.append("\tOriginal Text: ")
                slide_link = li_item.find_element(By.CLASS_NAME, "slide_links")
                slide_link.click()
                time.sleep(1)
                nested_list = li_item.find_element(By.CLASS_NAME, "list_hier")
                nested_li_items = [it for it in nested_list.find_elements(By.TAG_NAME, "li") if MARC_RECORD not in it.text]
                for nested_li_item in nested_li_items:
                    a_items = nested_li_item.find_elements(By.TAG_NAME, "a")
            
                    if len(a_items) > 0:
                        item_url, item_title = get_correct_link_and_title(a_items)
                        print(item_url, item_title)
                        if item_url and item_title:
                            version = {item_title : item_url}
                            if version not in DocumentsDict["documents"][doc_title]:
                                terminal_docs.append(f"\t- {nested_li_item.text}")
                                DocumentsDict["documents"][doc_title].append(version)
            elif li_item.text != "" and not check_exists_by_class(li_item, "slide_links"):
                a_items = li_item.find_elements(By.TAG_NAME, "a")
                if len(a_items) > 0:
                    url, name = get_correct_link_and_title(a_items)
                    print(url, name)
                    
                    if url and name:
                        version = {name : url}
                        if version not in DocumentsDict["documents"][doc_title]:
                            terminal_docs.append(f"\t- {name}")
                            DocumentsDict["documents"][doc_title].append(version)

    for doc in terminal_docs:
        print(doc)
    print("Saving to json file...")

    # save to json file
    json_file = Path(output_dir, country_name + ".json")
    with open(json_file, "w") as f:
        json.dump(DocumentsDict, f, indent=4)
    
    print("Finished getting links for ", country_name, " at ", json_file)
    time.sleep(1)
    driver.quit()

# TODO: fix this
def extract_document_from_url(url, outfile):

    s = Service('/Applications/chromedriver')
    driver = webdriver.Chrome(service=s)
    driver.get(url)

    elements = driver.find_elements(By.CLASS_NAME, "page_line")
    all_links = []
    for element in elements:
        a_elem = element.find_elements(By.TAG_NAME, "a")
        if len(a_elem) > 0:
            all_links.append(a_elem[0].get_attribute("href"))
    
    unique_text_links = list(set(all_links))
    # sort the links
    unique_text_links = sorted(unique_text_links, key=lambda x: int(x.split("&id=")[-1].split("&")[0]))

    for link in tqdm(unique_text_links, total=len(unique_text_links), desc="Processing document pages..."):
        driver.get(link + TEXT_TYPE)
        pageTextBox = driver.find_element(By.XPATH, "//*[@id=\"PageTextBox\"]/pre")
        mode = "a" if Path(outfile).is_file() else "w"
        with open(outfile, mode) as f:
            f.write(pageTextBox.text + "\n")

    # print("Saved to file: ", outfile)
