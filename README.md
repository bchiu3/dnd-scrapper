# dnd-scrapper
Scrapper for reading dnd spells and feats

Uses the wikidot dnd page for scraping

## Running the scrapper
You do need a dnd-spells.txt file, with tab-seperated lines that look like this:
`Wish	Conjuration	1 Action	Self	Instantaneous	V	9	http://dnd5e.wikidot.com/spell:wish`
(Check wikidot spell page)

`python3 main.py`
it will export into a json that you can use.