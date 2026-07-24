from pathlib import Path
from typing import cast, TypedDict, TYPE_CHECKING

if TYPE_CHECKING:
    from _pytest.python import Metafunc

# Import the atypes module directly without aggressive mocking
# The atypes module only contains type definitions and doesn't need runtime mocking
from artisanlib import atypes
from artisanlib.util import deserialize, roast_message, stringfromseconds

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
        #print(profile_data)

        msg = roast_message(profile_data, org_id = 'org1', machine_id = 'machine1',
                interpolate_drops=True,
                smooth_curves=True,
                add_additional_curves=1,
                rate_of_rise=1,
                min_sampling_interval=1,
#                seconds_before_charge=None,
#                seconds_after_drop=None,
                factor=10)

        if msg is not None:

            from google.protobuf.json_format import MessageToDict,MessageToJson
            msg_dict = MessageToDict(msg, preserving_proto_field_name=True)

    #        print(msg_dict)
    #        from google.protobuf import json_format
    #        print(json_format.MessageToJson(msg, preserving_proto_field_name=True))
    #        print(msg.HasField("org_id"))
    #        print("msg_dict",msg_dict)

            print('---')
            print(f"{alog_file['filename']}.alog")
            print('#readings',len(msg_dict['times']))
            msg_json = MessageToJson(msg, preserving_proto_field_name=True)
            print('dict size',len(msg_json)/1024)
            import zlib
            print('dict compressed', len(zlib.compress(msg_json.encode('utf-8')))/1024)
            print('proto size',len(msg.SerializeToString())/1024)
            print('proto compressed',len(zlib.compress(msg.SerializeToString()))/1024)
            print('total time', stringfromseconds(msg_dict['times'][-1] - msg_dict['times'][0]))
            print('sample time', msg_dict['times'][1]- msg_dict['times'][0])
            print('start time',msg_dict['start'])
            print('end time',msg_dict['end'])

            import numpy
            tx_diff = numpy.diff(numpy.array(msg_dict['times'][1:])) # we skip the first sample as it might have been delayed/skipped by the startup anyhow not to influence the results
            avg_sample = float(numpy.average(tx_diff))
            print('avg_sample',avg_sample)
            sampling_interval = int(round(avg_sample))
            print('sampling_interval',sampling_interval)


            # making payload smaller
            # + don't include hidden extra curves
            #   flag to disable extra curves and flag to show all extra curves (or one parameter extra_curves 0:none, 1:visible, 2, all)
            # + no RoR (or only BT RoR)
            #   => turn this into an integer setting
            #
            # + less/no data before/after CHARGE/DROP (after DROP automated by upload moment, before CHARGE depends on use)
            #   setting to remove data before/after (30s before and 30s after)
            #
            # + resample: reduce/increase sampling interval to 1 or 2sec andn transport as sInt32
            #
            # + use int32 with factor 10
            #   even better use sInt32 to more efficiently encode -1!! (-1 in int32 takes 10 bytes)
            #     always use sInt32 if negative numbers can occur, if only positive, use Int32
            #     avoid float as it is fixed length
            #       sInt32: (only for FREQUENT negative numbers!)
            #          . Annotations.time_indices
            #          . all Milestones integers
            #          . Events.time_indices
            #          . Events.values
            #      Curve.temperatures factor 100
            #
            #     expected value range: -1 < x < 820C (Aferburner temp); mostly max 220C
            #     expected value range *100: -1 < x < 82.000; mostly max 22.000
            #     https://mousemelon.dev/documentation/protocol-buffers/number-types
            #     float: 4 bytes per reading
            #     int32:
            #          x < 0           : 10 bytes         <= a problem for error values -1
            #          0 < x < 128     :  1 byte (2^7)
            #          0 < x < 16384   :  2 bytes (2^14)  <= RoR and temp < 163C (1/100) or all temp (1/10)
            #          0 < x < 2097152 :  3 bytes (2^21)
            #     sint32:
            #          x == -1         :  1 bytes
            #          0 < x < 64      :  1 byte (2^6)
            #          0 < x < 8192    :  2 bytes (2^13)  <= all of RoR and temp < 81.9C (1/100) or all temp (1/10)
            #          0 < x < 1048576 :  3 bytes (2^20)
            #     => factor 1/10 would save one more byte per reading
            #     => 2 bytes per time in seconds has small negatives and is up to 900 (15min)
            #
            # - send roastID also in header (plus does not need to touch/extract payload at all)!
            #
            #-----
            # + invert bool to mostly contain false (dropped default)
            # - still use compression on data transmission!



    # => : sint32 factor 10 for readings
    # ==> : resample + sint32 for timex
    # ===> : max 30sec before/after CHARGE/DROP
    # =====> : factor 100 instead of 10


    #---------- include preheat:

            # profile1.alog (10:17/29min, 1sec, +12/4, 1735 => 677 readings)
            # >> Guji Shakiso
            # 30.5.2025 17:32 => 17:45 / 17:55:17
            # with 2xRoR, all extras
            #    dict size: 414,9k
            #    dict compressed: 72,2k
            #    proto size: 180,7k
            #    proto compressed: 64,7k
            # with 1xRoR, visible extras
            #    dict size: 196,6k => 159k ==> 153,9k ===> 60,4k
            #    dict compressed: 36,5k => 19,2k ==> 18,7k ===> 8,1k
            #    proto size: 54,4k => 28,4k ==> 24,9k ===> 9,9k
            #    proto compressed: 33k => 13,5k ==> 13,3k ===> 5,6k
            # without RoR, no extras
            #    dict size: 67,7k => 55k
            #    dict compressed: 16,7k => 10.3k
            #    proto size: 20,4k => 13.6k
            #    proto compressed: 14,4k => 7.4k

    #---------- standard:

            # profile2.alog (12:15/13:15, 5sec, +10/0, 167 => 157 readings)
            # >> Peru
            # 10.8.2015 14:25 => 14:25:15 / 14:37:30
            # with 2xRoR, all extras
            #    dict size: 36,6k
            #    dict compressed: 8.9k
            #    proto size: 9.4k
            #    proto compressed: 6.8k
            # with 1xRoR, visible extras
            #    dict size: 9k => 7,2k ==> 6,6k ===> 6,2k
            #    dict compressed: 2.8k => 1,8k ==> 1,5k ===> 1,5k
            #    proto size: 2.7k => 1,6k ==> 1,3k ===> 1,2k
            #    proto compressed: 2.2k => 1,4k ==> 1,1k ===> 1k
            # without RoR, no extras
            #    dict size: 7.4k => 5.8k
            #    dict compressed: 2.4k => 1.6k
            #    proto size: 2k => 1.4k
            #    proto compressed: 1.8k => 1.3k

            # profile3.alog (8:45/10:35, 1sec, +8/2, 636 => 562 readings)
            # >> Brazil 2024, Sousa Alvarenga - Brazil (SO)
            # 10.3.2025, 10:03 => 10:04:44 / 10:13:30
            # with 2xRoR, all extras
            #    dict size: 112.9k
            #    dict compressed: 13.6k
            #    proto size: 32.5k
            #    proto compressed: 11.8k
            # with 1xRoR, visible extras
            #    dict size: 50k => 44k ==> 41k ===> 37,5k
            #    dict compressed: 9,7k => 7,1k ==> 6,9k ===> 6,6k
            #    proto size: 15k => 8,6k ==> 7,3k ===> 6,6k
            #    proto compressed: 8,5k => 5,2k ==> 4,8k ===> 4,5k
            # without RoR, no extras
            #    dict size: 23.2k => 21k
            #    dict compressed: 4.7k => 4.3k
            #    proto size: 7.5k => 5k
            #    proto compressed: 4.1k => 3.2k

            # profile4.alog (10:30/10:31, 2sec, +0, 316 readings)
            # >> Guatemala Candelaria
            # 8.4.2020 22:10 => 22:10:02 / 22:20:32
            # with 2xRoR, all extras
            #    dict size: 20.5k
            #    dict compressed: 5.4k
            #    proto size: 6.2k
            #    proto compressed: 4.5k
            # with 1xRoR, visible extras
            #    dict size: 17.4k  ==> 12,4k
            #    dict compressed: 4.9k ==> 2,7k
            #    proto size: 5k ==> 2,5k
            #    proto compressed: 3.9k ==> 2k
            # without RoR, no extras
            #    dict size: 14.2k
            #    dict compressed: 4.2k
            #    proto size: 3.8k
            #    proto compressed: 3.1k

            # profile5.alog (10:58/11:24, 1sec, +12/3, 1123 => 715 readings)
            # >> Custom Blend
            # 2.3.2024 18:26 => 18:26:26 / 18:37
            # with 2xRoR, all extras
            #    dict size: 234,6k
            #    dict compressed: 47,9k
            #    proto size: 61,6k
            #    proto compressed: 39,5k
            # with 1xRoR, visible extras
            #    dict size: 91,8k ==> 71k ===> 46k (49,3k/100; 46,8k/20; 42,5k/1)
            #    dict compressed: 20,9k ==> 12,2k ===> 8k (11k/100; 9,2k/20; 3,6k/1)
            #    proto size: 26,4k ==> 12,6k ===> 8,3k (11k/100; 8,3k/20; 7,8k/1)
            #    proto compressed: 18,6k ==> 8,2k ===> 5,5k (8,5k/100;6,3k/20; 2,6k/1)
            # without RoR, no extras
            #    dict size: 43,6k => 35,2k
            #    dict compressed: 11,4k => 7k
            #    proto size: 13,2k => 8,9k
            #    proto compressed: 9,6k => 5k

            # profile6.alog (12:36/14:00, 5sec, +8/2, 265 readings)
            # >> Guatemala Jaguar B04
            # 20.10.2023 21:20 => 21:20:15 / 21:32:51
            # with 2xRoR, all extras
            #    dict size: 51k
            #    dict compressed: 9.2k
            #    proto size: 13.7k
            #    proto compressed: 6.3k
            # with 1xRoR, visible extras
            #    dict size: 24.5k ==> 17,9k ==> 18,5k
            #    dict compressed: 6.9k ==> 3,6k ==> 3,7k
            #    proto size: 6.4k ==> 3,2k ===> 3,2k
            #    proto compressed: 4,5k ==> 2k ==> 2k
            # without RoR, no extras
            #    dict size: 12.1k
            #    dict compressed: 3.9k
            #    proto size: 3.3k
            #    proto compressed: 2.9k

            # profile7.alog (5:46/8:20, 0.5sec, +18/0, 991 => 377 readings)
            # >> Guatemala, Tzikin Huehuetenango FW
            # 22.12.2025 17:39 => 17:40:14 / 17:46:00
            # with 2xRoR, all extras
            #    dict size: 300,5k
            #    dict compressed: 48,8k
            #    proto size: 77,8k
            #    proto compressed: 42k
            # with 1xRoR, visible extras
            #    dict size: 51.7k ==> 18,4k ===> 14,5k
            #    dict compressed: 13,6k ==> 3,7k ===> 3k
            #    proto size: 15.6k ==> 3,5k ===> 2,8k
            #    proto compressed: 10.8k ==> 2,6k ===> 2,1k
            # without RoR, no extras
            #    dict size: 41.7k
            #    dict compressed: 11.8k
            #    proto size: 11.7k
            #    proto compressed: 9k


#            print("back profile",roast_message_to_profile(msg))

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
