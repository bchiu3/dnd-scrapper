import re


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
