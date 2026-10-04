import csv
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from artisanlib.roasting_compass import extractProfileRoastingCompassCSV
from artisanlib.util import decodeLocalStrict


class RoastingCompassImportTest(unittest.TestCase):
    def test_cp932_temperature_and_checkpoint(self) -> None:
        with TemporaryDirectory() as directory:
            file = Path(directory) / 'roast.csv'
            with file.open('w', encoding='cp932', newline='') as stream:
                writer = csv.writer(stream)
                writer.writerows([
                    ['制御データ', '', '', ''],
                    ['日　付', '保存時間', '製品温度(℃)', 'チェックポイント'],
                    ['2026/10/03', '8:23:01', '189.8', '0'],
                    ['2026/10/03', '8:23:02', '189.6', '1'],
                    ['2026/10/03', '8:23:03', '188.0', '2'],
                    ['2026/10/03', '8:23:04', '187.0', '3'],
                    ['', '', '', ''],
                    ['2026/10/03 8:23:01', '豆名', '18', '60'],
                    ['晴れ', '250', '', '焙煎メモ'],
                ])
            profile = extractProfileRoastingCompassCSV(str(file), [], [], [], float)

        self.assertEqual(profile['timex'], [0.0, 1.0, 2.0, 3.0])
        self.assertEqual(profile['temp2'], [189.8, 189.6, 188.0, 187.0])
        self.assertEqual(profile['temp1'], [-1.0] * 4)
        self.assertEqual(profile['timeindex'][0], 0)
        self.assertEqual(profile['timeindex'][6], 3)
        self.assertEqual(profile['specialevents'], [1, 2, 3])
        self.assertEqual(profile['specialeventsStrings'], ['CP1', 'CP2', 'CP3'])
        self.assertEqual(decodeLocalStrict(profile['title']), '豆名')
        self.assertEqual(profile['ambientTemp'], 18.0)
        self.assertEqual(profile['ambient_humidity'], 60.0)
        self.assertEqual(decodeLocalStrict(profile['roastingnotes']), '天候: 晴れ\n焙煎メモ')

    def test_rejects_unrelated_csv(self) -> None:
        with TemporaryDirectory() as directory:
            file = Path(directory) / 'other.csv'
            file.write_text('time,temp\n0,20\n', encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'Not a Roasting Compass'):
                extractProfileRoastingCompassCSV(str(file), [], [], [], float)


if __name__ == '__main__':
    unittest.main()
