
from scipy.signal import find_peaks,savgol_filter
from datetime import datetime, timedelta
import pdb
from typing import List, Tuple
class WaterRecord:
    def __init__(self, id, serial_number, date_time, water_level_0, water_level_1, water_level_2, vol):
        self.id = id
        self.serial_number = serial_number
        self.date_time = date_time
        self.water_level_0 = water_level_0
        self.water_level_1 = water_level_1
        self.water_level_2 = water_level_2
        self.vol = vol
        
def detect_absolute_peaks_troughs(
    records: List[WaterRecord],
    window_sg: int = 3,
    polyorder: int = 2, #1: noi suy, 2: do thi bac 2
    prominence: int = 10,
    min_distance: int = 2
):
    #values = np.array([r.water_level_0 for r in records])
    values = [r.water_level_0 for r in records]
    frist_value =       values[0]
    second_value =      values[1]
    pre_last_value =    values[-2]
    last_value =        values[-1]
    print(f"values before smoothing: {values}")
    smooth = savgol_filter(values, window_length=window_sg, polyorder=polyorder)
    print(f"values after smoothing: {smooth}")
    smooth[0] = frist_value  # Keep the first value unchanged
    smooth[1] = second_value  # Keep the second value unchanged
    smooth[-2] = pre_last_value  # Keep the second last value unchanged
    smooth[-1] = last_value  # Keep the last value unchanged
    smooth_revert = [-1 * v for v in smooth]  # Revert smoothed values for trough detection
    
    # 3) Tìm peaks và troughs
    absolute_peaks = []
    absolute_troughs = [] 
    relative_peak_poses, _   = find_peaks(smooth, prominence=prominence, distance=min_distance)
    relative_trough_poses,_ = find_peaks(smooth_revert, prominence=prominence, distance=min_distance)
    print(f"Detect RELATIVE {len(relative_peak_poses)} peaks and {len(relative_trough_poses)} troughs.")
    # 4) Lấy bản ghi tương ứng với peaks và troughs
    for idx in relative_peak_poses:
        rec = records[idx]
        print(f"relative peak at: {rec.date_time.strftime('%D %H:%M')}  →  Water_Level(0) = {rec.water_level_0}")
        left_date_time_border = rec.date_time - timedelta(minutes=90) 
        right_date_time_border = rec.date_time + timedelta(minutes=90) 
        list_rec = [r for r in records if left_date_time_border <= r.date_time <= right_date_time_border]
        if len(list_rec) > 0:
            absolute_peaks.append(max(list_rec, key=lambda r: r.water_level_0))
            print(f"Detect absolute peaks at: {absolute_peaks[-1].date_time.strftime('%D %H:%M')}  →  Water_Level(0) = {absolute_peaks[-1].water_level_0}")
    for idx in relative_trough_poses:
        rec = records[idx]
        print(f"relative trough at: {rec.date_time.strftime('%H:%M')}  →  Water_Level(0) = {rec.water_level_0}")
        left_date_time_border = rec.date_time - timedelta(minutes=90)
        right_date_time_border = rec.date_time + timedelta(minutes=90) 
        list_rec = [r for r in records if left_date_time_border <= r.date_time <= right_date_time_border]
        if len(list_rec) > 0:
            absolute_troughs.append(min(list_rec, key=lambda r: r.water_level_0))
            print(f"Detect absolute troughs at: {absolute_troughs[-1].date_time.strftime('%H:%M')}  →  Water_Level(0) = {absolute_troughs[-1].water_level_0}")
    return absolute_peaks, absolute_troughs


def main():
    value_4h =[1898, 1906, 1928, 1940, 1937, 1942, 1956, 1976, 1980, 1968, 1960, 1973, 1974, 1997, 2020, 2016, 2019, 2022, 2024, 2015, 2006, 1996, 1987, 1976, 1935, 1894, 1877, 1861, 1823]
    start_dt = datetime(2025, 6, 17, 6, 50, 7)        # "2025-6-17 6:50:7"
    interval = timedelta(minutes=10)                  # subtract 10 minutes each step
    raw_data = []
    for i, val in enumerate(value_4h):
        ts = start_dt - i * interval
        raw_data.append((ts.strftime("%Y-%m-%d %H:%M:%S"), val))
        
        raw_data.sort(key=lambda r: r[0])
        parsed_records = [
            WaterRecord(
                id=i,
                serial_number="SN001",
                date_time=datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S"),
                water_level_0=level,
                water_level_1=0,
                water_level_2=0,
                vol=0.0
            )
            for i, (dt_str, level) in enumerate(raw_data)
        ]      
    print("Parsed Records:")
    for record in parsed_records:
        print(f"ID: {record.id}, DateTime: {record.date_time}, Water Level: {record.water_level_0}")
        
    absolute_peaks, absolute_troughs = detect_absolute_peaks_troughs(parsed_records)
    print(f"Absolute Peaks: {absolute_peaks[0].water_level_0 if absolute_peaks else 'None'}")
    print(f"Absolute Troughs: {absolute_troughs[0].water_level_0 if absolute_troughs else 'None'}")
    
if __name__ == "__main__":
    main()