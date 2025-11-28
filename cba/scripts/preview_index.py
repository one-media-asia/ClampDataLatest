"""Neutralized preview helper for security.

This script rendered templates locally to inspect output. It has been
disabled because executing template rendering with DB access from the
repository can expose sensitive data.
"""
import sys

print('This helper has been disabled for security. Please remove the file if unneeded.')
sys.exit(0)
