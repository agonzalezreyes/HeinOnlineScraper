import json
import os
from multiprocessing import Process
from pathlib import Path

import click
import pandas as pd
from tqdm import tqdm
from selenium.webdriver.chrome.service import Service
from selenium import webdriver

import defaults
from hein_scraper import constitution_scrape_links, extract_document_from_url
from utils import create_file_string, log_to_file, generate_header, extractYear

@click.group()
def cli():
    pass

@cli.command(help="Scrape a country\'s constitution links")
@click.option(
    '--country_code', 
    '-c', 
    default=86, 
    type=int, 
    help='Country to scrape'
    )
@click.option(
    '--map_file', 
    '-m', 
    default='country_codes.csv', 
    help='CSV map file between countries and country codes in HeinOnline'
    )
@click.option(
    '--out_dir', 
    '-o', 
    default='output', 
    type=click.Path(), 
    help='Output directory for scraped files'
    )
@click.option(
    '--all_files', 
    '-a', 
    is_flag=True, 
    default=False,
    help='All files to scrape under Constitution and Fundamental Laws section in HeinOnline'
    )
@click.option(
    '--max_year', 
    '-m', 
    default=defaults.MAX_YEAR,
    help='Max year to scrape'
    )
@click.option(
    '--off_campus',
    '-off',
    is_flag=True,
    default=False,
    help='Use off campus url'
    )
def links(country_code, map_file, out_dir, max_year, all_files, off_campus):
    """
        Scrape a country's constitution document inks from HeinOnline
    """
    # create output directory if it doesn't exist
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    # load country code map
    map_df = pd.read_csv(map_file)
    country = map_df[map_df['code'] == country_code]['country'].values[0]
    all_files = map_df[map_df['code'] == country_code]['all_files'].values[0]
    # scrape links
    constitution_scrape_links(
        country, 
        country_code, 
        max_year, 
        all_files, 
        out_dir,
        off_campus
        )

@cli.command(help="Scrape a country\'s constitution documents to txt files")
@click.option(
    '--country_json',
    '-c',
    type=click.Path(),
    required=True,
    help='JSON file containing country\'s constitution document links'
    )
@click.option(
    '--out_dir', 
    '-o', 
    default='output', 
    type=click.Path(), 
    help='Output directory for scraped files'
    )
@click.option(
    '--off_campus',
    '-off',
    is_flag=True,
    default=False,
    help='Use if located off campus'
    )
def text(country_json, out_dir, off_campus):
    """
        Scrape a country's constitution document text from HeinOnline
    """

    # create output directory if it doesn't exist
    Path(out_dir).mkdir(parents=True, exist_ok=True)

    # open json file of country with documents and links
    country_dict = {}
    with open(country_json, 'r') as f:
        country_dict = json.load(f)

    # create output directory if it doesn't exist
    out_dir = os.path.join(out_dir, country_dict['country']['name'])
    Path(out_dir).mkdir(parents=True, exist_ok=True)

    documents = country_dict['documents']

    driver = None
    if off_campus:
        # further, we are gonna create a single driver for all the documents 
        # so we dont have to sign-in multiple times when off campus network
        s = Service('/Applications/chromedriver')
        driver = webdriver.Chrome(service=s)

    for document in documents:
        # subfolder for document, to save all relevant versions
        subfolder_name = create_file_string(document)
        subfolder_path = os.path.join(out_dir, subfolder_name)
        Path(subfolder_path).mkdir(parents=True, exist_ok=True)

        versions = country_dict['documents'][document]
        print("Document: " + document.strip(), out_dir)

        processes = []
        for version in versions:
            version_title = list(version.keys())[0]
            version_link = version[version_title]
            version_name = create_file_string(version_title) + '.txt'
            version_path = os.path.join(subfolder_path, version_name)
            header = generate_header(
                country_dict['country']['name'], 
                document.strip(), 
                extractYear(document.strip()), 
                version_title, 
                version_link)
            with open(version_path, "w") as f:
                f.write(header + "\n\n")
            
            # Note: We only don't do multiprocess if we're off campus to manually sign-in to heinonline
            if off_campus and driver: # since we are off campus and need to manually sign-in, we can't multiprocess
                extract_document_from_url(driver, version_link, version_path, off_campus)
            else: # not off campus
                p = Process(target=extract_document_from_url, args=(None, version_link, version_path, off_campus))
                processes.append(p)
                p.start()
        
        if not off_campus:
            for p in processes:
                p.join()
        
        print("Finished extracting document(s) for " + document)


if __name__ == "__main__":
    cli()
