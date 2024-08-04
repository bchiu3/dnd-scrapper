import re

BASE_URL = "http://dnd5e.wikidot.com"

def feets_to_units(description: str) -> str:
    """
    Converts any instance of the unit feet to generic units.

    Args:
        description: The description to convert.

    Returns:
        str: The converted description.
    """
    description = description.replace("feet", "unit").replace("foot", "unit")
    if "mile" in description:
        try:
            unit = next(re.finditer(r'\d+', description))[0]
            range_unit = int(unit)
            description = str(range_unit * 5280) + " unit"
        except StopIteration:
            print(f"can't find number for spell range: {description}")
    return description


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