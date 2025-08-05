from pathlib import Path
from json import load as json_load
from typing import Tuple, Dict, Union, Optional, List, TypedDict, cast, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from _pytest.python_api import ApproxScalar
    from _pytest.python import Metafunc

from artisanlib.atypes import ProfileData
from artisanlib.util import serialize, deserialize, csv_load, exportProfile2CSV

from _pytest.python_api import ApproxBase, ApproxMapping, ApproxSequenceLike
import pytest

#######
# Types

class FileData(TypedDict):
    directory:Path
    filename:str


CSV_KEYS = [
    'roastdate',
    'roasttime',
    'roastepoch',
    'roasttzoffset',
    'mode',
    'timex',
    'temp1',
    'temp2',
    'extradevices',
    'extraname1',
    'extraname2',
    'extratimex',
    'extratemp1',
    'extratemp2',
    'extramathexpression1',
    'extramathexpression2',
    'timeindex',
]

#######
# Config


# the values to some keys are to be ignored, like the data which might be set to the import date
values_to_ignore = [
    'roasttime',    # without seconds in CSV
    'roasttzoffset',
    'roastepoch',
    'timex',        # times are rounded to seconds
    'extradevices', # not stored in CSV, generated DUMMY (50)
    'extratimex',   # times are rounded to
    'extramathexpression1', # not exported to CSV
    'extramathexpression2', # not exported to CSV
]

#######
# Helpers


# approximation on nested structures (not directly supported by pytest)
# see https://stackoverflow.com/questions/56046524/check-if-python-dictionaries-are-equal-allowing-small-difference-for-floats
# by https://stackoverflow.com/users/8380999/iker

class ApproxBaseReprMixin(ApproxBase):
    def __repr__(self) -> str:

        def recur_repr_helper(obj:Any) -> Union[Dict[Any,Any], Tuple[Any,...], List[Any], ApproxScalar]:
            if isinstance(obj, dict):
                return {k : recur_repr_helper(v) for k, v in obj.items()}
            if isinstance(obj, tuple):
                return tuple(recur_repr_helper(o) for o in obj)
            if isinstance(obj, list):
                return [recur_repr_helper(o) for o in obj]
            return self._approx_scalar(obj)

        return f'approx({recur_repr_helper(self.expected)})'


class ApproxNestedSequenceLike(ApproxSequenceLike, ApproxBaseReprMixin):

    def _yield_comparisons(self, actual:Any) -> Any:
        mapping: Union[ApproxNestedMapping, ApproxNestedSequenceLike]
        for k in range(len(self.expected)):
            if isinstance(self.expected[k], dict):
                mapping = ApproxNestedMapping(self.expected[k], rel=self.rel, abs=self.abs, nan_ok=self.nan_ok)
                yield from mapping._yield_comparisons(actual[k])
            elif isinstance(self.expected[k], (tuple, list)):
                mapping = ApproxNestedSequenceLike(self.expected[k], rel=self.rel, abs=self.abs, nan_ok=self.nan_ok)
                yield from mapping._yield_comparisons(actual[k])
            else:
                yield actual[k], self.expected[k]

    def _check_type(self) -> None:
        pass



class ApproxNestedMapping(ApproxMapping, ApproxBaseReprMixin):

    def _yield_comparisons(self, actual:Any) -> Any:
        mapping: Union[ApproxNestedMapping, ApproxNestedSequenceLike]
        for k in self.expected:
            if isinstance(self.expected[k], dict):
                mapping = ApproxNestedMapping(self.expected[k], rel=self.rel, abs=self.abs, nan_ok=self.nan_ok)
                yield from mapping._yield_comparisons(actual[k])
            elif isinstance(self.expected[k], (tuple, list)):
                mapping = ApproxNestedSequenceLike(self.expected[k], rel=self.rel, abs=self.abs, nan_ok=self.nan_ok)
                yield from mapping._yield_comparisons(actual[k])
            else:
                yield actual[k], self.expected[k]

    def _check_type(self) -> None:
        pass


def nested_approx(expected:Any, rel:Optional[float]=None, absv:Optional[float]=None, nan_ok:bool=False) -> ApproxBase:
    if isinstance(expected, dict):
        return ApproxNestedMapping(expected, rel, absv, nan_ok)
    if isinstance(expected, (tuple, list)):
        return ApproxNestedSequenceLike(expected, rel, absv, nan_ok)
    return pytest.approx(expected, rel, absv, nan_ok)



#######
# Test Generator

def pytest_generate_tests(metafunc:'Metafunc') -> None:
    this_directory = Path(__file__).resolve().parent
    data_dir = (this_directory / 'data')
    profiles_dir = (data_dir / 'artisan')

    def get_file_data(ext:str) -> List[FileData]:
        files_data:List[FileData] = []
        for filename in [f.stem for f in profiles_dir.iterdir() if f.is_file() and f.suffix == ext]:
            # we found the filename again matching the second suffix, add it to the results
            profile_data:FileData = {
                'directory': profiles_dir,
                'filename': filename}
            files_data.append(profile_data)
        return files_data

    if 'alog_file' in metafunc.fixturenames:
        metafunc.parametrize('alog_file', get_file_data('.alog'))

    if 'json_file' in metafunc.fixturenames:
        metafunc.parametrize('json_file', get_file_data('.json'))


#######
# Tests

