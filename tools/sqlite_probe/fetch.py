#!/usr/bin/env python3
"""Fetch the pinned amalgamation to a new directory outside the repository."""
import argparse
import hashlib
from pathlib import Path
import urllib.request
import zipfile
import io

URL = "https://www.sqlite.org/2026/sqlite-amalgamation-3530400.zip"
SHA3 = "628a44cfe82c66aed1ccbbe85a562d2e33ebe64b3288981ed76285612227934e"
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("destination", type=Path)
args = parser.parse_args()
with urllib.request.urlopen(URL, timeout=60) as response:
    data = response.read()
if hashlib.sha3_256(data).hexdigest() != SHA3:
    raise SystemExit("SQLite archive checksum mismatch")
with zipfile.ZipFile(io.BytesIO(data)) as archive:
    files = {name: archive.read("sqlite-amalgamation-3530400/" + name)
             for name in ("sqlite3.c", "sqlite3.h")}
args.destination.mkdir(parents=True, exist_ok=False)
for name, content in files.items():
    (args.destination / name).write_bytes(content)
print(args.destination.resolve())
