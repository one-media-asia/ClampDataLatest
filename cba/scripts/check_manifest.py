#!/usr/bin/env python3
"""Simple manifest safety check that can be run without pytest.
Exits with code 0 on success, non-zero on failure and prints a helpful message.
"""
import json
import sys
from pathlib import Path


def main():
    repo_root = Path(__file__).resolve().parents[1]
    manifest_path = repo_root / 'static' / 'manifest.json'
    if not manifest_path.exists():
        print(f"ERROR: manifest.json not found at {manifest_path}")
        return 2
    try:
        data = json.loads(manifest_path.read_text(encoding='utf-8'))
    except Exception as e:
        print(f"ERROR: manifest.json is not valid JSON: {e}")
        return 3

    # Basic checks
    if not data.get('name'):
        print('ERROR: "name" is missing or empty in manifest.json')
        return 4
    if not data.get('short_name'):
        print('ERROR: "short_name" is missing or empty in manifest.json')
        return 5
    icons = data.get('icons')
    if not isinstance(icons, list) or len(icons) == 0:
        print('ERROR: "icons" must be a non-empty list in manifest.json')
        return 6
    first = icons[0]
    if not first.get('src') or not first.get('sizes') or not first.get('type'):
        print('ERROR: first icon must have "src", "sizes", and "type"')
        return 7

    print('manifest.json looks good')
    return 0


if __name__ == '__main__':
    sys.exit(main())
