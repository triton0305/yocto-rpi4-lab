#!/usr/bin/env python3
"""Synchronize only this repository's integration files into an existing layer.

Existing differing files are backed up before replacement. BBLAYERS and all
unrelated files are left intact; the caller must select the actual active layer.
"""
import argparse
from datetime import datetime, timezone
from pathlib import Path
import shutil

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('active_layer',type=Path)
p.add_argument('backup_dir',type=Path)
a=p.parse_args()
source=Path(__file__).resolve().parents[1]/'layers/meta-yocto-lab'
target=a.active_layer.resolve()
assert (target/'conf/layer.conf').is_file(), 'Select an existing layer'
assert (target/'conf/layer.conf').read_bytes()==(source/'conf/layer.conf').read_bytes(), 'Review differing layer.conf first'
backup=a.backup_dir.resolve()/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
for src in sorted(source.rglob('*')):
    if not src.is_file(): continue
    rel=src.relative_to(source); dst=target/rel
    if dst.exists() and dst.read_bytes()==src.read_bytes(): continue
    if dst.exists():
        saved=backup/rel; saved.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(dst,saved)
    dst.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(src,dst)
    print(rel)
print('Integration synchronized; unrelated files and BBLAYERS preserved.')
