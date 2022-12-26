import json
import os
from pathlib import Path

import click
import pandas as pd
from tqdm import tqdm

import defaults
from hein_scraper import constitution_scrape_links, extract_document_from_url
from utils import create_file_string, log_to_file

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
    '-o',
    is_flag=True,
    default=False,
    help='Use off campus url'
    )
def links(country_code, map_file, out_dir, max_year, all_files, off_campus):
    """Scrape a country's constitution document inks from HeinOnline"""
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
def text(country_json, out_dir):
    """Scrape a country's constitution document text from HeinOnline"""
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
    for document in documents:
        subfolder_name = create_file_string(document)
        subfolder_path = os.path.join(out_dir, subfolder_name)
        Path(subfolder_path).mkdir(parents=True, exist_ok=True)
        versions = country_dict['documents'][document]
        # print("Document: ", document.strip())

        log_to_file("Document: " + document.strip(), out_dir)
        for version in tqdm(versions, total=len(versions), desc=f"- Processing versions..."):
            version_title = list(version.keys())[0]
            version_link = version[version_title]
            version_name = create_file_string(version_title) + '.txt'
            version_path = os.path.join(subfolder_path, version_name)
            extract_document_from_url(version_link, version_path)
            log_to_file("Finished extracting document(s) from url: " + version_link, out_dir)
        
        # process each version is a different thread
        # with concurrent.futures.ThreadPoolExecutor() as executor:
        #     executor.map(extract_document_from_url, versions, version_paths)





if __name__ == "__main__":
    cli()
