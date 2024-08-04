#from dataclasses import InitVar, dataclass, field
from enum import Enum
import requests
from bs4 import BeautifulSoup
from markdownify import markdownify

class Type(Enum):
    Weapon = 0
    Armor = 1
    Ring  = 2
    Wondrous = 3
    Potion = 4
    Scroll = 5
    Staff = 6
    Wand = 7
    Rod = 8

    def toJSON(self):
        return self.name

class Source(Enum):
    AI = "Acquisitions Incorporated"
    BGDA = "Baldur's Gate: Descent into Avernus"
    BOMT = "The Book of Many Things"
    BPGOG = "Bigby Presents: Glory of the Giants"
    CM = "Candlekeep Mysteries"
    COS = "Curse of Strahd"
    CRCN = "Critical Role: Call of the Netherdeep"
    DC = "Divine Contention"
    DMG = "Dungeon Master's Guide"
    DSDQ = "Dragonlance: Shadow of the Dragon Queen"
    ERLW = "Eberron: Rising from the Last War"
    EGW = "Explorer's Guide to Wildemount"
    FTD = "Fizban's Treasury of Dragons"
    GGR = "Guildmaster's Guide to Ravnica"
    GOS = "Ghosts of Saltmarsh"
    HAT = "Dungeons and Dragons: Honor Among Thieves"
    IDRF = "Icewind Dale: Rime of the Frostmaiden"
    IMR = "Infernal Machine Rebuild"
    JRC = "Journeys through the Radiant Citadel"
    KGV = "Keys from the Golden Vault"
    LLK = "Lost Laboratory of Kwalish"
    LMP = "Lost Mine of Phandelver"
    MCV2 = "Monstrous Compendium Volume 2 - Dragonlance Creatures"
    MOT = "Mythic Odysseys of Theros"
    OOA = "Out of the Abyss"
    PBTSO = "Phandelver and Below: The Shattered Obelisk"
    PSAIM = "Planescape: Adventures in the Multiverse"
    QIS = "Quests from the Infinite Staircase"
    POA = "Princes of the Apocalypse"
    ROT = "The Rise of Tiamat"
    SAS = "Spelljammer: Adventures in Space"
    SCC = "Strixhaven: A Curriculum of Chaos"
    SDW = "Sleeping Dragon's Wake"
    SKT = "Storm King's Thunder"
    TCE = "Tasha's Cauldron of Everything"
    TOA = "Tomb of Annihilation"
    TOD = "Tyranny of Dragons"
    TYP = "Tales from the Yawning Portal"
    VRGR = "Van Richten's Guide to Ravenloft"
    VEOR = "Vecna: Eve of Ruin"
    VGM = "Volo's Guide to Monsters"
    WDH = "Waterdeep: Dragon Heist"
    WDMM = "Waterdeep: Dungeon of the Mad Mage"
    WGTE = "Wayfarer's Guide to Eberron"
    WGE = "Wayfarer's Guide to Eberron"
    WBW = "The Wild Beyond the Witchlight"
    XGE = "Xanathar's Guide to Everything"
    U = 'Unknown'

    def toJSON(self):
        return self.name

class Rarity(Enum):
    Common = 0
    Uncommon = 1
    Rare = 2
    VeryRare = 3
    Legendary = 4
    Artifact = 5
    Unique = 6
    Unknown = 7

    def toJSON(self):
        return self.name

class MagicItem:

    def __init__(self, item : dict[str,str]) -> None:
        self.name = item['Item Name']
        self.rarity = Rarity[item['category'].replace(' ', '').replace('???', 'Unknown')]
        self.type = Type[item['Type'].replace(' Item', '')]
        self.attuned = (item['Type'] == 'Attuned')
        self.url = 'http://dnd5e.wikidot.com' + item['URL']
        try:
            self.source = Source[item['Source'].replace(':', '').upper()]
        except Exception as e:
            print(f'Could not set the source for {self.name} using the following URL: {self.url}')
            print(e)
            self.source = Source.U
        self.text = item.get('text', self.set_item_text()) 

    def set_item_text(self) -> str:
        item_page = requests.get(self.url)
        if item_page.status_code != 200:
            raise LookupError(f'Could not find {self.name} using this URL: {self.url}')
        element_html = str(BeautifulSoup(item_page.content, 'html.parser').find(id = 'page-content'))
        return markdownify(element_html, strip = ['scripts', 'page-tags'], autolinks = False)

    def to_json(self) -> dict[str, str]:
        return {
            "name"      : self.name,
            "rarity"    : self.rarity.toJSON(),
            "type"      : self.type.toJSON(),
            "source"    : self.source.toJSON(),
            "attuned"   : self.attuned,
            "text"      : self.text,
            "url"       : self.url
        }
        