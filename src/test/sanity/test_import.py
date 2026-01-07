from pathlib import Path
from json import load as json_load
from collections.abc import Callable
from typing import override, Any, TypedDict, TYPE_CHECKING

if TYPE_CHECKING:
    from _pytest.python_api import ApproxScalar
    from _pytest.python import Metafunc

from _pytest.python_api import ApproxBase, ApproxMapping, ApproxSequenceLike
import pytest


from artisanlib.atypes import ProfileData

from artisanlib.giesen import extractProfileGiesenCSV
from artisanlib.ikawa import extractProfileIkawaCSV
from artisanlib.kaleido import extractProfileKaleidoCSV
from artisanlib.loring import extractProfileLoringCSV
from artisanlib.petroncini import extractProfilePetronciniCSV
from artisanlib.roest import extractProfileRoestCSV
from artisanlib.rubasse import extractProfileRubasseCSV
from artisanlib.stronghold import extractProfileStrongholdXLSX
from artisanlib.cropster import extractProfileCropsterXLS


#######
# Types

Extractor = Callable[[str, list[str], list[str], list[str], Callable[[int],float]], ProfileData|None] # ty:ignore
ImportSpecs = tuple[Extractor, str, str]

class ImportData(TypedDict):
    extractor:Extractor
    directory:Path
    filename:str
    ext:str


#######
# Mocks

etypesdefault:list[str] = [ 'Air','Drum','Damper', 'Burner', '--']
alt_etypesdefault:list[str] = ['Fan', 'Drum', 'Cooling', 'Heater', '--']
artisanflavordefaultlabels:list[str] = ['Acidity','Aftertaste', 'Clean Cup', 'Head', 'Fragrance', 'Sweetness', 'Aroma', 'Balance', 'Body']

def eventsExternal2InternalValue(v:int) -> float:
    if v == 0:
        return 0.
    if v >= 1:
        return v/10. + 1.
    return v/10. - 1.


#######
# Config


# the values to some keys are to be ignored, like the data which might be set to the import date
values_to_ignore = [
    'roastdate', 'roastisodate', 'roasttime', 'roastepoch', 'roasttzoffset', 'roastUUID'
]

# the importers to test
# input files with the specified file extension are expected to be located in a subdirectory of the 'data' directory,
# named by the second argument, next to this test file together with a variant of the profile exported as Artisan JSON
# eg. ./data/cropster/<name>.xls and ./data/cropster/<name>.json
import_specs:list[ImportSpecs] = [
    (extractProfileCropsterXLS, 'cropster', '.xls'),
    (extractProfileGiesenCSV, 'giesen', '.csv'),
    (extractProfileIkawaCSV, 'ikawa', '.csv'),
    (extractProfileKaleidoCSV, 'kaleido', '.csv'),
    (extractProfileLoringCSV, 'loring', '.csv'),
    (extractProfilePetronciniCSV, 'petroncini', '.csv'),
    (extractProfileRoestCSV, 'roest', '.csv'),
    (extractProfileRubasseCSV, 'rubasse', '.csv'),
    (extractProfileStrongholdXLSX, 'stronghold', '.xlsx'),
]



#######
# Helpers


# approximation on nested structures (not directly supported by pytest)
# see https://stackoverflow.com/questions/56046524/check-if-python-dictionaries-are-equal-allowing-small-difference-for-floats
# by https://stackoverflow.com/users/8380999/iker

class ApproxBaseReprMixin(ApproxBase):

    @override
    def __repr__(self) -> str:

        def recur_repr_helper(obj:Any) -> dict[Any,Any]|tuple[Any,...]|list[Any]|ApproxScalar:
            if isinstance(obj, dict):
                return {k : recur_repr_helper(v) for k, v in obj.items()}
            if isinstance(obj, tuple):
                return tuple(recur_repr_helper(o) for o in obj)
            if isinstance(obj, list):
                return [recur_repr_helper(o) for o in obj]
            return self._approx_scalar(obj)

        return f'approx({recur_repr_helper(self.expected)})'


