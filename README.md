# guagualeEXP

A simple scraper that fetches prize information for Taiwan Lottery scratch games using the official JSON API and estimates each game's expected value after taxes.

## Requirements

- Python 3.11+
- `requests`

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

The script retrieves the list of currently sold games from `https://www.taiwanlottery.com` and downloads each game's prize structure via the JSON API. It then prints the expected value for every scratcher sorted from highest to lowest.

> **Note**
> The script retries failed requests automatically. If live scraping still fails, run with `--json data/sample_games.json` to see example output.
