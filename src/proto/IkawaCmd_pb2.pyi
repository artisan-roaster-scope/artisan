from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union, Any as _Any

DESCRIPTOR: _descriptor.FileDescriptor

class CmdProfileSet(_message.Message):
    __slots__ = ["profile"]
    PROFILE_FIELD_NUMBER: _ClassVar[int]
    profile: RoastProfile
    def __init__(self, profile: _Optional[_Union[RoastProfile, _Mapping[_Any,_Any]]] = ...) -> None: ...

class CmdSettingGet(_message.Message):
    __slots__ = ["field"]
    FIELD_FIELD_NUMBER: _ClassVar[int]
    field: int
    def __init__(self, field: _Optional[int] = ...) -> None: ...

class FanPoint(_message.Message):
    __slots__ = ["power", "time"]
    POWER_FIELD_NUMBER: _ClassVar[int]
    TIME_FIELD_NUMBER: _ClassVar[int]
    power: int
    time: int
    def __init__(self, time: _Optional[int] = ..., power: _Optional[int] = ...) -> None: ...

class IkawaResponse(_message.Message):
    __slots__ = ["resp", "resp_bootloader_get_version", "resp_hist_get_total_roast_count", "resp_mach_id", "resp_mach_prop_get_support_info", "resp_mach_prop_type", "resp_mach_status_get_all", "resp_mach_status_get_error", "resp_profile_get", "resp_setting_get", "seq"]
    class Resp(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = [] # type: ignore
    A: IkawaResponse.Resp
    BOOTLOADER_GET_VERSION: IkawaResponse.Resp
    HIST_GET_PROFILE_ROAST_COUNT: IkawaResponse.Resp
    HIST_GET_TOTAL_ROAST_COUNT: IkawaResponse.Resp
    MACH_ID: IkawaResponse.Resp
    MACH_PROP_GET_NAME: IkawaResponse.Resp
    MACH_PROP_GET_SUPPORT_INFO: IkawaResponse.Resp
    MACH_PROP_TYPE: IkawaResponse.Resp
    MACH_STATUS_GET_ALL: IkawaResponse.Resp
    MACH_STATUS_GET_ERROR: IkawaResponse.Resp
    MACH_STATUS_GET_SENSORS: IkawaResponse.Resp
    MACH_STATUS_GET_TIME: IkawaResponse.Resp
    PROFILE_GET: IkawaResponse.Resp
    RESP_BOOTLOADER_GET_VERSION_FIELD_NUMBER: _ClassVar[int]
    RESP_FIELD_NUMBER: _ClassVar[int]
    RESP_HIST_GET_TOTAL_ROAST_COUNT_FIELD_NUMBER: _ClassVar[int]
    RESP_MACH_ID_FIELD_NUMBER: _ClassVar[int]
    RESP_MACH_PROP_GET_SUPPORT_INFO_FIELD_NUMBER: _ClassVar[int]
    RESP_MACH_PROP_TYPE_FIELD_NUMBER: _ClassVar[int]
    RESP_MACH_STATUS_GET_ALL_FIELD_NUMBER: _ClassVar[int]
    RESP_MACH_STATUS_GET_ERROR_FIELD_NUMBER: _ClassVar[int]
    RESP_PROFILE_GET_FIELD_NUMBER: _ClassVar[int]
    RESP_SETTING_GET_FIELD_NUMBER: _ClassVar[int]
    ROAST_SUMMARY_GET: IkawaResponse.Resp
    SEQ_FIELD_NUMBER: _ClassVar[int]
    SETTING_GET: IkawaResponse.Resp
    SETTING_GET_INFO: IkawaResponse.Resp
    SETTING_GET_LIST: IkawaResponse.Resp
    TEST_STATUS_GET: IkawaResponse.Resp
    UNKNOWN: IkawaResponse.Resp
    resp: IkawaResponse.Resp
    resp_bootloader_get_version: RespBootloaderGetVersion
    resp_hist_get_total_roast_count: RespHistGetTotalRoastCount
    resp_mach_id: RespMachPropGetID
    resp_mach_prop_get_support_info: RespMachPropGetSupportInfo
    resp_mach_prop_type: RespMachPropGetType
    resp_mach_status_get_all: RespMachStatusGetAll
    resp_mach_status_get_error: RespMachStatusGetError
    resp_profile_get: RespProfileGet
    resp_setting_get: RespSettingGet
    seq: int
    def __init__(self, seq: _Optional[int] = ..., resp: _Optional[_Union[IkawaResponse.Resp, str]] = ..., resp_bootloader_get_version: _Optional[_Union[RespBootloaderGetVersion, _Mapping[_Any,_Any]]] = ..., resp_mach_prop_type: _Optional[_Union[RespMachPropGetType, _Mapping[_Any,_Any]]] = ..., resp_mach_id: _Optional[_Union[RespMachPropGetID, _Mapping[_Any,_Any]]] = ..., resp_mach_status_get_error: _Optional[_Union[RespMachStatusGetError, _Mapping[_Any,_Any]]] = ..., resp_mach_status_get_all: _Optional[_Union[RespMachStatusGetAll, _Mapping[_Any,_Any]]] = ..., resp_hist_get_total_roast_count: _Optional[_Union[RespHistGetTotalRoastCount, _Mapping[_Any,_Any]]] = ..., resp_profile_get: _Optional[_Union[RespProfileGet, _Mapping[_Any,_Any]]] = ..., resp_setting_get: _Optional[_Union[RespSettingGet, _Mapping[_Any,_Any]]] = ..., resp_mach_prop_get_support_info: _Optional[_Union[RespMachPropGetSupportInfo, _Mapping[_Any,_Any]]] = ...) -> None: ...

class Message(_message.Message):
    __slots__ = ["cmd_type", "profile_set", "seq", "setting_get"]
    CMD_TYPE_FIELD_NUMBER: _ClassVar[int]
    PROFILE_SET_FIELD_NUMBER: _ClassVar[int]
    SEQ_FIELD_NUMBER: _ClassVar[int]
    SETTING_GET_FIELD_NUMBER: _ClassVar[int]
    cmd_type: int
    profile_set: CmdProfileSet
    seq: int
    setting_get: CmdSettingGet
    def __init__(self, cmd_type: _Optional[int] = ..., seq: _Optional[int] = ..., profile_set: _Optional[_Union[CmdProfileSet, _Mapping[_Any,_Any]]] = ..., setting_get: _Optional[_Union[CmdSettingGet, _Mapping[_Any,_Any]]] = ...) -> None: ...

class RespBootloaderGetVersion(_message.Message):
    __slots__ = ["revision", "version"]
    REVISION_FIELD_NUMBER: _ClassVar[int]
    VERSION_FIELD_NUMBER: _ClassVar[int]
    revision: str
    version: int
    def __init__(self, version: _Optional[int] = ..., revision: _Optional[str] = ...) -> None: ...

class RespHistGetTotalRoastCount(_message.Message):
    __slots__ = ["total_roast_count"]
    TOTAL_ROAST_COUNT_FIELD_NUMBER: _ClassVar[int]
    total_roast_count: int
    def __init__(self, total_roast_count: _Optional[int] = ...) -> None: ...

class RespMachPropGetID(_message.Message):
    __slots__ = ["id_"]
    ID__FIELD_NUMBER: _ClassVar[int]
    id_: int
    def __init__(self, id_: _Optional[int] = ...) -> None: ...

class RespMachPropGetSupportInfo(_message.Message):
    __slots__ = ["profile_schema"]
    PROFILE_SCHEMA_FIELD_NUMBER: _ClassVar[int]
    profile_schema: int
    def __init__(self, profile_schema: _Optional[int] = ...) -> None: ...

class RespMachPropGetType(_message.Message):
    __slots__ = ["type_", "variant"]
    TYPE__FIELD_NUMBER: _ClassVar[int]
    VARIANT_FIELD_NUMBER: _ClassVar[int]
    type_: int
    variant: int
    def __init__(self, type_: _Optional[int] = ..., variant: _Optional[int] = ...) -> None: ...

class RespMachStatusGetAll(_message.Message):
    __slots__ = ["board_temp", "d", "fan", "fan_d", "fan_i", "fan_measured", "fan_p", "fan_power", "fan_rpm_measured", "fan_rpm_setpoint", "heater", "i", "j", "p", "pid_sensor", "relay_state", "ror_above", "ror_below", "setpoint", "state", "temp_above", "temp_above_filtered", "temp_below", "temp_below_filtered", "time"]
    BOARD_TEMP_FIELD_NUMBER: _ClassVar[int]
    D_FIELD_NUMBER: _ClassVar[int]
    FAN_D_FIELD_NUMBER: _ClassVar[int]
    FAN_FIELD_NUMBER: _ClassVar[int]
    FAN_I_FIELD_NUMBER: _ClassVar[int]
    FAN_MEASURED_FIELD_NUMBER: _ClassVar[int]
    FAN_POWER_FIELD_NUMBER: _ClassVar[int]
    FAN_P_FIELD_NUMBER: _ClassVar[int]
    FAN_RPM_MEASURED_FIELD_NUMBER: _ClassVar[int]
    FAN_RPM_SETPOINT_FIELD_NUMBER: _ClassVar[int]
    HEATER_FIELD_NUMBER: _ClassVar[int]
    I_FIELD_NUMBER: _ClassVar[int]
    J_FIELD_NUMBER: _ClassVar[int]
    PID_SENSOR_FIELD_NUMBER: _ClassVar[int]
    P_FIELD_NUMBER: _ClassVar[int]
    RELAY_STATE_FIELD_NUMBER: _ClassVar[int]
    ROR_ABOVE_FIELD_NUMBER: _ClassVar[int]
    ROR_BELOW_FIELD_NUMBER: _ClassVar[int]
    SETPOINT_FIELD_NUMBER: _ClassVar[int]
    STATE_FIELD_NUMBER: _ClassVar[int]
    TEMP_ABOVE_FIELD_NUMBER: _ClassVar[int]
    TEMP_ABOVE_FILTERED_FIELD_NUMBER: _ClassVar[int]
    TEMP_BELOW_FIELD_NUMBER: _ClassVar[int]
    TEMP_BELOW_FILTERED_FIELD_NUMBER: _ClassVar[int]
    TIME_FIELD_NUMBER: _ClassVar[int]
    board_temp: int
    d: int
    fan: int
    fan_d: int
    fan_i: int
    fan_measured: int
    fan_p: int
    fan_power: int
    fan_rpm_measured: int
    fan_rpm_setpoint: int
    heater: int
    i: int
    j: int
    p: int
    pid_sensor: int
    relay_state: int
    ror_above: int
    ror_below: int
    setpoint: int
    state: int
    temp_above: int
    temp_above_filtered: int
    temp_below: int
    temp_below_filtered: int
    time: int
    def __init__(self, time: _Optional[int] = ..., temp_above: _Optional[int] = ..., fan: _Optional[int] = ..., state: _Optional[int] = ..., heater: _Optional[int] = ..., p: _Optional[int] = ..., i: _Optional[int] = ..., d: _Optional[int] = ..., setpoint: _Optional[int] = ..., fan_measured: _Optional[int] = ..., board_temp: _Optional[int] = ..., temp_below: _Optional[int] = ..., fan_rpm_measured: _Optional[int] = ..., fan_rpm_setpoint: _Optional[int] = ..., fan_i: _Optional[int] = ..., fan_p: _Optional[int] = ..., fan_d: _Optional[int] = ..., fan_power: _Optional[int] = ..., j: _Optional[int] = ..., relay_state: _Optional[int] = ..., pid_sensor: _Optional[int] = ..., temp_above_filtered: _Optional[int] = ..., temp_below_filtered: _Optional[int] = ..., ror_above: _Optional[int] = ..., ror_below: _Optional[int] = ...) -> None: ...

class RespMachStatusGetError(_message.Message):
    __slots__ = ["error"]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    error: int
    def __init__(self, error: _Optional[int] = ...) -> None: ...

class RespProfileGet(_message.Message):
    __slots__ = ["profile"]
    PROFILE_FIELD_NUMBER: _ClassVar[int]
    profile: RoastProfile
    def __init__(self, profile: _Optional[_Union[RoastProfile, _Mapping[_Any,_Any]]] = ...) -> None: ...

class RespSettingGet(_message.Message):
    __slots__ = ["field", "value"]
    FIELD_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    field: int
    value: int
    def __init__(self, field: _Optional[int] = ..., value: _Optional[int] = ...) -> None: ...

class RoastProfile(_message.Message):
    __slots__ = ["coffee_id", "coffee_name", "coffee_web_url", "cooldown_fan", "fan_points", "id", "name", "profile_type", "schema", "temp_points", "temp_sensor", "user_id"]
    COFFEE_ID_FIELD_NUMBER: _ClassVar[int]
    COFFEE_NAME_FIELD_NUMBER: _ClassVar[int]
    COFFEE_WEB_URL_FIELD_NUMBER: _ClassVar[int]
    COOLDOWN_FAN_FIELD_NUMBER: _ClassVar[int]
    FAN_POINTS_FIELD_NUMBER: _ClassVar[int]
    ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    PROFILE_TYPE_FIELD_NUMBER: _ClassVar[int]
    SCHEMA_FIELD_NUMBER: _ClassVar[int]
    TEMP_POINTS_FIELD_NUMBER: _ClassVar[int]
    TEMP_SENSOR_FIELD_NUMBER: _ClassVar[int]
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    coffee_id: str
    coffee_name: str
    coffee_web_url: str
    cooldown_fan: FanPoint
    fan_points: _containers.RepeatedCompositeFieldContainer[FanPoint]
    id: bytes
    name: str
    profile_type: str
    schema: int
    temp_points: _containers.RepeatedCompositeFieldContainer[TempPoint]
    temp_sensor: int
    user_id: str
    def __init__(self, schema: _Optional[int] = ..., id: _Optional[bytes] = ..., name: _Optional[str] = ..., temp_points: _Optional[_Iterable[_Union[TempPoint, _Mapping[_Any,_Any]]]] = ..., fan_points: _Optional[_Iterable[_Union[FanPoint, _Mapping[_Any,_Any]]]] = ..., temp_sensor: _Optional[int] = ..., cooldown_fan: _Optional[_Union[FanPoint, _Mapping[_Any,_Any]]] = ..., coffee_name: _Optional[str] = ..., user_id: _Optional[str] = ..., coffee_id: _Optional[str] = ..., coffee_web_url: _Optional[str] = ..., profile_type: _Optional[str] = ...) -> None: ...

class TempPoint(_message.Message):
    __slots__ = ["temp", "time"]
    TEMP_FIELD_NUMBER: _ClassVar[int]
    TIME_FIELD_NUMBER: _ClassVar[int]
    temp: int
    time: int
    def __init__(self, time: _Optional[int] = ..., temp: _Optional[int] = ...) -> None: ...
