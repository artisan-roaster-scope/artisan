#
# ABOUT
# Kaleido CSV roast profile importer for Artisan

import csv
import re
import logging
from collections.abc import Callable
from typing import Final

from artisanlib.util import encodeLocal, weight_units, weight_units_lower
from artisanlib.atypes import ProfileData

_log: Final[logging.Logger] = logging.getLogger(__name__)


# returns a dict containing all profile information contained in the given Kaleido CSV file
def extractProfileKaleidoCSV(file: str,
        _etypesdefault: list[str],
        alt_etypesdefault: list[str],
        _artisanflavordefaultlabels: list[str],
        eventsExternal2InternalValue: Callable[[int], float]) -> ProfileData:
    res: ProfileData = ProfileData()  # the interpreted data set

    # 初始化数据列表
    timex = []  # 时间轴
    temp1 = []  # ET (环境温度)
    temp2 = []  # BT (豆温)
    temp3 = []  # RoR (升温率)

    specialevents = []        # 特殊事件时间点
    specialeventstype = []    # 事件类型 (0=Fan, 1=Drum, 2=Damper, 3=Burner)
    specialeventsvalue = []   # 事件数值
    specialeventsStrings = [] # 事件描述

    timeindex = [-1, 0, 0, 0, 0, 0, 0, 0]  # 时间索引: [CHARGE, DRY END, FC START, FC END, SC START, SC END, DROP, COOL]
                                            # CHARGE index init set to -1 as 0 could be an actual index used

    # 解析 Kaleido CSV 文件（Kaleido文件是文本格式，包含多个部分）
    with open(file, encoding='utf-8') as f:
        content = f.read()

    # 分割文件内容到不同部分
    sections = {}
    current_section = None
    lines = content.split('\n')

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # 检查是否是 section 标记，如 [{DATA}], [{EVENT}], [{CookDate}] 等
        if line.startswith('[{') and line.endswith('}]'):
            current_section = line[2:-2]  # 去掉 [{ 和 }]
            sections[current_section] = []
            i += 1
            continue

        # 如果当前在某个 section 内，收集内容
        if current_section and line:
            sections[current_section].append(line)

        i += 1

    # 解析基本信息
    # 解析烘焙日期和时间
    if 'CookDate' in sections and sections['CookDate']:
        cook_date = sections['CookDate'][0].strip() if sections['CookDate'] else ''
        if cook_date:
            # 格式: 25-05-18 19:32:48
            try:
                date_part, time_part = cook_date.split(' ')
                year = f"20{date_part[:2]}"
                month = date_part[3:5]
                day = date_part[6:8]
                res['roastdate'] = f"{year}-{month}-{day}"
                res['roastisodate'] = f"{year}-{month}-{day}"
                res['roasttime'] = time_part
            except:
                _log.warning('Could not parse CookDate: %s', cook_date)

    # 解析评论/标题
    if 'Comment' in sections and sections['Comment']:
        comment = sections['Comment'][0].strip() if sections['Comment'] else ''
        if comment:
            res['title'] = comment

    # 解析预热温度
    if 'PreTemp' in sections and sections['PreTemp']:
        pre_temp = sections['PreTemp'][0].strip() if sections['PreTemp'] else ''
        if pre_temp:
            try:
                res['drumtemp'] = float(pre_temp)  # 使用预热温度作为初始鼓温
            except ValueError:
                pass

    # Parse DATA section
    if 'DATA' in sections:
        data_lines = sections['DATA']

        # First line is header
        if data_lines:
            headers = [h.strip() for h in data_lines[0].split(',')]

            # Store previous parameter values to detect changes
            last_fan = None      # Corresponds to SM (Fan/Air) -> Fan (index 0)
            last_drum = None     # Corresponds to RL (Rotation) -> Drum (index 1)
            last_burner = None   # Corresponds to HP (Heat Power) -> Burner (index 3)

            # Prepare lists for extra device data
            sm_list = []  # SM (Fan/Air) -> Fan %
            rl_list = []  # RL (Rotation) -> Drum %
            hp_list = []  # HP (Heat Power) -> Burner %
            sv_list = []  # SV (Set Value) -> Set Value
            # hpm_list = [] # HPM (Manual/Auto mode) -> Mode (not displayed in Roast Properties Data)
            # ps_list = []  # PS (Status) -> Status (not displayed in Roast Properties Data)

            for idx, line in enumerate(data_lines[1:]):  # 跳过标题行
                line = line.strip()
                if line:
                    parts = line.split(',')
                    if len(parts) >= 11:  # 确保有足够的列
                        try:
                            # 解析数据列: Index,Time,BT,ET,RoR,SV,HPM,HP,SM,RL,PS
                            # Index = parts[0] (跳过)
                            time_ms = int(parts[1])      # 时间（毫秒）
                            bt = float(parts[2])         # BT (豆温)
                            et = float(parts[3])         # ET (环境温度)
                            ror = float(parts[4])        # RoR (升温率)
                            sv = float(parts[5])         # 设定值

                            hpm_str = parts[6].strip()   # HPM (手动/自动模式 - M=手动火力, A=依据SV值PID火力控制)
                            hp_str = parts[7].strip()    # HP (火力)
                            sm_str = parts[8].strip()    # SM (风门设置/Air)
                            rl_str = parts[9].strip()    # RL (转速)
                            ps_str = parts[10].strip()   # PS (状态 - O或F)

                            # 转换时间（毫秒转秒）
                            time_sec = time_ms / 1000.0

                            # 转换各参数值
                            hpm = hpm_str if hpm_str else 'M'  # 默认为手动模式
                            hp = float(hp_str) if hp_str and hp_str not in ['0', ''] else 0.0
                            sm = float(sm_str) if sm_str and sm_str not in ['0', ''] else 0.0
                            rl = float(rl_str) if rl_str and rl_str not in ['0', ''] else 0.0
                            ps = ps_str if ps_str else 'O'  # 默认为火力打开状态

                            # 添加到数据列表
                            timex.append(time_sec)
                            temp1.append(et)
                            temp2.append(bt)
                            temp3.append(ror)

                            # Add to extra device data lists
                            sm_list.append(sm)
                            rl_list.append(rl)
                            hp_list.append(hp)
                            sv_list.append(sv)
                            # HPM: M=Manual Heat (100), A=PID Heat Control based on SV value (0) - Kaleido machine mode, not displayed in Roast Properties Data
                            # hpm_numeric = 100 if hpm == 'M' else 0  
                            # hpm_list.append(hpm_numeric) - HPM data not added to extra device list
                            # PS: O=Heat On (100), C=Heat Off (0) - Kaleido machine specific, not displayed in Roast Properties Data
                            # ps_numeric = 100 if ps == 'O' else 0
                            # ps_list.append(ps_numeric) - PS data not added to extra device list

                            # Detect Fan (SM - Fan/Air) changes - Map to Artisan Fan (index 0)
                            if sm != last_fan:
                                last_fan = sm
                                specialeventsvalue.append(eventsExternal2InternalValue(int(sm)))
                                specialevents.append(idx)
                                specialeventstype.append(0)  # Fan
                                specialeventsStrings.append(f'SM={int(sm)}%')

                            # Detect Drum (RL - Rotation) changes - Map to Artisan Drum (index 1)
                            if rl != last_drum:
                                last_drum = rl
                                specialeventsvalue.append(eventsExternal2InternalValue(int(rl)))
                                specialevents.append(idx)
                                specialeventstype.append(1)  # Drum
                                specialeventsStrings.append(f'RL={int(rl)}%')

                            # Detect Burner (HP - Heat Power) changes - Map to Artisan Burner (index 3)
                            if hp != last_burner:
                                last_burner = hp
                                specialeventsvalue.append(eventsExternal2InternalValue(int(hp)))
                                specialevents.append(idx)
                                specialeventstype.append(3)  # Burner
                                specialeventsStrings.append(f'HP={int(hp)}%')

                        except (ValueError, IndexError) as e:
                            # Skip unparsable lines
                            _log.warning('Could not parse data line: %s, error: %s', line, str(e))
                            continue

            # Add extra device data - Include all Kaleido parameters except HPM and PS
            if timex:  # Ensure there is data
                res['extradevices'] = [32, 33, 44, 45]  # Device IDs, removed HPM and PS device IDs
                res['extraname1'] = ['SM', 'RL', 'HP', 'SV']  # Removed HPM and PS
                res['extraname2'] = ['Fan', 'Drum', 'Burner', 'SV']  # Removed HPM and PS
                res['extratimex'] = [timex, timex, timex, timex]  # Removed HPM and PS time axis
                res['extratemp1'] = [sm_list, rl_list, hp_list, sv_list]  # Removed HPM and PS data
                res['extratemp2'] = [[0]*len(timex), [0]*len(timex), [0]*len(timex), [0]*len(timex)]  # Removed HPM and PS data

    # Parse event timestamps and map to Artisan timeindex
    # Mapping relationship: 
    # StartBeansIn -> CHARGE (timeindex[0])
    # TurntoYellow -> DRY END (timeindex[1]) 
    # 1stBoomStart -> FC START (timeindex[2])
    # 1stBoomEnd -> FC END (timeindex[3])
    # 2ndBoomStart -> SC START (timeindex[4])
    # 2ndBoomEnd -> SC END (timeindex[5])
    # BeansColdDown -> DROP (timeindex[6])

    event2timeindex = {
        'StartBeansIn': 0,  # CHARGE
        'TurntoYellow': 1,  # DRY END
        '1stBoomStart': 2,  # FC START
        '1stBoomEnd': 3,    # FC END
        '2ndBoomStart': 4,  # SC START
        '2ndBoomEnd': 5,    # SC END
        'BeansColdDown': 6  # DROP
    }

    # Process events
    for event_name, time_idx in event2timeindex.items():
        if event_name in sections:
            event_data = sections[event_name][0] if sections[event_name] else ''
            if event_data:
                # Parse format like "170@00:00" -> temperature@time
                if '@' in event_data:
                    try:
                        time_str = event_data.split('@')[1]
                        time_parts = time_str.split(':')
                        if len(time_parts) == 2:
                            minutes = int(time_parts[0])
                            seconds = int(time_parts[1])
                            time_seconds = minutes * 60 + seconds
                            # Find closest time index
                            if timex:  # Ensure timex is not empty
                                closest_idx = min(range(len(timex)), key=lambda i: abs(timex[i] - time_seconds))
                                timeindex[time_idx] = closest_idx
                    except (ValueError, IndexError) as e:
                        _log.warning('Could not parse event time for %s: %s, error: %s', event_name, event_data, str(e))

    # Set basic roast information
    res['samplinginterval'] = 1.5  # Kaleido CSV sampling interval is 1.5 seconds
    res['mode'] = 'C'  # Default Celsius

    # Set roast data
    res['timex'] = timex
    res['temp1'] = temp1
    res['temp2'] = temp2
    if temp3 and all(x != 0 for x in temp3):  # If RoR data exists and not all zeros
        res['temp3'] = temp3

    res['timeindex'] = timeindex

    # Set special events (if exist)
    if len(specialevents) > 0:
        res['specialevents'] = specialevents
        res['specialeventstype'] = specialeventstype
        res['specialeventsvalue'] = specialeventsvalue
        res['specialeventsStrings'] = specialeventsStrings

    # Set event type names
    # Artisan event type system:
    # Index 0: Fan
    # Index 1: Drum 
    # Index 2: Damper
    # Index 3: Burner
    # Index 4: '--' (Special events/annotations for marking notes during roasting)
    # 
    # Kaleido has only 3 control events, using 3 from Artisan:
    # SM (Fan/Air) -> Fan (0)
    # RL (Rotation) -> Drum (1)  
    # HP (Heat Power) -> Burner (3)
    # HPM (M=Manual Heat, A=PID Heat Control based on SV value) - Kaleido machine mode, not used as Artisan control event
    # PS (Status) - Kaleido machine specific, not mapped to Artisan control event
    alt_etypesdefault[0] = 'Fan'    # Corresponds to SM
    alt_etypesdefault[1] = 'Drum'   # Corresponds to RL
    alt_etypesdefault[2] = 'Damper' # Reserved Damper label, but Kaleido doesn't use
    alt_etypesdefault[3] = 'Burner' # Corresponds to HP
    alt_etypesdefault[4] = '--'     # Special events/annotations
    res['etypes'] = alt_etypesdefault

    # Set roaster information
    res['roastertype'] = 'Kaleido Legacy'
    res['roastersize'] = 0.1  # Default roaster size

    # Parse total time
    if 'TotalTime' in sections and sections['TotalTime']:
        total_time = sections['TotalTime'][0].strip() if sections['TotalTime'] else ''
        if total_time:
            try:
                time_parts = total_time.split(':')
                if len(time_parts) == 2:
                    minutes = int(time_parts[0])
                    seconds = int(time_parts[1])
                    total_seconds = minutes * 60 + seconds
                    res['roasttotaltime'] = total_seconds
            except ValueError:
                pass

    return res