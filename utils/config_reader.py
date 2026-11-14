import json
from pathlib import Path

import yaml


def load_selectors(file_path: Path, section: str) -> dict:
    """Return a selector block (e.g. 'login') from a YAML file."""
    with open(file_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if section not in data:
        raise KeyError(f"'{section}' section not found in {file_path}")
    return data[section]


def load_values(file_path: Path) -> dict:
    """Return test data (e.g. username/password) from a JSON file."""
    with open(file_path, encoding="utf-8") as f:
        return json.load(f)
