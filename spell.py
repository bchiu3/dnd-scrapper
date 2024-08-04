from dataclasses import InitVar, dataclass, field
from enum import Enum
import json
import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup, PageElement
import requests

from utils import BASE_URL, feets_to_units, sanitize_strings


class CastType(Enum):
    Action = 0
    Bonus = 1
    Reaction = 2
    Time = 3
    Unknown = 4

    def toJSON(self):
        return self.name


class SpellRangeType(Enum):
    Self = 0
    Touch = 1
    Sight = 2
    Special = 3
    Unlimited = 4
    Units = 5
    Unknown = 6

    def toJSON(self):
        return self.name


class ComponentTypes(Enum):
    Verbal = 0
    Somatic = 1
    Material = 2

    def toJSON(self):
        return self.name


class ClassTypes(Enum):
    Artificer = "artificer"
    Bard = "bard"
    Cleric = "cleric"
    Druid = "druid"
    Paladin = "paladin"
    Ranger = "ranger"
    Sorcerer = "sorcerer"
    Warlock = "warlock"
    Wizard = "wizard"

    def toJSON(self):
        return self.name


LEVELS_MAP = {
    "cantrip": 0,
    "1st level": 1,
    "2nd level": 2,
    "3rd level": 3,
    "4th level": 4,
    "5th level": 5,
    "6th level": 6,
    "7th level": 7,
    "8th level": 8,
    "9th level": 9
}
UPCAST_STARTING_TEXT = "At Higher Levels"
SPELL_CLASS_STARTING_TEXT = "Spell Lists"


