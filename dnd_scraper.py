# coding=utf8
from datetime import time
import datetime
from pprint import pprint
from bs4 import BeautifulSoup, PageElement
import requests
from spell import ClassTypes, ComponentTypes, Spell
from redis import Redis
from rq import Queue
import json
import time

DND_SPELL_TAB_LIST = "dnd-spells.txt"
UPCAST_STARTING_TEXT = "At Higher Levels"
SPELL_CLASS_STARTING_TEXT = "Spell Lists"

class DNDScraper:
    def __init__(self):
        self.url = "http://dnd5e.wikidot.com/spells"
        self.spells = {}
        self.redis_queue = Queue(connection=Redis())
        
        self.file = open("exported_spells.json", "w", encoding='utf-8')
            
        self.file.write("[")
        
        with open(DND_SPELL_TAB_LIST) as file:
            for line in file:
                spell = Spell(line = line.strip())
                
                self.spells[spell.name] = spell

        self.time = datetime.datetime.now()
        for i, spell in enumerate(self.spells.values()):
            # self.redis_queue.enqueue_at(self.time, search_spells, spell)
            # self.time += datetime.timedelta(seconds=3)
            if i != 0:
                self.file.write(", ")
            search_spells(spell)
            self.file.write(spell.to_json() + "\n")
            time.sleep(5)
        self.file.write("]")
    
    def close_file(self):
        if self.file:
            self.file.close()
    
    def print_spells(self):
        for i in self.spells:
            pprint(self.spells[i])

def search_spells(spell: Spell):
    """
    Perform a spell search using the given `Spell` object.
    
    Args:
        spell (Spell): The `Spell` object containing the information of the spell to search.
        
    Returns:
        None
    """
    response = requests.get(spell.url)
    if response.status_code != 200:
        return
    
    soup = BeautifulSoup(response.text, 'html.parser')
    paragraphs = soup.find(id="page-content")
    link_paragraphs = paragraphs.find_all('a')
    for link in link_paragraphs:
        link.replace_with(link.text)
    
    paragraphs = list(paragraphs.children)
    
    _set_components(spell, paragraphs)
    
    _set_description_upcast_classes(spell, paragraphs)
    
    

def _set_components(spell: Spell, paragraphs: [PageElement]):
    """
    Set the components of a spell based on the provided spell object and paragraphs.

    Parameters:
        spell (Spell): The spell object for which to set the components.
        paragraphs (list): A list of paragraphs containing the spell details.

    Returns:
        None
    """
    if ComponentTypes.Material in spell.components:
        spell_types = paragraphs[7].text
        components_start = spell_types.find("Components: ")
        components_end = spell_types.find("\n", components_start + 1)
        components = spell_types[components_start + 1:components_end]
        components = components[components.rfind("("):].strip("()")
        spell.component_material = sanitize_strings(components)

def _set_description_upcast_classes(spell: Spell, paragraphs: [PageElement]):
    """
    Set the description of a given spell and upcast it if necessary.
    
    Parameters:
        spell (Spell): The spell object to set the description and upcast.
        paragraphs (list): A list of paragraphs containing the description and upcast information.
        
    Returns:
        None
    """
    
    end_description = (
        UPCAST_STARTING_TEXT, 
        SPELL_CLASS_STARTING_TEXT
    )
    for i in range(9, len(paragraphs)):
        flag = False
        for end_str in end_description:
            if end_str in str(paragraphs[i]):
                flag = True
                break
        if flag:
            break
    
    description = paragraphs[9:i]
    spell.description = "".join([sanitize_strings(str(p)) for p in description])
    
    _set_upcast(spell, paragraphs[i:])
    
    _set_classes(spell, paragraphs[i:])

def _set_upcast(spell: Spell, paragraphs: [PageElement]):
    """
    Set up the upcast property of a given spell if it has upcast ability.

    Args:
        spell (Spell): The spell object to set upcast for.
        paragraphs (list): The list of paragraphs STARTING AT THE UPCAST DESCRIPTION

    Returns:
        None
    """
    if paragraphs[0].text.strip().startswith(UPCAST_STARTING_TEXT):
        upcast = paragraphs[0].text.strip(UPCAST_STARTING_TEXT).strip().lstrip(".").lstrip(":")
        spell.upcast = upcast
        spell.has_upcast = True

def _set_classes(spell: Spell, paragraphs: [PageElement]):
    """
    Set the classes of a given spell based on the paragraphs provided.
    
    This function iterates over each paragraph in the provided list of paragraphs. If a paragraph's text starts with
    the specified starting text for spell classes, it extracts the class names from the paragraph's text and adds them
    to the spell's classes attribute. The class names are expected to be comma-separated and any optional text is
    removed before adding the class names to the spell's classes attribute.

    Args:
        spell (Spell): A Spell object representing the spell to set the classes for.
        paragraphs (list): A list of PageElement objects representing the paragraphs to search for class information.

    Returns:
        None
    """
    for paragraph in paragraphs:
        if paragraph.text.startswith(SPELL_CLASS_STARTING_TEXT):
            classes = paragraph.text.replace(SPELL_CLASS_STARTING_TEXT, "").strip().lstrip(".").lstrip(":")
            for spell_class in classes.split(","):
                spell_class = spell_class.strip()
                has_space = spell_class.find(" ")
                if has_space != -1:
                    spell_class = spell_class[:spell_class.find(" ")]
                try:
                    spell.classes.append(ClassTypes[spell_class.strip().title()])
                except KeyError:
                    print(f"Unknown class for spell: {spell}\n\nwith class: {spell_class}")

def sanitize_strings(paragraph: str):
    """
    Generate a sanitized version of the input paragraph by replacing newline characters with spaces,
    smart apostrophes with regular apostrophes, and en dashes with hyphens.

    Args:
        paragraph (str): The input paragraph to be sanitized.
    
    Returns: 
        The sanitized version of the input paragraph.
    """
    return paragraph.replace("\n", " ").replace("\u2019", "'").replace("\u2013", "-")