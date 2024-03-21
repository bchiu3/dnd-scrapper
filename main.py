from dnd_scraper import DNDScraper

if __name__ == "__main__":
    # dnd_spell = DNDScraper()
    # dnd_spell.close_file()
    dnd_feat = DNDScraper("feats")
    dnd_feat.close_file()