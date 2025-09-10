import json
import os
from typing import Optional

def get_ism_description(ism_key: str, data_path: Optional[str] = None) -> Optional[str]:
    """
    Returns the description for a given ISM control key from data.json.
    Args:
        ism_key: The ISM control key to look up (e.g., 'ISM-001').
        data_path: Optional path to data.json. Defaults to ../data/data.json relative to this file.
    Returns:
        The description string if found, else None.
    """
    if data_path is None:
        data_path = os.path.join(os.path.dirname(__file__), "../data/data.json")
    with open(data_path, "r") as f:
        data = json.load(f)
    for ism in data:
        key = list(ism.keys())[0]
        if key == ism_key:
            return ism[key].get("Description")
    return None

# Example usage:
# desc = get_ism_description("ISM-001")
# print(desc)
