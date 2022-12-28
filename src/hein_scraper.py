import json
import time
from pathlib import Path

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from tqdm import tqdm

import defaults
from utils import satisfiesConstraints, sort_links, get_next_link, add_to_file

def check_exists_by_class(driver, class_name):
    try:
        driver.find_element(By.CLASS_NAME, class_name)
    except NoSuchElementException:
        return False
    return True

TARGET_URL = ["HOL/Page?handle=hein.cow/", "/HOL/Page?collection=cow&handle=hein.cow/"]
def get_correct_link_and_title(items):
    for item in items:
        url = item.get_attribute("href")
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
            exit(1)
    
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
                        # print(item_url, item_title)
                        if item_url and item_title:
                            version = {item_title : item_url}
                            if version not in DocumentsDict["documents"][doc_title]:
                                terminal_docs.append(f"\t- {nested_li_item.text}")
                                DocumentsDict["documents"][doc_title].append(version)
            elif li_item.text != "" and not check_exists_by_class(li_item, "slide_links"):
                a_items = li_item.find_elements(By.TAG_NAME, "a")
                if len(a_items) > 0:
                    url, name = get_correct_link_and_title(a_items)
                    # print(url, name)
                    
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

def section_pages_url(driver, url, outfile, id_num, off_campus = False):
    """
    Get the text in a section page
    """
    print("Getting text from section page...")

    if not driver:
        print("Initializing driver...")
        s = Service('/Applications/chromedriver')
        driver = webdriver.Chrome(service=s)

    driver.get(url)
    time.sleep(1)

    if off_campus:
        try:
            element_present = EC.presence_of_element_located((By.XPATH, '//*[@id="table-of-contents"]'))
            WebDriverWait(driver, 60).until(element_present)
        except TimeoutException:
            print("Timed out waiting for page to load!")
            exit(1)
    
    elements = driver.find_elements(By.CLASS_NAME, "page_line")
    all_links = []
    for element in elements:
        a_elem = element.find_elements(By.TAG_NAME, "a")
        if len(a_elem) > 0:
            all_links.append(a_elem[0].get_attribute("href"))
    
    unique_text_links = sort_links(all_links)
    next_section_link, next_section_id = get_next_link(id_num, unique_text_links)
    link = url + TEXT_TYPE
    # open text section
    add_to_file(outfile, "<text>")
    if next_section_id and next_section_link:
        for id in range(id_num, next_section_id):
            # replace the &id= number in the url url
            link = link.replace(f"&id={id_num}", f"&id={id}")
            driver.get(link)
            # wait until page loads with textbox 
            textbox_present = EC.presence_of_element_located((By.XPATH, '//*[@id=\"PageTextBox\"]/pre'))
            WebDriverWait(driver, 1).until(textbox_present)
            # get text from page and write to file
            pageTextBox = driver.find_element(By.XPATH, "//*[@id=\"PageTextBox\"]/pre")
            add_to_file(outfile, pageTextBox.text)
    # close text section
    add_to_file(outfile, "</text>")

def all_pages_url(driver, url, outfile, off_campus = False):
    """
    Get the text in all pages from the url
    """
    if not driver:
        print("Initializing driver...")
        s = Service('/Applications/chromedriver')
        driver = webdriver.Chrome(service=s)
    
    driver.get(url + TEXT_TYPE)
    time.sleep(1)

    if off_campus:
        try:
            element_present = EC.presence_of_element_located((By.XPATH, '//*[@id="table-of-contents"]'))
            WebDriverWait(driver, 60).until(element_present)
        except TimeoutException:
            print("Timed out waiting for page to load!")
            exit(1)
    
    next_page_button = driver.find_element(By.XPATH, '//*[@id="page_right"]')

    javascript_string = next_page_button.get_attribute("onclick").strip().splitlines()[1]
    javascript_string = javascript_string.replace("\t", "")
    max_page = int(javascript_string.split("i_id == ")[1].split("))")[0])

    # open text section
    add_to_file(outfile, "<text>")
    curr_id = 1
    while curr_id <= max_page:
        pageTextBox = driver.find_element(By.XPATH, "//*[@id=\"PageTextBox\"]/pre")
        add_to_file(outfile, pageTextBox.text)
        curr_id += 1
        next_page_button.click()
        time.sleep(0.5)
        next_page_button = driver.find_element(By.XPATH, '//*[@id="page_right"]')
    # close text section
    add_to_file(outfile, "</text>")

def extract_document_from_url(driver, url, outfile, off_campus = False):
    # check if url contains &id=, which means it is a section to be scraped
    if "&id=" in url:
        id_num = int(url.split("&id=")[-1].split("&")[0])
        section_pages_url(driver, url, outfile, id_num, off_campus)
    else: # otherwise, all document needs to be scraped
        all_pages_url(driver, url, outfile, off_campus)
