# guagualeEXP

A simple scraper that fetches prize information for Taiwan Lottery scratch games and estimates the expected value of each game after taxes.

## Requirements

- Python 3.11+
- `requests`
- `beautifulsoup4`

Install dependencies with:

```bash
pip install -r requirements.txt
```

## Usage

Run the scraper from the command line. You can attempt to fetch live data or load a local JSON file:

```bash
# fetch live data (may fail if the website is unreachable)
python scrape.py

# use bundled sample data
python scrape.py --json data/sample_games.json
```

The script will request the list of available scratch cards from the official Taiwan Lottery website, fetch the prize structure for each game, and print the expected value for every scratcher sorted from highest to lowest.

> **Note**
> The official website occasionally blocks automated requests, resulting in `HTTP 503` errors. If fetching live data fails, use the `--json` option with `data/sample_games.json` to see how results are presented.
