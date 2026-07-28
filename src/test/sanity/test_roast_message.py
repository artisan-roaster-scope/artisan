from pathlib import Path
from typing import cast, TypedDict, TYPE_CHECKING

if TYPE_CHECKING:
    from _pytest.python import Metafunc

# Import the atypes module directly without aggressive mocking
# The atypes module only contains type definitions and doesn't need runtime mocking
from artisanlib import atypes
from artisanlib.util import deserialize, roast_message

import pytest


#######
# Types

class FileData(TypedDict):
    directory:Path
    filename:str


#######
# Test Generator

def pytest_generate_tests(metafunc:'Metafunc') -> None:
    this_directory = Path(__file__).resolve().parent
    data_dir = (this_directory / 'data')
    profiles_dir = (data_dir / 'artisan')

    def get_file_data(ext:str) -> list[FileData]:
        files_data:list[FileData] = []
        for filename in [f.stem for f in profiles_dir.iterdir() if f.is_file() and f.suffix == ext]:
            # we found the filename again matching the second suffix, add it to the results
            profile_data:FileData = {
                'directory': profiles_dir,
                'filename': filename}
            files_data.append(profile_data)
        return files_data

    if 'alog_file' in metafunc.fixturenames:
        metafunc.parametrize('alog_file', get_file_data('.alog'))


# pytest -s -k TestRoastMessageOnFiles
class TestRoastMessageOnFiles:
    """Test loading and saving of profiles available in the native Artisan .alog, .csv, .json formats."""

    def test_load_save_load_alog(self, alog_file:FileData) -> None:
        alog_profile_path = (alog_file['directory'] / f"{alog_file['filename']}.alog")

        # Skip test if file doesn't exist
        if not alog_profile_path.exists():
            pytest.skip('Test .alog profile file not found')
        alog_obj = deserialize(str(alog_profile_path))

        profile_data: atypes.ProfileData = cast(atypes.ProfileData, alog_obj)

        msg = roast_message(profile_data, org_id = 'org1', machine_id = 'machine1',
                interpolate_drops=True,
                smooth_curves=True,
                add_additional_curves=1,
                rate_of_rise=1,
                min_sampling_interval=1,
                seconds_before_charge=30, # or 0 or None
                seconds_after_drop=30, # or 0 or None
                factor=100)

        if msg is not None:

            from google.protobuf.json_format import MessageToDict # MessageToJson
            msg_dict = MessageToDict(msg, preserving_proto_field_name=True)

