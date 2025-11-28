#!/usr/bin/env python3
"""
Generate PNG icons from `static/images/logo.svg`.
Writes: `static/images/icon-192.png`, `static/images/icon-512.png`.
"""
import sys
from pathlib import Path
try:
    import cairosvg
except Exception as e:
    print('cairosvg not available:', e, file=sys.stderr)
    sys.exit(2)

BASE = Path(__file__).resolve().parents[1] / 'static' / 'images'
SVG = BASE / 'logo.svg'
OUT_192 = BASE / 'icon-192.png'
OUT_512 = BASE / 'icon-512.png'

if not SVG.exists():
    print('Source SVG not found:', SVG, file=sys.stderr)
    sys.exit(3)

print('Converting', SVG)
try:
    cairosvg.svg2png(url=str(SVG), write_to=str(OUT_192), output_width=192, output_height=192)
    cairosvg.svg2png(url=str(SVG), write_to=str(OUT_512), output_width=512, output_height=512)
    print('Wrote', OUT_192)
    print('Wrote', OUT_512)
except Exception as e:
    print('Conversion failed:', e, file=sys.stderr)
    sys.exit(4)

print('Done')
