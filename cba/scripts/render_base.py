#!/usr/bin/env python3
from app import app
from flask import render_template
from pathlib import Path

out = Path('tmp_rendered_base.html')
with app.app_context():
    html = render_template('base.html', current_year=2025)
    out.write_text(html, encoding='utf-8')
    print('Wrote', out)
    print('\n--- header snippet ---')
    print(html.split('<main>')[0][:1200])