class ApproxNestedSequenceLike(ApproxSequenceLike, ApproxBaseReprMixin):

    @override
    def _yield_comparisons(self, actual:Any) -> Any:
        mapping: ApproxNestedMapping|ApproxNestedSequenceLike
        for k in range(len(self.expected)):
            if isinstance(self.expected[k], dict):
                mapping = ApproxNestedMapping(self.expected[k], rel=self.rel, abs=self.abs, nan_ok=self.nan_ok)
                yield from mapping._yield_comparisons(actual[k])
            elif isinstance(self.expected[k], (tuple, list)):
                mapping = ApproxNestedSequenceLike(self.expected[k], rel=self.rel, abs=self.abs, nan_ok=self.nan_ok)
                yield from mapping._yield_comparisons(actual[k])
            else:
                yield actual[k], self.expected[k]

    @override
    def _check_type(self) -> None:
        pass



class ApproxNestedMapping(ApproxMapping, ApproxBaseReprMixin):

    @override
    def _yield_comparisons(self, actual:Any) -> Any:
        mapping: ApproxNestedMapping|ApproxNestedSequenceLike
        for k in self.expected:
            if isinstance(self.expected[k], dict):
                mapping = ApproxNestedMapping(self.expected[k], rel=self.rel, abs=self.abs, nan_ok=self.nan_ok)
                yield from mapping._yield_comparisons(actual[k])
            elif isinstance(self.expected[k], (tuple, list)):
                mapping = ApproxNestedSequenceLike(self.expected[k], rel=self.rel, abs=self.abs, nan_ok=self.nan_ok)
                yield from mapping._yield_comparisons(actual[k])
            else:
                yield actual[k], self.expected[k]

    @override
    def _check_type(self) -> None:
        pass


def nested_approx(expected:Any, rel:float|None=None, absv:float|None=None, nan_ok:bool=False) -> ApproxBase:
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

    def get_import_data(extractor:Extractor, dir_name:str, ext:str) -> list[ImportData]:
        profiles_dir = (data_dir / dir_name)
        import_data:list[ImportData] = []
        for filename in [f.stem for f in profiles_dir.iterdir() if f.is_file() and f.suffix == ext]:
            roest_data:ImportData = {
                'extractor': extractor,
                'directory': profiles_dir,
                'filename': filename,
                'ext': ext}
            import_data.append(roest_data)
        return import_data

    if 'import_data' in metafunc.fixturenames:
        import_data:list[ImportData] = []
        for spec in import_specs:
            import_data.extend(get_import_data(*spec))
        metafunc.parametrize('import_data', import_data)



#######
# Test


class TestProfileImport:
    """Test import of profiles available in formats different to the native Artisan .alog format."""


    def test_import(self, import_data:ImportData) -> None:
        test_profile_path = (import_data['directory'] / f"{import_data['filename']}{import_data['ext']}")
        # Skip test if file doesn't exist
        if not test_profile_path.exists():
            pytest.skip('Test profile file not found')
        csv_obj:ProfileData|None = import_data['extractor'](
            str(test_profile_path),
            etypesdefault,
            alt_etypesdefault,
            artisanflavordefaultlabels,
            eventsExternal2InternalValue)
        if csv_obj is None:
            pytest.skip('ProfileData is None')
        else:
            test_validation_profile_path = (import_data['directory'] / f"{import_data['filename']}.json")
            # Skip test if file doesn't exist
            if not test_validation_profile_path.exists():
                pytest.skip('Test validation profile file not found')
            with open(test_validation_profile_path, encoding='utf-8') as infile:
                json_obj = json_load(infile)
                for key, value in csv_obj.items():
                    assert key in json_obj
                    if key not in values_to_ignore:
                        assert value == nested_approx(json_obj[key]) # approximation on nested data structures needed for rounding issues
