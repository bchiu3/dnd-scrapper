# dnd-scrapper
Scrapper for reading dnd spells and feats

Uses the wikidot dnd page for scraping

## Running the scrapper
`python -r requirements.txt`
Add dependencies to run code.

`python3 main.py`
Won't do anything by itself, you have to use one of the options from:
`python3 main.py --help`

## Current Args
| Arg               | Description       |
| -------------     | -------------     |
| -f, --feats       | Scrape Feats      |
| -m, --magic_item  | Scrape Magic Items|
| -s, --spells      | Scrape Spells     |
