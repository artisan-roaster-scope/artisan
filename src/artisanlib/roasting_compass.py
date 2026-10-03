"""Import Fuji Royal Roasting Compass CSV profiles."""

import csv
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from artisanlib.atypes import ProfileData


def _read_rows(file: str) -> list[list[str]]:
    for encoding in ('utf-8-sig', 'cp932'):
        try:
            with open(file, encoding=encoding, newline='') as stream:
                return list(csv.reader(stream))
        except UnicodeDecodeError:
            continue
    raise ValueError('Unsupported Roasting Compass CSV encoding')


def extractProfileRoastingCompassCSV(
        file: str,
        _etypesdefault: list[str],
        _alt_etypesdefault: list[str],
        _artisanflavordefaultlabels: list[str],
        _eventsExternal2InternalValue: Callable[[int], float]) -> 'ProfileData':
    rows = _read_rows(file)
    expected_header = ['日　付', '保存時間', '製品温度(℃)', 'チェックポイント']
    if len(rows) < 3 or rows[0][0] != '制御データ' or rows[1][:4] != expected_header:
        raise ValueError('Not a Roasting Compass CSV profile')

    timex: list[float] = []
    temp2: list[float] = []
    specialevents: list[int] = []
    specialeventstype: list[int] = []
    specialeventsvalue: list[float] = []
    specialeventsStrings: list[str] = []
    started: datetime | None = None

    for row in rows[2:]:
        if not row or not row[0].strip():
            break  # The remaining rows contain a separate summary table.
        if len(row) < 4:
            raise ValueError('Incomplete Roasting Compass sample row')
        try:
            # Roasting Compass stores local wall-clock time without a timezone.
            timestamp = datetime.strptime(  # noqa: DTZ007
                f'{row[0].strip()} {row[1].strip()}', '%Y/%m/%d %H:%M:%S')
            temperature = float(row[2])
            checkpoint = int(row[3])
        except ValueError as exc:
            raise ValueError('Invalid Roasting Compass sample row') from exc
        if started is None:
            started = timestamp
        elapsed = (timestamp - started).total_seconds()
        if elapsed < 0 or (timex and elapsed <= timex[-1]):
            raise ValueError('Roasting Compass timestamps must increase')
        timex.append(elapsed)
        temp2.append(temperature)
        if checkpoint in (1, 2, 3):
            specialevents.append(len(timex) - 1)
            specialeventstype.append(4)  # Artisan custom event
            specialeventsvalue.append(0.0)
            specialeventsStrings.append(f'CP{checkpoint}')

    if not timex or started is None:
        raise ValueError('Roasting Compass CSV has no temperature samples')

    profile: ProfileData = {
        'title': Path(file).stem,
        'mode': 'C',
        'samplinginterval': 1.0,
        'timex': timex,
        'temp1': [-1.0] * len(timex),
        'temp2': temp2,
        'timeindex': [0, 0, 0, 0, 0, 0, len(timex) - 1, 0],
        'roastdate': started.date().isoformat(),
        'roastisodate': started.date().isoformat(),
        'roasttime': started.time().isoformat(),
        'roastepoch': int(started.astimezone().timestamp()),
    }
    if specialevents:
        profile['specialevents'] = specialevents
        profile['specialeventstype'] = specialeventstype
        profile['specialeventsvalue'] = specialeventsvalue
        profile['specialeventsStrings'] = specialeventsStrings

    # The first summary row repeats the roast start and names the coffee.
    summary = rows[len(timex) + 3:]
    if summary and len(summary[0]) > 1 and summary[0][1].strip():
        profile['title'] = summary[0][1].strip()
    return profile
