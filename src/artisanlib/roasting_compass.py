"""Import Fuji Royal Roasting Compass CSV profiles."""

import csv
from bisect import bisect_left
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from artisanlib.atypes import ProfileData

from artisanlib.util import decodeLocalStrict, encodeLocalStrict


_NUMBER = re.compile(r'\d+(?:\.\d+)?')


def convertedRoastingCompassFilename(file: str, profile: 'ProfileData') -> str:
    """Keep the source date and add the roast title to a converted profile name."""
    stem = Path(file).stem
    title = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '',
                   decodeLocalStrict(profile.get('title', b''))).strip(' .')
    name = f'{stem}_{title}' if title and title != stem else stem
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '', name).strip(' .')
    # Leave room for the extension within common filesystem component limits.
    return name.encode('utf-8')[:240].decode('utf-8', 'ignore') + '.alog'


def _setting_values(rows: list[list[str]], start: int, end: int) -> list[tuple[int, str]]:
    """Read a 16-by-4 footer grid, where each cell represents one roast minute."""
    return [(4 * row_index + column, value)
            for row_index, row in enumerate(rows[start:end])
            for column, cell in enumerate(row[:4])
            if (value := cell.strip()) and _NUMBER.fullmatch(value)]


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
        'title': encodeLocalStrict(Path(file).stem),
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
    # A blank row separates the samples from the summary table. Its first row
    # contains the coffee name; the next row's fourth column contains the memo.
    summary_index = next((i for i in range(len(timex) + 2, len(rows))
                          if rows[i] and rows[i][0].strip()), None)
    if summary_index is not None:
        summary = rows[summary_index]
        if len(summary) > 1 and summary[1].strip():
            profile['title'] = encodeLocalStrict(summary[1].strip())
        if len(summary) > 2 and summary[2].strip():
            profile['ambientTemp'] = float(summary[2])
        if len(summary) > 3 and summary[3].strip():
            profile['ambient_humidity'] = float(summary[3])
        if summary_index + 1 < len(rows):
            details = rows[summary_index + 1]
            weather = details[0].strip() if details else ''
            memo = details[3].strip() if len(details) > 3 else ''
            # Preserve weather in notes because Artisan has no dedicated weather field.
            # Each footer grid cell represents a minute from the roast start.
            # Preserve exact settings in notes as the graph event values use
            # Artisan's integer scale (tenths of kPa for gas pressure).
            gas = _setting_values(rows, summary_index + 5, summary_index + 21)
            damper = _setting_values(rows, summary_index + 21, summary_index + 37)
            notes = '\n'.join(part for part in (
                f'天候: {weather}' if weather else '',
                f'ガス圧 (kPa): {", ".join(value for _, value in gas)}' if gas else '',
                f'ダンパー開度: {", ".join(value for _, value in damper)}' if damper else '',
                memo,
            ) if part)
            if notes:
                profile['roastingnotes'] = encodeLocalStrict(notes)

            for event_type, settings in ((3, gas), (2, damper)):
                for minute, value in settings:
                    seconds = minute * 60
                    if seconds > timex[-1]:
                        continue
                    specialevents.append(bisect_left(timex, seconds))
                    specialeventstype.append(event_type)
                    external_value = (round(float(value) * 10) if event_type == 3
                                      else round(float(value)))
                    specialeventsvalue.append(_eventsExternal2InternalValue(external_value))
                    specialeventsStrings.append(
                        f'{value} kPa' if event_type == 3 else f'Damper {value}')

    if specialevents:
        events = sorted(zip(specialevents, specialeventstype,
                            specialeventsvalue, specialeventsStrings, strict=True),
                        key=lambda event: event[0])
        profile['specialevents'] = [event[0] for event in events]
        profile['specialeventstype'] = [event[1] for event in events]
        profile['specialeventsvalue'] = [event[2] for event in events]
        profile['specialeventsStrings'] = [event[3] for event in events]
    return profile
