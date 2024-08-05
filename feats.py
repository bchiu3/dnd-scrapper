from dataclasses import InitVar, dataclass
import json
from urllib.parse import urljoin

from bs4 import BeautifulSoup, ResultSet
import requests
from utils import BASE_URL, feets_to_units, sanitize_strings

PREREQ_TEXT = "prerequisite"


@dataclass
class Feats:
    feat: InitVar[ResultSet | None] = None

    name: str = ""
    description: str = ""
    prerequisite: str = ""
    url: str = ""

    has_prerequisite: bool = False

    def __post_init__(self, feat: ResultSet = None):
        if feat is None:
            return
        self.name = feat.text
        self.url = urljoin(BASE_URL, feat.get("href"))
        self.search_feats()

    def to_json_str(self) -> str:
        """
        Converts the object to a JSON string representation.

        Parameters:
            self: The object being converted to JSON.
        Returns:
            str: A string representing the object in JSON format.
        """
        return json.dumps(self.__dict__, default=lambda o: o.toJSON(), ensure_ascii=False)

    def search_feats(self) -> None:
        """
        Perform a search for features based on the provided URL and name.

        Parameters:
            self: The object being searched.

        Returns:
            Returns an instance of Feats if features are found, otherwise returns None.
        """
        response = requests.get(self.url)
        if response.status_code != 200:
            return None
        soup = BeautifulSoup(response.text, 'html.parser')
        paragraphs = soup.find(id="page-content")
        link_paragraphs = paragraphs.find_all('a')
        for link in link_paragraphs:
            link.replace_with(link.text)

        paragraphs = list(filter(lambda x: x.text.strip()
                                 != "", paragraphs.children))[1:]
        prereq = ""
        has_prereq = False
        if PREREQ_TEXT.lower() in paragraphs[0].text.lower():
            split_at = paragraphs[0].text.find(" ")
            prereq = paragraphs[0].text[split_at+1:]
            has_prereq = True
            paragraphs = paragraphs[1:]

        paragraphs = sanitize_strings("".join(map(str, paragraphs)))
        self.description, self.prerequisite, self.has_prerequisite = (
            paragraphs, prereq, has_prereq)
        self.description = feets_to_units(self.description)
