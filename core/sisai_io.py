#!/usr/bin/env python3
"""SISAI atomic JSON I/O — the single crash-safe write primitive (stdlib only).

The autonomous security loop accumulates a ledger/registry it must not corrupt. A
plain open(path,"w") leaves a half-written file on a crash. Here we write to a temp
file in the SAME directory then os.replace (atomic same-volume rename), so the file
is always either the previous valid state or the new one. Deterministic: the random
temp suffix never affects the final path or content.
"""

import json
import os
import tempfile


def atomic_write_json(path: str, obj) -> None:
    """Serialize obj to path atomically (temp + os.replace). Sorted keys, UTF-8."""
    directory = os.path.dirname(os.path.abspath(path))
    os.makedirs(directory, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=directory, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(obj, f, ensure_ascii=False, indent=2, sort_keys=True)
            f.write("\n")
        os.replace(tmp, path)
    except BaseException:
        try:
            os.remove(tmp)
        except OSError:
            pass
        raise


def read_json(path: str, default=None):
    """Read a JSON file; return default if it does not exist."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return default
