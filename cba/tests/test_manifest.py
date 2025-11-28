import json
from pathlib import Path


def test_manifest_exists_and_valid_json():
    repo_root = Path(__file__).resolve().parents[1]
    manifest_path = repo_root / 'static' / 'manifest.json'
    assert manifest_path.exists(), f"manifest.json not found at {manifest_path}"
    data = json.loads(manifest_path.read_text(encoding='utf-8'))

    # Basic required fields
    assert 'name' in data and isinstance(data['name'], str) and data['name'].strip(), 'Missing or invalid "name"'
    assert 'short_name' in data and isinstance(data['short_name'], str), 'Missing or invalid "short_name"'
    assert 'start_url' in data and isinstance(data['start_url'], str), 'Missing or invalid "start_url"'
    assert 'icons' in data and isinstance(data['icons'], list) and len(data['icons']) > 0, 'Missing or invalid "icons" list'

    # Check first icon has required keys
    first_icon = data['icons'][0]
    assert 'src' in first_icon and isinstance(first_icon['src'], str) and first_icon['src'].strip(), 'Icon missing "src"'
    assert 'sizes' in first_icon and isinstance(first_icon['sizes'], str), 'Icon missing "sizes"'
    assert 'type' in first_icon and isinstance(first_icon['type'], str), 'Icon missing "type"'

    # Optional: ensure theme_color is a hex string if present
    if 'theme_color' in data:
        tc = data['theme_color']
        assert isinstance(tc, str) and tc.startswith('#') and 4 <= len(tc) <= 7, 'Invalid "theme_color" format'
