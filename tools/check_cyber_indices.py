#!/usr/bin/env python3
## CYBER ##
"""
Guard-rail for the Cyberroaster (Skywalker V2) device indices.

WHY THIS EXISTS
---------------
Artisan has no device plugin API. Devices are integer-indexed entries in a
hardcoded list, and at runtime the active device is invoked *directly* by id:

    devicefunctionlist[qmc.device]()        # comm.py

So the position of SKYWALKER_BTET in `devicefunctionlist` (comm.py) MUST equal
the device id assigned to it in devices.py and announced in canvas.py. If an
upstream rebase shifts that position (e.g. Marko inserts a new device before
ours), the rebase can succeed *silently* while the Skywalker now calls the
wrong function. This script catches exactly that.

THE OFFSET TRAP
---------------
The two lists use DIFFERENT offsets:
  * comm.py  `devicefunctionlist` : list index == device id   (Fuji PID is a
    real element at index 0)
  * canvas.py `self.devices`       : list index == device id - 1 (Fuji PID is a
    COMMENT, not an element -- see the note on that list)
This script encodes both, and also asserts the +1 length relationship between
the two lists so a stray phantom entry can't quietly desync them.

USAGE
-----
    python3 tools/check_cyber_indices.py
Exit code 0 == all invariants hold, 1 == drift detected (suitable for a
pre-push hook or CI). Run it after every `git rebase upstream/master`.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
COMM = REPO / 'src' / 'artisanlib' / 'comm.py'
CANVAS = REPO / 'src' / 'artisanlib' / 'canvas.py'
DEVICES = REPO / 'src' / 'artisanlib' / 'devices.py'

# Canonical wiring: comm method name -> (canvas device name, device id we expect)
BTET_METHOD = 'SKYWALKER_BTET'
PF_METHOD = 'SKYWALKER_PF'
BTET_NAME = 'Skywalker BT/ET'
PF_NAME = '+Skywalker Burner/Air'


def _read(path: Path) -> str:
    if not path.is_file():
        sys.exit(f'FATAL: expected source file not found: {path}')
    return path.read_text(encoding='utf-8')


def _slice_list(text: str, open_re: str) -> list[str]:
    """Return the raw lines of a bracketed list literal, excluding the opening
    line (which holds the `[`) and the closing `]` line."""
    lines = text.splitlines()
    start = None
    for i, ln in enumerate(lines):
        if re.search(open_re, ln):
            start = i
            break
    if start is None:
        sys.exit(f'FATAL: could not locate list opening matching /{open_re}/')
    out = []
    for ln in lines[start + 1:]:
        if ln.strip().startswith(']'):
            return out
        out.append(ln)
    sys.exit(f'FATAL: unterminated list for /{open_re}/')


def parse_comm_methods(text: str) -> list[str]:
    """Ordered method names in serialport.devicefunctionlist (index == id)."""
    body = _slice_list(text, r'self\.devicefunctionlist\s*:.*=\s*\[')
    methods = []
    for ln in body:
        m = re.search(r'self\.(\w+)', ln)  # first entry per line
        if m:
            methods.append(m.group(1))
    return methods


def parse_canvas_devices(text: str) -> list[str]:
    """Ordered device-name strings in self.devices (index == id - 1).
    Comment-only lines like `#Fuji PID  #0` are not elements and are skipped."""
    body = _slice_list(text, r'self\.devices\s*:.*=\s*\[')
    names = []
    for ln in body:
        # quoted string at line start, allowing f/r/b string prefixes
        # (e.g. the f'+IKAWA ...' entry). Comment-only lines start with '#'
        # and are correctly skipped -- they are not list elements.
        m = re.match(r"\s*(?:[frbuFRBU]{1,2})?(['\"])(.*?)\1", ln)
        if m:
            names.append(m.group(2))
    return names


def parse_devices_assignment(text: str, name: str) -> int | None:
    """The integer id assigned to qmc.device in the `elif meter == '<name>'`
    branch of DeviceAssignmentDlg (devices.py)."""
    pat = re.compile(
        r"meter\s*==\s*['\"]" + re.escape(name) + r"['\"].*?"
        r"self\.aw\.qmc\.device\s*=\s*(\d+)",
        re.DOTALL,
    )
    m = pat.search(text)
    return int(m.group(1)) if m else None


def main() -> int:
    comm_txt = _read(COMM)
    canvas_txt = _read(CANVAS)
    devices_txt = _read(DEVICES)

    methods = parse_comm_methods(comm_txt)
    canvas_names = parse_canvas_devices(canvas_txt)

    results: list[tuple[bool, str]] = []

    def check(ok: bool, msg: str) -> None:
        results.append((ok, msg))

    # --- Source of truth: positions in comm.devicefunctionlist ---
    if BTET_METHOD not in methods:
        check(False, f'comm.py: {BTET_METHOD} missing from devicefunctionlist')
        btet_id = None
    else:
        btet_id = methods.index(BTET_METHOD)
        check(True, f'comm.py: {BTET_METHOD} at devicefunctionlist index {btet_id}')

    if PF_METHOD not in methods:
        check(False, f'comm.py: {PF_METHOD} missing from devicefunctionlist')
        pf_id = None
    else:
        pf_id = methods.index(PF_METHOD)
        check(True, f'comm.py: {PF_METHOD} at devicefunctionlist index {pf_id}')

    # --- Adjacency: PF echoes must sit right after BT/ET ---
    if btet_id is not None and pf_id is not None:
        check(pf_id == btet_id + 1,
              f'comm.py: {PF_METHOD} (id {pf_id}) is immediately after '
              f'{BTET_METHOD} (id {btet_id})')

    # --- Structural offset: canvas.devices is exactly 1 shorter (Fuji phantom) ---
    check(len(methods) == len(canvas_names) + 1,
          f'offset: len(devicefunctionlist)={len(methods)} == '
          f'len(canvas.devices)={len(canvas_names)} + 1')

    # --- canvas.py self.devices: index == id - 1 ---
    for name, expected in ((BTET_NAME, btet_id), (PF_NAME, pf_id)):
        if expected is None:
            continue
        if name not in canvas_names:
            check(False, f"canvas.py: '{name}' missing from self.devices")
            continue
        got = canvas_names.index(name) + 1
        check(got == expected,
              f"canvas.py: '{name}' maps to device id {got} (expected {expected})")

    # --- canvas.py nonserial / percentage sets carry the literal ids ---
    if btet_id is not None:
        # nonserial set: the BT/ET id must be flagged nonserial (BLE device)
        check(re.search(rf'\b{btet_id}\b[^\n]*nonserial', canvas_txt) is not None
              or re.search(rf'\b{btet_id}\b\s*[#)\]].*Skywalker BT/ET', canvas_txt) is not None,
              f'canvas.py: id {btet_id} present in a Skywalker BT/ET (nonserial) list entry')
    if pf_id is not None:
        check(re.search(rf'\b{pf_id}\b[^\n]*\+Skywalker Burner/Air', canvas_txt) is not None,
              f'canvas.py: id {pf_id} present in a +Skywalker Burner/Air list entry')

    # --- devices.py: explicit device assignment matches the BT/ET id ---
    if btet_id is not None:
        assigned = parse_devices_assignment(devices_txt, BTET_NAME)
        if assigned is None:
            check(False, f"devices.py: no `qmc.device = N` for '{BTET_NAME}'")
        else:
            check(assigned == btet_id,
                  f"devices.py: '{BTET_NAME}' assigns device {assigned} "
                  f'(expected {btet_id})')

    # --- report ---
    ok_all = all(ok for ok, _ in results)
    for ok, msg in results:
        print(f'  {"OK  " if ok else "FAIL"}  {msg}')
    print()
    if ok_all:
        print('CYBER index invariants: ALL OK '
              f'(Skywalker BT/ET=#{btet_id}, Burner/Air=#{pf_id})')
        return 0
    print('CYBER index invariants: DRIFT DETECTED -- fix before pushing.')
    print('  See the offset notes at the top of this file. Likely cause: an '
          'upstream device was inserted, shifting the indices.')
    return 1


if __name__ == '__main__':
    raise SystemExit(main())
