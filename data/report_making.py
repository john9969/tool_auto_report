from data.data_handler import WaterRecord
from datetime import datetime
from typing import List, Tuple, Set
from logger.logger import LoggerFactory
from datetime import timedelta
import json
SERIAL_NUMBER = "74194"

import os
from typing import List, Tuple
def load_last_events(filename: str = "record_data.json") -> Tuple[Set[int], Set[int]]:
    """
    1. Opens filename and reads its entire contents as a string.
    2. Parses JSON: expects {"peaks": [id,...], "troughs":[id,...]}.
    3. Returns two sets of ints.
    """
    if not os.path.exists(filename):
        return set(), set()
    with open(filename, "r") as f:
        data_str = f.read()
    data = json.loads(data_str)
    return set(data.get("peaks", [])), set(data.get("troughs", []))


def update_peaks_troughs_json(
    filtered_new: List[Tuple[WaterRecord, str]],
    filename: str = "record_data.json"
) -> List[Tuple[WaterRecord, str]]:
    """
    - Loads last-run peaks/troughs from JSON.
    - Filters out any rec.id already seen in the appropriate category.
    - Saves THIS runs peaks & troughs (fresh lists) back to JSON.
    - Returns only the new events.
    """
    # 1) Load last-run sets
    last_peaks, last_troughs = load_last_events(filename)
    
    # 2) Sort incoming events by datetime
    sorted_candidates = sorted(filtered_new, key=lambda x: x[0].date_time)

    # 3) Keep only those within the last 8 hours
    cutoff = datetime.now() - timedelta(hours=8)
    recent_candidates = [
        (rec, kind)
        for rec, kind in sorted_candidates
        if rec.date_time > cutoff
    ]

    # 4) Filter for genuinely new
    new_events: List[Tuple[WaterRecord, str]] = []
    for rec, kind in recent_candidates:
        if kind == "peak" and rec.id not in last_peaks:
            new_events.append((rec, kind))
        elif kind == "trough" and rec.id not in last_troughs:
            new_events.append((rec, kind))
        else: 
            LoggerFactory().add_log(
                "INFO",
                f"Skipping {kind} at {rec.date_time.strftime('%Y-%m-%d %H:%M')} with ID {rec.id} already seen in file record_data.",
                tag="ReportMaking"
            )
            print(
                f"Skipping {kind} at {rec.date_time.strftime('%Y-%m-%d %H:%M')} with ID {rec.id} already seenin file record_data."
            )

    # 5) Prepare fresh lists for saving (overwrite)
    fresh_peaks   = [rec.id for rec, kind in filtered_new if kind == "peak"]
    fresh_troughs = [rec.id for rec, kind in filtered_new if kind == "trough"]

    # 6) Write JSON file (not appending)
    with open(filename, "w") as f:
        json.dump(
            {"peaks": fresh_peaks, "troughs": fresh_troughs},
            f,
            indent=2
        )

    return new_events


def make_report(
    filtered: List[Tuple[WaterRecord,str]],
    trend_code:  str,
    closest_record: WaterRecord,
) -> str:
    print("Start Making report")
    LoggerFactory().add_log("INFO", f"Start Making report:", tag="ReportMaking")
    trend_code += f"{closest_record.water_level_0 // 10:04d}"
    print(f"Trend code: {trend_code} (1: downtrend, 2: uptrend)")
    # Lọc bỏ các peak/trough cũ hơn 6.5 giờ so với thời điểm hiện tại
    # Tmin = datetime.now() - timedelta(hours=6, minutes=30)
    # filtered_new: List[Tuple[WaterRecord, str]] = []
    # for rec, kind in filtered:
    #     if rec.date_time < Tmin:
    #         LoggerFactory().add_log(
    #             "INFO",
    #             f"Dropping {kind} at {rec.date_time.strftime('%Y-%m-%d %H:%M')} older than {Tmin.strftime('%Y-%m-%d %H:%M')}",
    #             tag="ReportMaking"
    #         )
    #         print(
    #             f"Dropping {kind} at {rec.date_time.strftime('%Y-%m-%d %H:%M')} older than {Tmin.strftime('%Y-%m-%d %H:%M')}"
    #         )
    #     else:
    #         filtered_new.append((rec, kind))
            
    # 1) Check old reported peaks and troughs
    if(datetime.now().hour == 1 or datetime.now().hour == 7 or datetime.now().hour == 13 or datetime.now().hour == 19):
        filtered = update_peaks_troughs_json(filtered)
    else:
        # Lọc bỏ các peak/trough cũ hơn 6.5 giờ so với thời điểm hiện tại
        Tmin = datetime.now() - timedelta(hours=6, minutes=30)
        filtered_new: List[Tuple[WaterRecord, str]] = []
        for rec, kind in filtered:
            if rec.date_time < Tmin:
                LoggerFactory().add_log(
                    "INFO",
                    f"Dropping {kind} at {rec.date_time.strftime('%Y-%m-%d %H:%M')} older than {Tmin.strftime('%Y-%m-%d %H:%M')}",
                    tag="ReportMaking"
                )
                print(
                    f"Dropping {kind} at {rec.date_time.strftime('%Y-%m-%d %H:%M')} older than {Tmin.strftime('%Y-%m-%d %H:%M')}"
                )
            else:
                filtered_new.append((rec, kind))
        filtered = filtered_new
                
    peaks_and_troughs_str =""
    for rec in filtered:
        if(rec[1] == 'peak'):
            if peaks_and_troughs_str:
                peaks_and_troughs_str += " "
            peaks_and_troughs_str += f"{rec[0].date_time.strftime('%H%M')} 8{rec[0].water_level_0 // 10:04d}"
            print(f"add peak at {rec[0].date_time.strftime('%H:%M')} → Water_Level(0) = {rec[0].water_level_0}")
        else:
            if peaks_and_troughs_str:
                peaks_and_troughs_str += " "
            peaks_and_troughs_str += f"{rec[0].date_time.strftime('%H%M')} 9{rec[0].water_level_0 // 10:04d}"
            print(f"add trough at {rec[0].date_time.strftime('%H:%M')} → Water_Level(0) = {rec[0].water_level_0}")
    # 2) Create report string
    print("Creating report string:")
    ch = f"{datetime.now().day:02d}{datetime.now().hour:02d}"
    parts = [str(SERIAL_NUMBER), "22", ch]
    parts.append(str(trend_code))
    if peaks_and_troughs_str:
        parts.append(peaks_and_troughs_str)
    parts += ["44", ch, "30000="]
    return " ".join(parts)