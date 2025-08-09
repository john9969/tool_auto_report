from data.data_process import WaterRecord
from datetime import datetime
from typing import List, Tuple, Set
from logger.logger import LoggerFactory
from data.trend_detected import ReportPoint
from datetime import timedelta
import json
SERIAL_NUMBER = "74165"

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
    list_report_point: List[ReportPoint],
    rain_level: int
) -> str:
    print("Start Making report")
    LoggerFactory().add_log("INFO", f"Start Making report:", tag="ReportMaking")
    
    report = SERIAL_NUMBER + " 22 "
    for report_point in list_report_point:
        ch = f"{report_point.date_time.day:02d}{report_point.date_time.hour:02d} "
        ch += f"{report_point.trend}{report_point.water_level//10:04d} "
        report += ch
    report += f"44 {datetime.now().day:02d}{datetime.now().hour:02d} 3"
    report += f"{rain_level:04d}="
    
    return report