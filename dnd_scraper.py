# coding=utf8
from pprint import pprint
from urllib.parse import urljoin
from bs4 import BeautifulSoup, ResultSet
import requests
from feats import Feats
from spell import Spell
from magic_item import MagicItem
import json

import time
from tqdm import tqdm

from utils import BASE_URL

INTERVAL = 2


class DNDScraper:
    def __init__(self, type_grab: (str | None) = None):
        if type_grab == "feats":
            self.url = urljoin(BASE_URL, "/#toc70")
            self.file = open("exported_feats.json", "w", encoding='utf-8')
            self.list_info = get_feats_urls(self.url)
            self.class_parse = Feats
        elif type_grab == 'magic_item':
            self.url = urljoin(BASE_URL, "/wondrous-items")
            self.file = open("exported_magic_items.json",
                             "w", encoding='utf-8')
            self.list_info = self.get_wiki_table()
            self.class_parse = MagicItem

            with open('./magic_items.json', 'w') as outputFile:
                json.dump(self.list_info, outputFile)
        else:
            # default is spells
            self.url = urljoin(BASE_URL, "/spells")
            self.file = open("exported_spells.json", "w", encoding='utf-8')
            self.list_info = self.get_wiki_table()
            self.class_parse = Spell

        self.file.write("[\n")
        progress_bar = tqdm(total=len(self.list_info))
        for i, info in enumerate(self.list_info):
            if i != 0:
                self.file.write(", ")
            files = self.class_parse(info).to_json_str()
            self.file.write(files + "\n")
            time.sleep(INTERVAL)
            progress_bar.update(1)
        self.file.write("]")

    def close_file(self):
        if hasattr(self, 'file') and self.file:
            self.file.close()

    def print_spells(self):
        for i in self.spells:
            pprint(self.spells[i])

    def get_wiki_table(self) -> list[dict[str, str]]:
        '''
        Extracts all the tables from the main page, given by `self.url`
        '''
        main_page = requests.get(self.url)
        if main_page.status_code != 200:
            raise LookupError(f'Could not connect to {self.url}')

        soup = BeautifulSoup(main_page.content, 'html.parser')

        table_categories = soup.find('ul', class_='yui-nav').find_all('li')
        categories_names = []

        for category in table_categories:
            categories_names.append(category.find('a').text)

        tables = soup.find_all('div', class_='list-pages-box')
        table_list = []
        for i in range(len(tables)):
            table = tables[i]
            category = categories_names[i]
            table_headers = [th.text for th in table.find_all('th')]
            table_rows = table.find_all('tr')

            for row in table_rows[1:]:
                row_dict = {}
                cells = row.find_all('td')
                for header, cell in zip(table_headers, cells):
                    row_dict[header] = cell.text

                row_dict['URL'] = row.find('a', href=True)['href']
                row_dict['category'] = category
                table_list.append(row_dict)

        return table_list


def get_feats_urls(url: str) -> list[ResultSet]:
    """
    A function that takes a URL as input and returns a list of URLs for features.

    Args:
        url: a string representing the URL

    Returns:
        a list of BS4 elements representing the URLs for features
    """
    list_feats = []
    response = requests.get(url)
    if response.status_code != 200:
        return list_feats

    soup = BeautifulSoup(response.text, 'html.parser')
    # this is just the title of the table, not the entire table
    list_links = soup.find(id="toc70").parent.parent.parent.find_all("a")
    return list_links
