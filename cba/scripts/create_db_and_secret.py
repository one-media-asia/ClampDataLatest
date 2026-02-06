#!/usr/bin/env python3
"""Helper: generate SECRET_KEY (runtime) and run db.create_all().

Run: python scripts/create_db_and_secret.py

This prints the generated secret so you can persist it if desired.
"""
import os
import secrets
import pathlib

secret = secrets.token_urlsafe(48)
# set for this process before importing the app
os.environ['SECRET_KEY'] = secret
print('Generated SECRET_KEY:', secret)

# change to repo cba/ so imports work as in normal execution
repo_dir = pathlib.Path(__file__).resolve().parents[1]
os.chdir(str(repo_dir))

from app import app, db

with app.app_context():
    db.create_all()
    print('db.create_all() completed')
