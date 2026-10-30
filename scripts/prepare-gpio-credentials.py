#!/usr/bin/env python3
"""Generate a private per-build root login secret without printing its value."""
import argparse
import os
from pathlib import Path
import secrets
import subprocess

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('build_dir', type=Path)
args = parser.parse_args()
folder = args.build_dir.resolve() / 'conf/gpio-private'
folder.mkdir(mode=0o700, exist_ok=True)
os.chmod(folder, 0o700)
password = folder / 'root-password.txt'
hashfile = folder / 'root-password.hash'
if password.exists() or hashfile.exists():
    raise SystemExit('Credential file already exists; preserving it. Inspect privately or explicitly archive both files before rotating.')
value = secrets.token_urlsafe(18)
hashed = subprocess.check_output(['openssl', 'passwd', '-6', '-stdin'], input=(value+'\n').encode()).decode()
for path, content in ((password, value+'\n'), (hashfile, hashed)):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, 'w') as stream:
        stream.write(content)
print('Created private credentials in', folder)
print('Read root-password.txt privately for UART root login; never publish these files.')
