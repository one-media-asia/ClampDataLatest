#!/usr/bin/env python3
"""Check that the Flask app serves the logo SVG at the expected URL."""
from app import app

with app.test_client() as c:
    resp = c.get('/static/images/logo.svg')
    print('status:', resp.status_code)
    print('content-type:', resp.headers.get('Content-Type'))
    body = resp.get_data(as_text=True)
    print('first 300 chars:\n', body[:300])
    print('\n... (length)', len(body))