#    #        print(msg_dict)
#    #        from google.protobuf import json_format
#    #        print(json_format.MessageToJson(msg, preserving_proto_field_name=True))
#    #        print(msg.HasField("org_id"))
#    #        print("msg_dict",msg_dict)
#
#            print('---')
#            print(f"{alog_file['filename']}.alog")
#            print('#readings',len(msg_dict['times']))
#            msg_json = MessageToJson(msg, preserving_proto_field_name=True)
#            print('dict size',len(msg_json)/1024)
#            import zlib
#            print('dict compressed', len(zlib.compress(msg_json.encode('utf-8')))/1024)
#            print('proto size',len(msg.SerializeToString())/1024)
#            print('proto compressed',len(zlib.compress(msg.SerializeToString()))/1024)
#            print('total time', stringfromseconds(msg_dict['times'][-1] - msg_dict['times'][0]))
#            print('sample time', msg_dict['times'][1]- msg_dict['times'][0])
#            print('start time',msg_dict['start'])
#            print('end time',msg_dict['end'])
#
#            import numpy
#            tx_diff = numpy.diff(numpy.array(msg_dict['times'][1:])) # we skip the first sample as it might have been delayed/skipped by the startup anyhow not to influence the results
#            avg_sample = float(numpy.average(tx_diff))
#            print('avg_sample',avg_sample)
#            sampling_interval = int(round(avg_sample))
#            print('sampling_interval',sampling_interval)


            # Assert
            assert msg.HasField('org_id')
            assert msg.HasField('machine_id')

            # INVARIANTS

            #
            #// - roast_id is mandatory
            #//   HasField(roast_id)
            assert msg.HasField('roast_id')

            #// - all indices of the given milestones are valid and strict monotonic
            #//   milestone_idicies = [
            #//      milestones.charge_idx,
            #//      milestones.dry_end_idx,
            #//      milestones.first_crack_start_idx,
            #//      milestones.first_crack_end_idx,
            #//      milestones.second_crack_start_idx,
            #//      milestones.second_crack_end_idx,
            #//      milestones.drop_idx
            #//   ]
            #//   for i, idx in enumerate(milestone_idicies):
            #//     if hasValue(idx):
            #//         0 <= idx < len(times) and
            #//         for 0 <= j < i:
            #//         if hasValue(milestone_idicies[j]
            #//            milestone_idicies[j] < idx
            if msg.HasField('milestones'):
                milestone_indicies = [
                    'charge_idx',
                    'dry_end_idx',
                    'first_crack_start_idx',
                    'first_crack_end_idx',
                    'second_crack_start_idx',
                    'second_crack_end_idx',
                    'drop_idx'
                ]
                for i, idx in enumerate(milestone_indicies):
                    if idx in msg_dict['milestones']:
                        assert 0 <= msg_dict['milestones'][idx] < len(msg.times)
                        for j in range(i):
                            if milestone_indicies[j] in msg_dict['milestones']:
                                assert msg_dict['milestones'][milestone_indicies[j]] < msg_dict['milestones'][idx]

            #// - all annotations are well defined and valid
            #//   len(annotations.time_indices) == len(annotations.tags) and
            #//   for idx in annotations.time_indices: 0 <= idx < len(times)
            if msg.HasField('annotations'):
                assert len(msg.annotations.time_indices) == len(msg.annotations.tags)
                for ind in msg.annotations.time_indices:
                    assert 0 <= ind <= len(msg.times)

            #// - all events are well defined, valid and event values are positive
            #//   for events:
            #//       len(events.time_indices) == len(events.values) and
            #//       for idx in events.time_indices:
            #//          0 <= idx <= len(times)
            #//       for v in events.values:
            #//          v >= 0
            for event in msg.events:
                assert len(event.time_indices) == len(event.values)
                for ind in event.time_indices:
                    assert 0 <= ind <= len(msg.times)
                for value in event.values:
                    assert value >= 0

            #// - all readings are valid
            #//   for readings in {
            #//          bt_values, et_values,
            #//          bt_ror_values, et_ror_values}:
            #//      len(readings) <= len(times)
            #//   for curve in additional_curves:
            #//       len(curve.values) <= len(times)
            assert len(msg.bt_values) <= len(msg.times)
            assert len(msg.et_values) <= len(msg.times)
            assert len(msg.bt_ror_values) <= len(msg.times)
            assert len(msg.et_ror_values) <= len(msg.times)
            for curve in msg.additional_curves:
                assert len(curve.values) <= len(msg.times)

            #// - time is monotonic
            #//   for i in range(0,len(times)):
            #//      for 0 <= j < i:
            #//         times[j] <= times[i]
            assert all(x<=y for x, y in zip(msg.times, msg.times[1:], strict=False))

            #// - time of CHARGE (start of roast)
            #//   if HasField(milestones) and HasField(milestones.charge_idx):
            #//      times[milestones.charge_idx] == 0
            #//   elif len(times)>0:
            #//      times[0] = 0
            #//   NOTE: time[x]=0 corresponds to timestamp 'start'
            if msg.HasField('milestones') and msg.milestones.HasField('charge_idx'):
                assert msg.times[msg.milestones.charge_idx] == 0
            elif len(msg.times)>0:
                assert msg.times[0] == 0

            #// - multiplication factor is >0 (defaults to 1 if not given)
            #//   if HasField(factor):
            #//      factor > 0
            if msg.HasField('factor'):
                assert msg.factor > 0
