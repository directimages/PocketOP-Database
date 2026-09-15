"""Weekly monitor for productUrl and manufacturerUrl link health.

Reads the published database from jsDelivr (the same CDN URLs the app and
website use), checks every productUrl and manufacturerUrl for liveness, and
writes a markdown triage report. Read-only: this package never edits any
database field. See PIPELINE.md and this package's own module docstrings for
the classification rules.
"""