@dataclass
class Spell:
    spell: InitVar[dict | None] = None

    name: str = ""
    description: str = ""
    level: int = -1

    school: str = ""

    duration: str = ""
    is_concentration: bool = False

    cast_type: CastType = CastType.Unknown
    cast_time: str = ""
    is_ritual: bool = False

    range_type: SpellRangeType = SpellRangeType.Unknown
    spell_range: str = ""

    has_upcast: bool = False
    upcast: str = ""

    components: list[ComponentTypes] = field(default_factory=list)
    component_material: str = ""
    classes: list[ClassTypes] = field(default_factory=list)

    url: str = ""

    def __post_init__(self, spell: dict = None):
        if spell is None:
            return

        # get all from dict like:
        # {
        # 'Spell Name': '',
        # 'School': '',
        # 'Casting Time': '',
        # 'Range': '',
        # 'Duration': ',
        # 'Components': '',
        # 'URL': '',
        # 'category': ''
        # }
        name = spell["Spell Name"]
        school = spell["School"]
        cast_time = spell["Casting Time"]
        spell_range = spell["Range"]
        duration = spell["Duration"]
        components = spell["Components"]
        level = spell["category"]
        url = spell["URL"]

        spell_name = Spell._parse_spell_name(name)
        self.name = spell_name

        school = school.strip().lower().split(" ")[0]
        self.school = school

        cast_type, cast_time_time, is_ritual = Spell._parse_cast_time(
            cast_time)
        self.cast_type, self.cast_time, self.is_ritual = cast_type, cast_time_time, is_ritual

        spell_range_type, spell_range_range = Spell._parse_spell_range(
            spell_range)
        self.range_type, self.spell_range = spell_range_type, spell_range_range

        duration, is_concentration = Spell._parse_duration(duration)
        self.duration, self.is_concentration = duration, is_concentration

        component_types = Spell._parse_components(components)
        self.components = component_types

        level = Spell._parse_level(level)
        self.level = level

        self.url = urljoin(BASE_URL, url)

        try:
            self.search_spell()
        except Exception as e:
            print(f'Could not find spell {spell.name}')
            print(e)

    def to_json_str(self) -> str:
        """
        Converts the object to a JSON string representation.

        Parameters:
            self: The object being converted to JSON.
        Returns:
            str: A string representing the object in JSON format.
        """
        return json.dumps(self.__dict__, default=lambda o: o.toJSON(), ensure_ascii=False)

    @staticmethod
    def _parse_spell_name(spell_name_unsanitized: str) -> str:
        """
        Sanitizes a spell name by removing any additional information after the last space and the opening parenthesis.

        Parameters:
            spell_name_unsanitized (str): The unsanitized spell name.

        Returns:
            str: The sanitized spell name.
        """
        spell_name = spell_name_unsanitized
        spell_name_split = spell_name_unsanitized.rfind(" ")
        if spell_name_split != -1 and len(spell_name) > spell_name_split + 2:
            if spell_name[spell_name_split + 1] == "(":
                spell_name = spell_name[:spell_name_split]
        return spell_name

    @staticmethod
    def _parse_cast_time(cast_time_unsanitized: str) -> tuple[CastType, int, bool]:
        """
        A static method that sanitizes a given cast time string and returns the sanitized value.

        Parameters:
            cast_time_unsanitized (str): The unsanitized cast time string.

        Returns:
            tuple: A tuple containing two elements:
                int: The sanitized cast time value.
                bool: A flag indicating ritual casting
        """
        has_ritual = cast_time_unsanitized.rfind(" ")
        is_ritual = False
        if has_ritual != -1 and cast_time_unsanitized[has_ritual+1:] == "R":
            is_ritual = True
            cast_time_unsanitized = cast_time_unsanitized[:has_ritual]
        cast_time_unsanitized = cast_time_unsanitized.strip().lower().split(" ")

        # reactions don't have 1 in front of them, but they should technically be 1 reaction
        if len(cast_time_unsanitized) < 2:
            cast_time_unsanitized = ["1"] + cast_time_unsanitized

        cast_time_time = 0
        match cast_time_unsanitized[1]:
            case "action":
                cast_type = CastType.Action
            case "bonus":
                cast_type = CastType.Bonus
            case "reaction":
                cast_type = CastType.Reaction
            case t if "hour" in t:
                cast_type = CastType.Time
                cast_time_time = int(cast_time_unsanitized[0]) * 60
            case t if "minute" in t:
                cast_type = CastType.Time
                cast_time_time = int(cast_time_unsanitized[0])
            case t:
                cast_type = CastType.Unknown
                print(f"could not parse cast time: {t}")

        # special case
        if len(cast_time_unsanitized) > 2 and cast_time_unsanitized[2] == "or":
            if "hour" in cast_time_unsanitized[4]:
                cast_time_time = int(cast_time_unsanitized[3]) * 60
            else:
                cast_time_time = int(cast_time_unsanitized[3])

        return (cast_type, cast_time_time, is_ritual)

    @staticmethod
    def _parse_spell_range(spell_range_unsanitized: str) -> tuple[SpellRangeType, str]:
        """
        Parses the spell range from a given unsanitized string and returns the corresponding SpellRangeType and spell range as a tuple.

        Parameters:
            spell_range_unsanitized (str): The unsanitized string representing the spell range.

        Returns:
            tuple: A tuple containing the SpellRangeType and the spell range.
        """
        spell_range_unsanitized = spell_range_unsanitized.strip().lower()
        match spell_range_unsanitized:
            case "touch":
                range_type = SpellRangeType.Touch
            case "sight":
                range_type = SpellRangeType.Sight
            case "special":
                range_type = SpellRangeType.Special
            case "unlimited":
                range_type = SpellRangeType.Unlimited
            case _ if "self" in spell_range_unsanitized:
                range_type = SpellRangeType.Self
            case _:
                range_type = SpellRangeType.Units

        spell_range = "0"
        self_spell_find = spell_range_unsanitized.find(" ")
        if range_type == SpellRangeType.Self and self_spell_find != -1:
            units = spell_range_unsanitized[self_spell_find + 1:]
            spell_range = units.strip("()")
            spell_range = feets_to_units(spell_range)
        elif range_type == SpellRangeType.Units:
            spell_range = feets_to_units(spell_range_unsanitized)

        return range_type, spell_range

    @staticmethod
    def _parse_duration(duration_unsanitized: str) -> tuple[str, bool]:
        """
        Parses the duration string and returns the sanitized duration and a boolean value indicating whether the duration is a concentration.

        Parameters:
            duration_unsanitized (str): The unsanitized duration string.

        Returns:
            tuple: A tuple containing the sanitized duration (str) and a boolean value indicating whether the duration is a concentration.
        """
        duration = duration_unsanitized.strip().lower().replace('"', "")
        is_concentration = False
        if "concentration" in duration:
            duration = duration[duration.find(" ") + 1:]
            is_concentration = True
        return duration, is_concentration

    @staticmethod
    def _parse_components(components_unsanitized: str) -> list[ComponentTypes]:
        """
        Parses the unsanitized components string and returns a list of ComponentTypes.

        Parameters:
            components_unsanitized (str): The unsanitized components string.

        Returns:
            list[ComponentTypes]: A list of ComponentTypes representing the parsed components.
        """
        components_unsanitized = components_unsanitized.strip().lower().replace(" ",
                                                                                "").replace('"', "")
        components = components_unsanitized.split(",")
        component_types = {"v": ComponentTypes.Verbal,
                           "s": ComponentTypes.Somatic, "m": ComponentTypes.Material}
        return [component_types[c] for c in components]

    @staticmethod
    def _parse_level(level_unsanitized: str) -> int:
        """
        Parse the level from a given unsanitized string.

        Parameters:
            level_unsanitized (str): The unsanitized string representing the level.

        Returns:
            int: The parsed level as an integer.
        """
        level = level_unsanitized.strip().lower()
        if level not in LEVELS_MAP:
            return -1
        return LEVELS_MAP[level]

    def search_spell(self):
        """
        Perform a spell search for the given `Spell` object.

        Parameters:
            self: The `Spell` object to search for.

        Returns:
            None
        """
        response = requests.get(self.url)
        if response.status_code != 200:
            raise LookupError(f'Could not find {
                              self.name} from the following URL: {self.url}')

        soup = BeautifulSoup(response.text, 'html.parser')
        paragraphs = soup.find(id="page-content")
        link_paragraphs = paragraphs.find_all('a')
        for link in link_paragraphs:
            link.replace_with(link.text)

        paragraphs = list(paragraphs.children)

        self._set_components(paragraphs)

        self._set_description_upcast_classes(paragraphs)

    def _set_components(self, paragraphs: list[PageElement]):
        """
        Set the components of a spell based on the provided spell object and paragraphs.

        Parameters:
            self: The `Spell` object to set the components for.
            paragraphs (list): A list of paragraphs containing the spell details.

        Returns:
            None
        """
        if ComponentTypes.Material in self.components:
            spell_types = paragraphs[7].text
            components_start = spell_types.find("Components: ")
            components_end = spell_types.find("\n", components_start + 1)
            components = spell_types[components_start + 1:components_end]
            components = components[components.rfind("("):].strip("()")
            self.component_material = sanitize_strings(components)

    def _set_description_upcast_classes(self, paragraphs: list[PageElement]):
        """
        Set the description of a given spell and upcast it if necessary.

        Parameters:
            self: The `Spell` object to set the description and upcast for.
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
        self.description = "".join([sanitize_strings(str(p))
                                    for p in description])

        self._set_upcast(paragraphs[i:])

        self._set_classes(paragraphs[i:])

    def _set_upcast(self, paragraphs: list[PageElement]):
        """
        Set up the upcast property of a given spell if it has upcast ability.

        Parameters:
            self: The `Spell` object to set the upcast for.
            paragraphs (list): The list of paragraphs STARTING AT THE UPCAST DESCRIPTION

        Returns:
            None
        """
        if paragraphs[0].text.strip().startswith(UPCAST_STARTING_TEXT):
            upcast = paragraphs[0].text.strip(
                UPCAST_STARTING_TEXT).strip().lstrip(".").lstrip(":")
            self.upcast = upcast
            self.has_upcast = True

    def _set_classes(self, paragraphs: list[PageElement]):
        """
        Set the classes of a given spell based on the paragraphs provided.

        This function iterates over each paragraph in the provided list of paragraphs. If a paragraph's text starts with
        the specified starting text for spell classes, it extracts the class names from the paragraph's text and adds them
        to the spell's classes attribute. The class names are expected to be comma-separated and any optional text is
        removed before adding the class names to the spell's classes attribute.

        Parameters:
            self: The `Spell` object to set the classes for.
            paragraphs (list): A list of PageElement objects representing the paragraphs to search for class information.

        Returns:
            None
        """
        for paragraph in paragraphs:
            if paragraph.text.startswith(SPELL_CLASS_STARTING_TEXT):
                classes = paragraph.text.replace(
                    SPELL_CLASS_STARTING_TEXT, "").strip().lstrip(".").lstrip(":")
                for spell_class in classes.split(","):
                    spell_class = spell_class.strip()
                    has_space = spell_class.find(" ")
                    if has_space != -1:
                        spell_class = spell_class[:spell_class.find(" ")]
                    try:
                        self.classes.append(
                            ClassTypes[spell_class.strip().title()])
                    except KeyError:
                        print(f"Unknown class for spell: {
                              self.name}\n\nwith class: {spell_class}")
