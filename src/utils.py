import os
import re

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