class TestLoadCompare:
    """Test loading of profiles available in the native Artisan .alog, .csv, .json formats."""


    def test_load_compare_alog_json(self, alog_file:FileData) -> None:
        alog_profile_path = (alog_file['directory'] / f"{alog_file['filename']}.alog")
        # Skip test if file doesn't exist
        if not alog_profile_path.exists():
            pytest.skip('Test .alog profile file not found')
        alog_obj = cast('ProfileData',deserialize(str(alog_profile_path)))

        json_profile_path = (alog_file['directory'] / f"{alog_file['filename']}.json")
        # Skip test if file doesn't exist
        if not json_profile_path.exists():
            pytest.skip('Test .json profile file not found')

        with open(json_profile_path, encoding='utf-8') as infile:
            json_obj = json_load(infile)
            for key, value in alog_obj.items():
                assert key in json_obj
                if key in values_to_ignore:
                    # even if the value is ignored, the key should be present
                    assert key in json_obj
                else:
                    assert value == nested_approx(json_obj[key]) # approximation on nested data structures needed for rounding issues



    def test_load_compare_alog_csv(self, alog_file:FileData) -> None:
        alog_profile_path = (alog_file['directory'] / f"{alog_file['filename']}.alog")
        # Skip test if file doesn't exist
        if not alog_profile_path.exists():
            pytest.skip('Test .alog profile file not found')
        alog_obj = cast('ProfileData',deserialize(str(alog_profile_path)))

        csv_profile_path = (alog_file['directory'] / f"{alog_file['filename']}.csv")
        # Skip test if file doesn't exist
        if not csv_profile_path.exists():
            pytest.skip('Test .csv profile file not found')

        with open(csv_profile_path, encoding='utf-8') as infile:
            csv_obj = csv_load(infile)
            for key in CSV_KEYS:
                assert key in alog_obj
                assert key in csv_obj
                if key not in values_to_ignore:
                    assert alog_obj[key] == nested_approx(csv_obj[key]) # type: ignore[literal-required] # approximation on nested data structures needed for rounding issues



    def test_load_compare_json_csv(self, json_file:FileData) -> None:
        json_profile_path = (json_file['directory'] / f"{json_file['filename']}.json")
        # Skip test if file doesn't exist
        if not json_profile_path.exists():
            pytest.skip('Test .json profile file not found')
        with open(json_profile_path, encoding='utf-8') as json_infile:
            json_obj = json_load(json_infile)

            csv_profile_path = (json_file['directory'] / f"{json_file['filename']}.csv")
            # Skip test if file doesn't exist
            if not csv_profile_path.exists():
                pytest.skip('Test .csv profile file not found')

            with open(csv_profile_path, encoding='utf-8') as infile:
                csv_obj = csv_load(infile)
                for key in CSV_KEYS:
                    assert key in json_obj
                    assert key in csv_obj
                    if key not in values_to_ignore:
                        assert json_obj[key] == nested_approx(csv_obj[key]) # type: ignore[literal-required] # approximation on nested data structures needed for rounding issues



class TestLoadSaveLoad:
    """Test loading and saving of profiles available in the native Artisan .alog, .csv, .json formats."""

    # load/save/re-load/compare alog
    def test_load_save_load_alog(self, alog_file:FileData, tmp_path:Path) -> None:
        alog_profile_path = (alog_file['directory'] / f"{alog_file['filename']}.alog")
        # Skip test if file doesn't exist
        if not alog_profile_path.exists():
            pytest.skip('Test .alog profile file not found')
        alog_obj = deserialize(str(alog_profile_path))

        # Temp file
        alog_temp_profile_path = (tmp_path / f"{alog_file['filename']}.alog")

        # Write temp alog file
        serialize(str(alog_temp_profile_path), alog_obj)

        # Reload temp alog file
        alog_obj_reloaded = cast('ProfileData', deserialize(str(alog_temp_profile_path)))

        # Compare with originally loaded alog file
        for key, value in alog_obj.items():
            assert key in alog_obj_reloaded
            if key in values_to_ignore:
                # even if the value is ignored, the key should be present
                assert key in alog_obj_reloaded
            else:
                assert value == nested_approx(alog_obj_reloaded[key]) # type: ignore[literal-required] # approximation on nested data structures needed for rounding issues

    # load alog/save csv/re-load csv/compare
    def test_load_save_load_csv(self, alog_file:FileData, tmp_path:Path) -> None:
        alog_profile_path = (alog_file['directory'] / f"{alog_file['filename']}.alog")
        # Skip test if file doesn't exist
        if not alog_profile_path.exists():
            pytest.skip('Test .alog profile file not found')
        alog_obj = deserialize(str(alog_profile_path))

        # Temp file
        csv_temp_profile_path = (tmp_path / f"{alog_file['filename']}.csv")

        # Write temp csv file
        exportProfile2CSV(str(csv_temp_profile_path), cast('ProfileData', alog_obj))

        # Reload temp csv file
        with open(csv_temp_profile_path, encoding='utf-8') as infile:
            csv_obj_reloaded = csv_load(infile)

            # Compare the CSV-fragment with originally loaded alog file
            for key in CSV_KEYS:
                assert key in alog_obj
                assert key in csv_obj_reloaded
                if key not in values_to_ignore:
                    assert alog_obj[key] == nested_approx(csv_obj_reloaded[key]) # type: ignore[literal-required] # approximation on nested data structures needed for rounding issues
