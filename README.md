# Hein Online Consitution Scraper

This is a scraper for the Hein Online database of US Constitutions. It is a work in progress.

## Usage

Python 3.9 is preferred. Install the requirements with `pip install -r requirements.txt`. 

### Getting relevant document links:

        python src/scrape.py links --country_code=86

Where the value for `--country_code` is the country code for the country you want to scrape. The country codes are listed in `country_codes.json`.

### Getting the text:

        python src/scrape.py text --country_json=output/Chile.json

Where the value for `--country_json` is the path to the JSON file containing the links to the constitutions.

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details.