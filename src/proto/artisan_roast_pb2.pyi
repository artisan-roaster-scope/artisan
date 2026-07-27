import datetime

from google.protobuf import timestamp_pb2 as _timestamp_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union, Any as _Any

DESCRIPTOR: _descriptor.FileDescriptor

class Roast(_message.Message):
    __slots__ = ("org_id", "machine_id", "roast_id", "start", "end", "times", "milestones", "annotations", "events", "bt_values", "et_values", "bt_ror_values", "et_ror_values", "additional_curves", "factor")
    class Milestones(_message.Message):
        __slots__ = ("charge_idx", "dry_end_idx", "first_crack_start_idx", "first_crack_end_idx", "second_crack_start_idx", "second_crack_end_idx", "drop_idx")
        CHARGE_IDX_FIELD_NUMBER: _ClassVar[int]
        DRY_END_IDX_FIELD_NUMBER: _ClassVar[int]
        FIRST_CRACK_START_IDX_FIELD_NUMBER: _ClassVar[int]
        FIRST_CRACK_END_IDX_FIELD_NUMBER: _ClassVar[int]
        SECOND_CRACK_START_IDX_FIELD_NUMBER: _ClassVar[int]
        SECOND_CRACK_END_IDX_FIELD_NUMBER: _ClassVar[int]
        DROP_IDX_FIELD_NUMBER: _ClassVar[int]
        charge_idx: int
        dry_end_idx: int
        first_crack_start_idx: int
        first_crack_end_idx: int
        second_crack_start_idx: int
        second_crack_end_idx: int
        drop_idx: int
        def __init__(self, charge_idx: _Optional[int] = ..., dry_end_idx: _Optional[int] = ..., first_crack_start_idx: _Optional[int] = ..., first_crack_end_idx: _Optional[int] = ..., second_crack_start_idx: _Optional[int] = ..., second_crack_end_idx: _Optional[int] = ..., drop_idx: _Optional[int] = ...) -> None: ...
    class Annotations(_message.Message):
        __slots__ = ("time_indices", "tags")
        TIME_INDICES_FIELD_NUMBER: _ClassVar[int]
        TAGS_FIELD_NUMBER: _ClassVar[int]
        time_indices: _containers.RepeatedScalarFieldContainer[int]
        tags: _containers.RepeatedScalarFieldContainer[str]
        def __init__(self, time_indices: _Optional[_Iterable[int]] = ..., tags: _Optional[_Iterable[str]] = ...) -> None: ...
    class Events(_message.Message):
        __slots__ = ("name", "unit", "time_indices", "values")
        NAME_FIELD_NUMBER: _ClassVar[int]
        UNIT_FIELD_NUMBER: _ClassVar[int]
        TIME_INDICES_FIELD_NUMBER: _ClassVar[int]
        VALUES_FIELD_NUMBER: _ClassVar[int]
        name: str
        unit: str
        time_indices: _containers.RepeatedScalarFieldContainer[int]
        values: _containers.RepeatedScalarFieldContainer[int]
        def __init__(self, name: _Optional[str] = ..., unit: _Optional[str] = ..., time_indices: _Optional[_Iterable[int]] = ..., values: _Optional[_Iterable[int]] = ...) -> None: ...
    class Curve(_message.Message):
        __slots__ = ("name", "values", "temperatures")
        NAME_FIELD_NUMBER: _ClassVar[int]
        VALUES_FIELD_NUMBER: _ClassVar[int]
        TEMPERATURES_FIELD_NUMBER: _ClassVar[int]
        name: str
        values: _containers.RepeatedScalarFieldContainer[int]
        temperatures: bool
        def __init__(self, name: _Optional[str] = ..., values: _Optional[_Iterable[int]] = ..., temperatures: _Optional[bool] = ...) -> None: ...
    ORG_ID_FIELD_NUMBER: _ClassVar[int]
    MACHINE_ID_FIELD_NUMBER: _ClassVar[int]
    ROAST_ID_FIELD_NUMBER: _ClassVar[int]
    START_FIELD_NUMBER: _ClassVar[int]
    END_FIELD_NUMBER: _ClassVar[int]
    TIMES_FIELD_NUMBER: _ClassVar[int]
    MILESTONES_FIELD_NUMBER: _ClassVar[int]
    ANNOTATIONS_FIELD_NUMBER: _ClassVar[int]
    EVENTS_FIELD_NUMBER: _ClassVar[int]
    BT_VALUES_FIELD_NUMBER: _ClassVar[int]
    ET_VALUES_FIELD_NUMBER: _ClassVar[int]
    BT_ROR_VALUES_FIELD_NUMBER: _ClassVar[int]
    ET_ROR_VALUES_FIELD_NUMBER: _ClassVar[int]
    ADDITIONAL_CURVES_FIELD_NUMBER: _ClassVar[int]
    FACTOR_FIELD_NUMBER: _ClassVar[int]
    org_id: str
    machine_id: str
    roast_id: str
    start: _timestamp_pb2.Timestamp
    end: _timestamp_pb2.Timestamp
    times: _containers.RepeatedScalarFieldContainer[int]
    milestones: Roast.Milestones
    annotations: Roast.Annotations
    events: _containers.RepeatedCompositeFieldContainer[Roast.Events]
    bt_values: _containers.RepeatedScalarFieldContainer[int]
    et_values: _containers.RepeatedScalarFieldContainer[int]
    bt_ror_values: _containers.RepeatedScalarFieldContainer[int]
    et_ror_values: _containers.RepeatedScalarFieldContainer[int]
    additional_curves: _containers.RepeatedCompositeFieldContainer[Roast.Curve]
    factor: int
    def __init__(self, org_id: _Optional[str] = ..., machine_id: _Optional[str] = ..., roast_id: _Optional[str] = ..., start: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping[_Any,_Any]]] = ..., end: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping[_Any,_Any]]] = ..., times: _Optional[_Iterable[int]] = ..., milestones: _Optional[_Union[Roast.Milestones, _Mapping[_Any,_Any]]] = ..., annotations: _Optional[_Union[Roast.Annotations, _Mapping[_Any,_Any]]] = ..., events: _Optional[_Iterable[_Union[Roast.Events, _Mapping[_Any,_Any]]]] = ..., bt_values: _Optional[_Iterable[int]] = ..., et_values: _Optional[_Iterable[int]] = ..., bt_ror_values: _Optional[_Iterable[int]] = ..., et_ror_values: _Optional[_Iterable[int]] = ..., additional_curves: _Optional[_Iterable[_Union[Roast.Curve, _Mapping[_Any,_Any]]]] = ..., factor: _Optional[int] = ...) -> None: ...
