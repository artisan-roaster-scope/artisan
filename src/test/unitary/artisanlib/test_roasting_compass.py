import csv
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from artisanlib.roasting_compass import extractProfileRoastingCompassCSV


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
                    ['', '', '', ''],
                    ['2026/10/03 8:23:01', '豆名', '', ''],
                ])
            profile = extractProfileRoastingCompassCSV(str(file), [], [], [], float)

        self.assertEqual(profile['timex'], [0.0, 1.0])
        self.assertEqual(profile['temp2'], [189.8, 189.6])
        self.assertEqual(profile['temp1'], [-1.0, -1.0])
        self.assertEqual(profile['timeindex'][0], 0)
        self.assertEqual(profile['timeindex'][6], 1)
        self.assertEqual(profile['specialevents'], [1])
        self.assertEqual(profile['specialeventsStrings'], ['CP1'])
        self.assertEqual(profile['title'], '豆名')

    def test_rejects_unrelated_csv(self) -> None:
        with TemporaryDirectory() as directory:
            file = Path(directory) / 'other.csv'
            file.write_text('time,temp\n0,20\n', encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'Not a Roasting Compass'):
                extractProfileRoastingCompassCSV(str(file), [], [], [], float)


if __name__ == '__main__':
    unittest.main()
