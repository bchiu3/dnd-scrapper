import argparse
from dnd_scraper import DNDScraper


parser = argparse.ArgumentParser(
                    prog='DnD Scraper',
                    description='Scrapes DnD content')

parser.add_argument('-f', '--feats', help='Scrape feats', action='store_true')
parser.add_argument('-m', '--magic_item', help='Scrape magic items', action='store_true')
parser.add_argument('-s', '--spells', help='Scrape spells', action='store_true')
args = parser.parse_args()

if __name__ == "__main__":
    if not any(vars(args).values()):
        print("Please select at least one option: -f, -m, -s")
        exit()

    if args.feats:
        print("Scraping feats...")
        dnd_scraper = DNDScraper("feats")
        dnd_scraper.close_file()
    if args.magic_item:
        print("Scraping magic items...")
        dnd_scraper = DNDScraper("magic_item")
        dnd_scraper.close_file()
    if args.spells:
        print("Scraping spells...")
        dnd_scraper = DNDScraper("spells")
        dnd_scraper.close_file()
    