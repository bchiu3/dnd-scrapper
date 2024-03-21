from dataclasses import dataclass
import json
from utils import feets_to_units


@dataclass
class Feats:
    name: str = ""
    description: str = ""
    prerequisite: str = ""
    url: str = ""

    has_prerequisite: bool = False

    def __post_init__(self):
        self.description = feets_to_units(self.description)

    def to_json(self) -> str:
        """
        Converts the object to a JSON string representation.

        Parameters:
            self: The object being converted to JSON.
        Returns:
            str: A string representing the object in JSON format.
        """
        return json.dumps(self.__dict__, default=lambda o: o.toJSON(), ensure_ascii=False)
