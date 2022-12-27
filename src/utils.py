import os
import re
from os import linesep
from pathlib import Path

import defaults

def hasKeyword(title):
    title = title.lower()
    for keyword in defaults.KEYWORDS:
        if keyword in title:
            return True
    return False

def extractYear(title):
    title = title.lower()
    year = re.findall(r'\d{4}', title)
    if len(year) > 0:
        year_val = int(year[0])
        return year_val
    return None

def satisfiesYear(year, max_year):
    if year is None:
        return False
    return year <= max_year

def satisfiesConstraints(title, max_year, all_files):
    year = extractYear(title)
    if all_files:
        return satisfiesYear(year, max_year)
    return satisfiesYear(year, max_year) and hasKeyword(title)

def create_file_string(title):
    clean = title.replace(' ', '_')
    clean = ''.join(e for e in clean if e.isalnum() or e == '_')
    clean = clean.replace('__', '_')
    return clean

def log_to_file(message, log_file_path, filename = "out_log.txt"):
    log_file = os.path.join(log_file_path, filename)
    mode = 'w' if not os.path.exists(log_file) else 'a'
    with open(log_file, mode) as f:
        f.write(message + '\n')

def sort_links(all_links):
    unique_text_links = list(set(all_links))
    unique_text_links = sorted(unique_text_links, key=lambda x: int(x.split("&id=")[-1].split("&")[0]))
    return unique_text_links

def get_next_link(id_num, all_links):
    """
    Remove all links that have an &id= that is less than or equal to id_num
    """
    all_links = [link for link in all_links if int(link.split("&id=")[-1].split("&")[0]) > id_num]
    if all_links[0]:
        return all_links[0], int(all_links[0].split("&id=")[-1].split("&")[0])
    return None, None

def dedent(message):
    return linesep.join(line.lstrip() for line in message.splitlines())

def generate_header(country, title, date, version, url, authors = "names"):
    header = """<?xml version="1.0" encoding="UTF-8"?>
            <author> {authors} </author>
            <country> {country} </country>
            <title> {title} </title>
            <date> {date} </date>
            <version> {version} </version>
            <source> {url} </source>
            """.format(
                authors = authors, 
                country = country, 
                title = title, 
                date = date, 
                version = version, 
                url = url)
    return dedent(header)

def add_to_file(outfile, message):
    mode = "a" if Path(outfile).is_file() else "w"
    with open(outfile, mode) as f:
        f.write(message + "\n")