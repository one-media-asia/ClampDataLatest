#!/usr/bin/env python3
"""Check that the static logo file exists and print diagnostics."""
from pathlib import Path
import sys

BASE = Path(__file__).resolve().parents[1] / 'static' / 'images'
SVG = BASE / 'logo.svg'
ICON192 = BASE / 'icon-192.png'
ICON512 = BASE / 'icon-512.png'

print('Checking static/images...')
print('base dir:', BASE)

for p in (SVG, ICON192, ICON512):
    print('\n--', p.name)
    if not p.exists():
        print(' MISSING')
        continue
    try:
        s = p.read_bytes()
        print(' size:', len(s))
        if p.suffix.lower() == '.svg':
            text = p.read_text(encoding='utf-8')
            print(' starts with:', text.strip()[:200].replace('\n',' '))
    except Exception as e:
        print(' read error:', e)

# Quick permission check
try:
    st = SVG.stat()
    print('\npermissions ok, mode:', oct(st.st_mode & 0o777))
except Exception as e:
    print('stat error:', e)
    sys.exit(2)

print('\nDone')
