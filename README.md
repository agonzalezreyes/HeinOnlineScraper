# Hein Online Constitution Scraper

This is a scraper for the Hein Online database of constitutions. It is a work in progress. 

This is for research purposes **only**.

## Usage

Python 3.9 is preferred; Google Chrome Driver is a requirement. 

Install the requirements with `pip install -r requirements.txt`. 

### Getting relevant document links:

        python src/scrape.py links --country_code=86

Where the value for `--country_code` is the country code for the country you want to scrape. The country codes are listed in `country_codes.csv`. This will create a JSON file in the `output` directory with the links to the constitutions of that country. 

Pass the `--off_campus` flag when running the script if you are off campus to login to HeinOnline.

*Note:* The file in `country_codes.csv` are shows as an example.

### Getting the text:

        python src/scrape.py text --country_json=output/Chile.json

Where the value for `--country_json` is the path to the JSON file containing the links to the constitutions. 

Pass the `--off_campus` flag when running the script if you are off campus to login to HeinOnline.

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details.