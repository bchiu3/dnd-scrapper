from dataclasses import InitVar, dataclass, field
from enum import Enum
import json
import re

from utils import feets_to_units


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


@dataclass
class Spell:
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

    line: InitVar[str | None] = None

    def __post_init__(self, line: str = None):
        if line is None:
            return

        name, school, cast_time, spell_range, duration, components, level = line.split("\t")

        spell_name = Spell._parse_spell_name(name)
        self.name = spell_name

        school = school.strip().lower()
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

        self.url = re.sub(r'\(.+?\)', '', self.name.replace("'", '').lower())
        self.url = re.sub(r'\W', '-', self.url)
        self.url = f'http://dnd5e.wikidot.com/spell:{self.url}'

    def to_json(self) -> str:
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
            - cast_time_unsanitized (str): The unsanitized cast time string.

        Returns:
            - tuple: A tuple containing two elements:
                - int: The sanitized cast time value.
                - bool: A flag indicating ritual casting
        """
        has_ritual = cast_time_unsanitized.rfind(" ")
        is_ritual = False
        if has_ritual != -1 and cast_time_unsanitized[has_ritual+1:] == "R":
            is_ritual = True
            cast_time_unsanitized = cast_time_unsanitized[:has_ritual]
        cast_time_unsanitized = cast_time_unsanitized.strip().lower().split(" ")

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

        Args:
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

        Args:
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

        Args:
            level_unsanitized (str): The unsanitized string representing the level.

        Returns:
            int: The parsed level as an integer.
        """
        level = level_unsanitized.strip().lower()
        return int(level)
