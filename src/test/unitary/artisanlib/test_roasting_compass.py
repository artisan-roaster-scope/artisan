import csv
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from artisanlib.roasting_compass import (convertedRoastingCompassFilename,
                                          applyRoastingCompassCheckpointMapping,
                                          extractProfileRoastingCompassCSV)
from artisanlib.util import (decodeLocalStrict, encodeLocalStrict,
                             events_external_to_internal_value)


class RoastingCompassImportTest(unittest.TestCase):
    def test_summary_turning_point_precedes_flat_bt_minimum(self) -> None:
        with TemporaryDirectory() as directory:
            file = Path(directory) / 'turning_point.csv'
            rows = [
                ['制御データ', '', '', ''],
                ['日　付', '保存時間', '製品温度(℃)', 'チェックポイント'],
            ]
            rows += [['2026/10/03', f'8:{23 + second // 60:02d}:{second % 60:02d}',
                      '96.7' if 68 <= second <= 72 else str(190 - second),
                      '1' if second == 73 else '0']
                     for second in range(76)]
            rows += [
                ['', '', '', ''],
                ['2026/10/03 8:23:00', '豆名', '', ''],
                ['', '', '', ''],
                ['01:08', '96.7', '01:13', '117.0'],
            ]
            with file.open('w', encoding='cp932', newline='') as stream:
                csv.writer(stream).writerows(rows)
            profile = extractProfileRoastingCompassCSV(
                str(file), [], [], [], events_external_to_internal_value)

        self.assertEqual(profile['TP_override_idx'], 68)
        self.assertEqual(profile['timex'][profile['TP_override_idx']], 68)
        self.assertEqual(profile['temp2'][profile['TP_override_idx']], 96.7)
        self.assertIn('CP1', profile['specialeventsStrings'])

    def test_checkpoint_mapping_uses_roast_markers_and_keeps_none(self) -> None:
        profile = {
            'timeindex': [0, 0, 0, 0, 0, 0, 4, 0],
            'specialevents': [1, 2, 3, 4],
            'specialeventstype': [4, 4, 4, 3],
            'specialeventsvalue': [0.0, 0.0, 0.0, 1.4],
            'specialeventsStrings': ['CP1', 'CP2', 'CP3', '4 kPa'],
        }
        applyRoastingCompassCheckpointMapping(
            profile, {1: 'DRY END', 2: 'FC START', 3: 'NONE'})
        self.assertEqual(profile['timeindex'], [0, 1, 2, 0, 0, 0, 4, 0])
        self.assertEqual(profile['specialevents'], [3, 4])
        self.assertEqual(profile['specialeventsStrings'], ['CP3', '4 kPa'])
        self.assertEqual(profile['specialeventstype'], [4, 3])
        self.assertEqual(profile['specialeventsvalue'], [0.0, 1.4])

    def test_duplicate_checkpoint_marker_is_rejected(self) -> None:
        profile = {'timeindex': [0] * 8}
        with self.assertRaisesRegex(ValueError, 'at most once'):
            applyRoastingCompassCheckpointMapping(
                profile, {1: 'FC START', 2: 'FC START'})

    def test_cp932_temperature_and_checkpoint(self) -> None:
        with TemporaryDirectory() as directory:
            file = Path(directory) / 'roast.csv'
            with file.open('w', encoding='cp932', newline='') as stream:
                writer = csv.writer(stream)
                rows = [
                    ['制御データ', '', '', ''],
                    ['日　付', '保存時間', '製品温度(℃)', 'チェックポイント'],
                    ['2026/10/03', '8:23:01', '189.8', '0'],
                    ['2026/10/03', '8:23:02', '189.6', '1'],
                    ['2026/10/03', '8:23:03', '188.0', '2'],
                    ['2026/10/03', '8:23:04', '187.0', '3'],
                    ['', '', '', ''],
                    ['2026/10/03 8:23:01', '豆名', '18', '60'],
                    ['晴れ', '250', '', '焙煎メモ'],
                    ['01:08', '96.7', '08:08', '198.4'],
                    ['', '', '', ''],
                    ['09:28', '205.1', '', ''],
                ]
                rows += [['1', '2.2', '', ''], ['1.6', '0.8', '', '']]
                rows += [['', '', '', ''] for _ in range(14)]
                rows += [['1', '4', '', ''], ['3', '', '2', '']]
                rows += [['', '', '', ''] for _ in range(14)]
                writer.writerows(rows)
            profile = extractProfileRoastingCompassCSV(
                str(file), [], [], [], events_external_to_internal_value)

        self.assertEqual(profile['timex'], [0.0, 1.0, 2.0, 3.0])
        self.assertEqual(profile['temp2'], [189.8, 189.6, 188.0, 187.0])
        self.assertEqual(profile['temp1'], [-1.0] * 4)
        self.assertEqual(profile['timeindex'][0], 0)
        self.assertEqual(profile['timeindex'][6], 3)
        self.assertNotIn('TP_override_idx', profile)  # summary TP lies beyond the samples
        self.assertEqual(profile['specialevents'], [0, 0, 1, 2, 3])
        self.assertEqual(profile['specialeventstype'], [3, 2, 4, 4, 4])
        self.assertEqual(profile['specialeventsStrings'],
                         ['1 kPa', 'Damper 1', 'CP1', 'CP2', 'CP3'])
        self.assertEqual(decodeLocalStrict(profile['title']), '豆名')
        self.assertEqual(convertedRoastingCompassFilename(str(file), profile),
                         'roast_豆名.alog')
        profile['title'] = encodeLocalStrict('豆/名:別?')
        self.assertEqual(convertedRoastingCompassFilename(str(file), profile),
                         'roast_豆名別.alog')
        self.assertEqual(profile['ambientTemp'], 18.0)
        self.assertEqual(profile['ambient_humidity'], 60.0)
        self.assertEqual(decodeLocalStrict(profile['roastingnotes']),
                         '天候: 晴れ\nガス圧 (kPa): 1, 2.2, 1.6, 0.8\n'
                         'ダンパー開度: 1, 4, 3, 2\n焙煎メモ')

    def test_setting_grid_cells_become_minute_events(self) -> None:
        with TemporaryDirectory() as directory:
            file = Path(directory) / 'settings.csv'
            rows = [
                ['制御データ', '', '', ''],
                ['日　付', '保存時間', '製品温度(℃)', 'チェックポイント'],
            ]
            rows += [['2026/10/03', f'8:{23 + minute:02d}:01', '180', '0']
                     for minute in range(9)]
            rows += [
                ['', '', '', ''],
                ['2026/10/03 8:23:01', '豆名', '', ''],
                ['', '', '', ''],
                ['01:08', '96.7', '', ''],
                ['', '', '', ''],
                ['09:28', '205.1', '', ''],
                ['1', '2.2', '', ''],
                ['1.6', '', '0.8', ''],
                ['0.4', '', '', ''],
            ]
            rows += [['', '', '', ''] for _ in range(13)]
            rows += [['1', '4', '', ''], ['3', '', '2', '']]
            rows += [['', '', '', ''] for _ in range(14)]
            with file.open('w', encoding='cp932', newline='') as stream:
                csv.writer(stream).writerows(rows)
            profile = extractProfileRoastingCompassCSV(
                str(file), [], [], [], events_external_to_internal_value)

        self.assertEqual(profile['specialevents'], [0, 0, 1, 1, 4, 4, 6, 6, 8])
        self.assertEqual(profile['specialeventstype'], [3, 2, 3, 2, 3, 2, 3, 2, 3])
        self.assertEqual(profile['specialeventsStrings'],
                         ['1 kPa', 'Damper 1', '2.2 kPa', 'Damper 4',
                          '1.6 kPa', 'Damper 3', '0.8 kPa', 'Damper 2', '0.4 kPa'])
        self.assertEqual(profile['specialeventsvalue'][2], 3.2)  # 2.2 kPa as G22
        self.assertEqual(profile['specialeventsvalue'][3], 1.4)  # Damper 4 as D4

    def test_rejects_unrelated_csv(self) -> None:
        with TemporaryDirectory() as directory:
            file = Path(directory) / 'other.csv'
            file.write_text('time,temp\n0,20\n', encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'Not a Roasting Compass'):
                extractProfileRoastingCompassCSV(str(file), [], [], [], float)


if __name__ == '__main__':
    unittest.main()
