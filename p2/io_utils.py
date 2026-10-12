"""Atomic JSON writing for the grid drivers.

write_atomic is copied unchanged from Paper 1's v2_common.py (commit f2c960b,
Zenodo doi:10.5281/zenodo.23323685), so Paper 2 does not import Paper 1's training code.
"""
import json
import os
import tempfile


def write_atomic(obj, path):
    """Write JSON via a temp file + rename so a kill mid-write cannot leave a
    truncated results file (defect B15's neighbourhood)."""
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    # A FULL DISK killed the L4b follow-up four times on 2026-09-26 (ENOSPC on this
    # very write), each time discarding a cell that had taken over an hour. The cell
    # is in memory and correct; waiting for space costs nothing, crashing costs the
    # cell. So on ENOSPC: remove the partial temp file, say so loudly, wait, retry.
    import errno
    import time
    for attempt in range(48):                      # up to 8 h of waiting
        fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path) or ".", suffix=".tmp")
        try:
            with os.fdopen(fd, "w") as f:
                json.dump(obj, f, indent=1)
            os.replace(tmp, path)
            return
        except OSError as e:
            try:
                os.remove(tmp)
            except OSError:
                pass
            if e.errno != errno.ENOSPC:
                raise
            print(f"  !! DISK FULL writing {path} -- waiting 10 min for space "
                  f"(attempt {attempt + 1}/48); the result is held in memory", flush=True)
            time.sleep(600)
    raise OSError(errno.ENOSPC, f"disk still full after 8 h; {path} not written")
