from typing import List, Tuple
from data.data_handler import WaterRecord 
from logger.logger import LoggerFactory
from typing import Tuple
from scipy.signal import find_peaks,savgol_filter
from collections import defaultdict
import numpy as np
from data.filter import FilterWaterLevel
from datetime import datetime
from datetime import timedelta

    
def find_peaks_custom(signal: np.ndarray, windows: int, delta: int) -> np.ndarray:
    """
    Tìm vị trí các peak trong mảng signal.

    Tham số:
    - signal: 1D numpy array
    - window: độ rộng cửa sổ (phải lẻ)
    - delta: ngưỡng độ nhô so với điểm thấp nhất trong cửa sổ

    Trả về:
    - numpy array các chỉ số i là peak
    """
    if windows % 2 == 0:
        raise ValueError("window must be an odd integer")
    
    half = windows // 2
    peaks = []
    
    # Chạy từ half đến len(signal)-half-1
    for i in range(half, len(signal) - half):
        win = signal[i-half: i+half+1]  # Cửa sổ hiện tại
        win_left = signal[i-half: i]
        win_right = signal[i+1: i+half+1]
        # kiểm tra i có phải max trong cửa sổ và độ nhô ≥ delta
        if signal[i] == win.max() and (signal[i] - win_left.min()) >= delta and (signal[i] - win_right.min()) >= delta:
            peaks.append(i)
            LoggerFactory().add_log("INFO",f"Peak detected at index {i} with value {signal[i]}", tag="PeakDetection")   
            print(f"Peak detected at index {i} with value {signal[i]}")
             
    return np.array(peaks, dtype=int)
def write_chart(raw_value:np.ndarray ,
                smooth_value:np.ndarray,
                peaks:np.ndarray,
                troughs:np.ndarray,
                ) -> None:
    """
    Saves a numpy array as an image file.
    """
    from matplotlib import pyplot as plt
    
    plt.plot(raw_value, label='Raw Data')
    plt.plot(smooth_value, label='Smoothed Data')
    plt.plot(peaks, raw_value[peaks], "ro", label="Peaks")
    plt.plot(troughs, raw_value[troughs], "go", label="Troughs")
    plt.legend()
    plt.grid(True)
    plt.title("Chart of Water Level with Peaks and Troughs")
    plt.show()
    
def detect_absolute_peaks_troughs(
    records: List[WaterRecord],
    window_sg:  int     = 23,
    delta_sg:   int = 3
) -> Tuple[np.ndarray, np.ndarray]:
    
    # 1) Chuẩn bị times/values
    times_np  = np.array([r.date_time for r in records], dtype='datetime64[m]')
    values_np = np.array([r.water_level_0 for r in records])

    # 2) Lọc dữ liệu, loại bỏ gai
    
    smoothed_value = savgol_filter(values_np, window_length=5, polyorder=1)
    
    # 3) Tìm relative peaks/troughs
    peaks   = find_peaks_custom(smoothed_value,
                        windows     = window_sg,
                        delta       = delta_sg)
    troughs = find_peaks_custom(    -smoothed_value,
                        windows     = window_sg,
                        delta       = delta_sg)
    
    absolute_peaks_indices   =[]
    absolute_troughs_indices =[]

    # 4) Với mỗi relative-peak, tìm absolute-peak trong window ±90’
    for idx in peaks:
        rec = records[idx]
        LoggerFactory().add_log("INFO", f"Relative peak at: {rec.date_time.strftime('%Y-%m-%d %H:%M')}  →  {rec.water_level_0}", tag="ReportMaking")
        

        left_border    = rec.date_time - timedelta(minutes=90)
        right_border   = rec.date_time + timedelta(minutes=90)
        window_indices = [
            idx
            for idx, r in enumerate(records)
            if left_border <= r.date_time <= right_border
        ]
    
        if window_indices:
            abs_peak_index = max(
                window_indices,
                key=lambda i: records[i].water_level_0
            )
            is_duplicate = False
            for peak_indices in absolute_peaks_indices:
                if abs_peak_index == peak_indices:
                    LoggerFactory().add_log(
                        "WARNING",
                        f"Found duplicate peak at {records[abs_peak_index].date_time.strftime('%Y-%m-%d %H:%M')}, skipping.",
                        tag="ReportMaking"
                    )
                    is_duplicate = True
                    print(f"Found duplicate peak at {records[abs_peak_index].date_time.strftime('%Y-%m-%d %H:%M')}, skipping.")
                    break
            if not is_duplicate:
                absolute_peaks_indices.append(abs_peak_index)
                LoggerFactory().add_log(
                    "INFO",
                    f"Absolute peak at: {records[abs_peak_index].date_time.strftime('%Y-%m-%d %H:%M')}  →  {records[abs_peak_index].water_level_0}",
                    tag="ReportMaking"
                )
                print(f"Absolute peak at: {records[abs_peak_index].date_time.strftime('%Y-%m-%d %H:%M')}  →  {records[abs_peak_index].water_level_0}")

    # 5) Tương  với troughs
    for idx in troughs:
        rec = records[idx]
        LoggerFactory().add_log("INFO", f"Relative trough at: {rec.date_time.strftime('%Y-%m-%d %H:%M')}  →  {rec.water_level_0}", tag="ReportMaking")
        print(f"Relative trough at: {rec.date_time.strftime('%Y-%m-%d %H:%M')}  →  {rec.water_level_0}")

        left_border    = rec.date_time - timedelta(minutes=90)
        right_border   = rec.date_time + timedelta(minutes=90)
        window_indices = [
            idx
            for idx, r in enumerate(records)
            if left_border <= r.date_time <= right_border
        ]
    
        if window_indices:
            abs_trough_index = min(
                window_indices,
                key=lambda i: records[i].water_level_0
            )
            is_duplicate = False
            for trough_indices in absolute_troughs_indices:
                if abs_trough_index == trough_indices:
                    LoggerFactory().add_log(
                        "WARNING",
                        f"Found duplicate trough at {records[abs_trough_index].date_time.strftime('%Y-%m-%d %H:%M')}, skipping.",
                        tag="ReportMaking"
                    )
                    print(f"Found duplicate trough at {records[abs_trough_index].date_time.strftime('%Y-%m-%d %H:%M')}, skipping.")
                    is_duplicate = True
                    break
            if not is_duplicate:
                absolute_troughs_indices.append(abs_trough_index)
                LoggerFactory().add_log(
                    "INFO",
                    f"Absolute trough at: {records[abs_trough_index].date_time.strftime('%Y-%m-%d %H:%M')}  →  {records[abs_trough_index].water_level_0}",
                    tag="ReportMaking"
                )
                print(f"Absolute trough at: {records[abs_trough_index].date_time.strftime('%Y-%m-%d %H:%M')}  →  {records[abs_trough_index].water_level_0}")   
    return np.array( absolute_peaks_indices), np.array(absolute_troughs_indices)

    
def detect_last_trend(
    all_records: List[WaterRecord],
    filtered : List[Tuple[WaterRecord, str]]
    ) -> str:
    closest_record = min(
        all_records,
        key=lambda record: abs((record.date_time -  datetime.now()).total_seconds())
        )
    LoggerFactory().add_log("INFO", f"Closest record: {closest_record}", tag="ReportMaking")
    print(f"Closest record: {closest_record}")

    if filtered:
        # 1: downtrend, 2: uptrend
        trend_code = "1" if filtered[-1][1] == 'peak' else "2" # get the last event type 
        print(f"Trend code: {trend_code} (1: downtrend, 2: uptrend)")
        LoggerFactory().add_log("INFO", f"Trend code: {trend_code} (1: downtrend, 2: uptrend)", tag="ReportMaking")
    else:
        LoggerFactory().add_log("INFO", f"No events found, using closest record: {closest_record}", tag="ReportMaking")
        print(f"No events found, using closest record: {closest_record}")
        if closest_record.water_level_0 > all_records[0].water_level_0:
            trend_code = "2" # uptrend
        else:
            trend_code = "1"  # downtrend
        print(f"Trend code: {trend_code} (1: downtrend, 2: uptrend)")
        LoggerFactory().add_log("INFO", f"Trend code: {trend_code} (1: downtrend, 2: uptrend)", tag="ReportMaking")
    return filtered , trend_code, closest_record
def find_peak_last_point(arr: np.ndarray, delta: int = 10) -> int:
    """
    Tìm index của peak đơn giản:
      - Lấy giá trị max và vị trí i = arr.argmax()
      - i không nằm trong 3 phần tử đầu hoặc 3 phần tử cuối
      - arr[i] - arr[-1] > delta
    Trả về i nếu thỏa, ngược lại trả về -1.
    """
    if arr.size < 7:
        return -1

    i = int(np.argmax(arr))
    if 2 < i < arr.size - 3 and (arr[i] - arr[-1]) > delta:
        return i
    return -1


def check_last_point(
    records: List[WaterRecord],
    absolute_peaks: List[int],
    absolute_troughs: List[int],
    delta: int
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Kiểm tra điểm cuối cùng và có thể thêm vào absolute_peaks hoặc absolute_troughs,
    rồi log và print trước khi trả về.

    - records: danh sách WaterRecord đã sắp xếp theo date_time tăng dần
    - absolute_peaks: danh sách các peak tuyệt đối hiện tại
    - absolute_troughs: danh sách các trough tuyệt đối hiện tại
    - delta: ngưỡng độ nhô so với đáy/cuội
    """
    # 1) Kết hợp & sort để kiểm tra khoảng 3h

    list_all_peaks_troughts_indice = sorted(
        [(r, 'peak')   for r in absolute_peaks] +
        [(r, 'trough') for r in absolute_troughs],
        key=lambda x: x[0]
    )

    last_rec  = records[-1]
    last_time = last_rec.date_time
    last_variable   = last_rec.water_level_0

    # Nếu đã có peak/trough trong 3h, log và trả về luôn
    if list_all_peaks_troughts_indice:
        last_pt_time = records[list_all_peaks_troughts_indice[-1][0]].date_time # lấy thời gian của peak/trough cuối cùng
        if (last_time - last_pt_time) < timedelta(hours=3):
            summary_peaks   = [(records[r].date_time.strftime('%Y-%m-%d %H:%M'), records[r].water_level_0) for r in absolute_peaks]
            summary_troughs = [(records[r].date_time.strftime('%Y-%m-%d %H:%M'), records[r].water_level_0) for r in absolute_troughs]
            LoggerFactory().add_log(
                "INFO",
                f"Found new point within 3h. Peaks: {summary_peaks}, Troughs: {summary_troughs}",
                tag="ReportMaking"
            )
            print(f"Found new point within 3h. Peaks: {summary_peaks}, Troughs: {summary_troughs}")
            return np.array(absolute_peaks), np.array(absolute_troughs)

    # Xác định window 3h, Trường hợp không có peak hoặc trough nào 
    window_start = last_time - timedelta(hours=3)
    rec_3h = next((r for r in records if r.date_time >= window_start), records[0])


    inner_start = window_start + timedelta(minutes=30)
    inner_end   = last_time     - timedelta(minutes=30)
    window_recs = [idx for (idx, r) in enumerate(records) if window_start <= r.date_time] # lọc các bản ghi trong khoảng 3h, trừ 30 phút đầu và cuối

    # Nếu không có bản ghi trong window, log và trả về
    if not window_recs:
        summary_peaks   = [(records[r].date_time.strftime('%Y-%m-%d %H:%M'), records[r].water_level_0) for r in absolute_peaks]
        summary_troughs = [(records[r].date_time.strftime('%Y-%m-%d %H:%M'), records[r].water_level_0) for r in absolute_troughs]
        LoggerFactory().add_log(
            "INFO",
            f"Not found data during 3h from : {last_time}",
            tag="ReportMaking"
        )
        print(f"Not found data during 3h from : {last_time}")
        return np.array(absolute_peaks), np.array(absolute_troughs)


    # Tìm candidate và thêm nếu vượt delta
    
    candidate = max(
        window_recs, 
        key=lambda r: records[r].water_level_0)
    # Tìm peak tuyệt đối trong khoảng 30 phút trước và sau
    if abs(records[candidate].water_level_0 - last_variable) > delta and inner_start < records[candidate].date_time <inner_end:
        # Chỉ thêm nếu candidate nằm trong khoảng 30 phút trước và sau:
        absolute_peaks.append(candidate)
    # Tương tự với troughs
    candidate = min(
        window_recs, 
        key=lambda r: records[r].water_level_0)
    if abs( records[candidate].water_level_0 - last_variable) > delta and inner_start < records[candidate].date_time <inner_end:
        absolute_troughs.append(candidate)

    # Cuối cùng: log + print summary rồi return
    summary_peaks   = [(records[r].date_time.strftime('%Y-%m-%d %H:%M'), records[r].water_level_0) for r in absolute_peaks]
    summary_troughs = [(records[r].date_time.strftime('%Y-%m-%d %H:%M'), records[r].water_level_0) for r in absolute_troughs]
    LoggerFactory().add_log(
        "INFO",
        f"Updated points. Peaks: {summary_peaks}, Troughs: {summary_troughs}",
        tag="ReportMaking"
    )
    print(f"Updated points. Peaks: {summary_peaks}, Troughs: {summary_troughs}")
    
    return  np.array(absolute_peaks), np.array(absolute_troughs)

def remove_duplicate_peaks_troughts( records: List[WaterRecord],
    absolute_peaks: List[WaterRecord],
    absolute_troughs: List[WaterRecord],
) ->Tuple[np.ndarray, np.ndarray]:
    """
    Lọc các peak/trough tuyệt đối để đảm bảo không có hai peak hoặc hai trough
    xuất hiện liên tiếp nhau.

    Tham số:
    - absolute_peaks: danh sách WaterRecord của các peak tuyệt đối
    - absolute_troughs: danh sách WaterRecord của các trough tuyệt đối

    Trả về:
    - List[ (record, 'peak'|'trough') ] đã được lọc và sắp xếp theo thời gian
    """
    # 1) Kết hợp rồi sort theo thời gian
    list_all_peaks_troughts_indice = sorted(
        [(r, 'peak')   for r in absolute_peaks] +
        [(r, 'trough') for r in absolute_troughs],
        key=lambda x: x[0]
    )
    # 2) Duyệt và gộp những nhóm cùng loại liên tiếp
    filtered: List[Tuple[int, str]] = []
    i = 0
    n = len(list_all_peaks_troughts_indice)

    while i < n:
        rec_i = list_all_peaks_troughts_indice[i][0]
        type_i =list_all_peaks_troughts_indice[i][1]
        # nhóm bắt đầu tại i
        group = [rec_i]
        j = i + 1
        # thu thập hết nhóm cùng type
        while j < n and list_all_peaks_troughts_indice[j][1] == type_i:
            group.append(list_all_peaks_troughts_indice[j][0])
            j += 1
        # nếu là peak, chọn peak cao nhất; nếu trough, chọn trough thấp nhất
        if len(group) > 1 and type_i == 'peak':
            best = max(group, key=lambda r: records[r].water_level_0)
            filtered.append((best, type_i))
            LoggerFactory().add_log("WARNING",f"Found dubplicate peak, choose the best: {best}")
        elif len(group) > 1:
            best = min(group, key=lambda r: records[r].water_level_0)
            LoggerFactory().add_log("WARNING",f"Found dubplicate trough, choose the best: {best}")
            filtered.append((best, type_i))
        else:
            # nếu chỉ có một bản ghi trong nhóm, thêm vào filtered
            filtered.append((group[0], type_i))
            LoggerFactory().add_log("INFO",f"Adding single record: {group[0]} as {type_i}")
        # tiếp tục từ sau nhóm
        i = j
    absolute_peaks_filtered =[r for r, _ in filtered if _ == 'peak']
    absolute_troughs_filtered = [r for r, _ in filtered if _ == 'trough']
    LoggerFactory().add_log("INFO",f"Filtered peaks: {absolute_peaks_filtered}")
    LoggerFactory().add_log("INFO",f"Filtered troughs: {absolute_troughs_filtered}")
    print(f"Filtered peaks: {absolute_peaks_filtered}")
    print(f"Filtered troughs: {absolute_troughs_filtered}")
    
    return np.array(absolute_peaks_filtered), np.array(absolute_troughs_filtered)

def remove_closed_peaks_troughts(
    records: List[WaterRecord],
    absolute_peaks: np.ndarray,
    absolute_troughs: np.ndarray,
    height: int,
    width: int
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Gom các event (peak/trough) nếu chúng cách nhau ≤ width (về index)
    và chênh lệch water_level_0 ≤ height, bất kể loại event.
    Sau đó với mỗi nhóm:
      - Nếu size nhóm == 1: giữ nguyên
      - Nếu size nhóm > 1: xác định biên trái phải, tính a, b, rồi:
          * a, b > 0  → peak  → chọn max(group)
          * a, b < 0  → trough→ chọn min(group)
          * khác      → bỏ nhóm
    """

    # 1) Kết hợp và sort theo index
    events: List[Tuple[int, str]] = [
        (int(idx), 'peak')   for idx in absolute_peaks
    ] + [
        (int(idx), 'trough') for idx in absolute_troughs
    ]
    events.sort(key=lambda x: x[0])

    new_peaks = []
    new_troughs = []
    n = len(events)
    n_rec = len(records)
    i = 0

    # 2) Quét tuần tự, gom nhóm bất kể loại
    while i < n:
        idx0, kind0 = events[i]
        group = [idx0]
        j = i + 1

        # Gom nhóm khi idx cách nhau ≤ width và value chênh ≤ height
        while j < n:
            idxj, _ = events[j]
            if idxj - group[-1] <= width and \
               abs(records[idxj].water_level_0 - records[group[-1]].water_level_0) <= height:
                group.append(idxj)
                j += 1
            else:
                break

        # 3) Xử lý nhóm
        if len(group) == 1:
            # đơn lẻ: thêm trực tiếp theo kind0
            if kind0 == 'peak':
                new_peaks.append(group[0])
            else:
                new_troughs.append(group[0])

        else:  # nhóm nhiều phần tử
            left, right = group[0], group[-1]
            # xác định biên trái/phải trong giới hạn array
            delta_t = width // 2
            left_b = max(0, left - delta_t)
            right_b = min(n_rec - 1, right + delta_t)

            # a = left_value - left_boundary_value
            a = records[left].water_level_0 - records[left_b].water_level_0
            # b = right_value - right_boundary_value
            b = records[right].water_level_0 - records[right_b].water_level_0

            if a > 0 and b > 0:
                # nhóm peak → chọn max
                best = max(group, key=lambda ix: records[ix].water_level_0)
                new_peaks.append(best)

            elif a < 0 and b < 0:
                # nhóm trough → chọn min
                best = min(group, key=lambda ix: records[ix].water_level_0)
                new_troughs.append(best)

            # else: bỏ cả nhóm

        # chuyển tới nhóm tiếp theo
        i = j

    return (
        np.array(new_peaks,   dtype=int),
        np.array(new_troughs, dtype=int),
    )


    
def filter_peaks_troughs( records: List[WaterRecord],
    absolute_peaks: List[WaterRecord],
    absolute_troughs: List[WaterRecord],
) -> Tuple[np.ndarray, np.ndarray]:
    absolute_peaks_filtered,absolute_troughs_filtered = remove_duplicate_peaks_troughts(records, absolute_peaks, absolute_troughs)
    absolute_peaks_after_remove_closeer, absolute_troughts_after_remove_closeer = remove_closed_peaks_troughts(records, absolute_peaks_filtered.tolist(),absolute_troughs_filtered.tolist(),height= 50,width= 40)
    write_chart(
        raw_value = np.array([r.water_level_0 for r in records], dtype='int'),
        smooth_value =  np.array([r.water_level_0 for r in records], dtype='int'),
        peaks =      absolute_peaks_after_remove_closeer,
        troughs =    absolute_troughts_after_remove_closeer
    )
    return absolute_peaks_after_remove_closeer, absolute_troughts_after_remove_closeer
def trend_detected_processes(
    all_records: List[WaterRecord],
) -> Tuple[List[WaterRecord], List[WaterRecord], str]:
    """
    Xử lý phát hiện xu hướng và đỉnh/đáy từ danh sách bản ghi.
    Trả về danh sách đỉnh, đáy và mã xu hướng.
    """
    raw_data = [r.water_level_0 for r in all_records]
    print(f"Raw data: {raw_data}")
    # 1) Phát hiện đỉnh/đáy
    absolute_peakss_indices, absolute_troughs_indices = detect_absolute_peaks_troughs(all_records)
    absolute_peaks_indices, absolute_troughs_indices = check_last_point(all_records, absolute_peakss_indices.tolist(), absolute_troughs_indices.tolist(), delta=15)
    absolute_peaks_indices,absolute_troughs_indices  = filter_peaks_troughs( all_records,absolute_peaks_indices.tolist(), absolute_troughs_indices.tolist())
    filtered = [
        (all_records[i], 'peak')   for i in absolute_peaks_indices
    ] + [
        (all_records[i], 'trough') for i in absolute_troughs_indices
    ]
    filtered.sort(key=lambda x: x[0].date_time)  # Sắp xếp theo thời gian
    # Log and print results
    LoggerFactory().add_log("INFO", f"Raw data: {raw_data}", tag="ReportMaking")
    LoggerFactory().add_log("INFO", f"Absolute peaks: {[all_records[r].date_time.strftime('%Y-%m-%d %H:%M') for r in absolute_peaks_indices]}", tag="ReportMaking")
    LoggerFactory().add_log("INFO", f"Absolute troughs: {[all_records[r].date_time.strftime('%Y-%m-%d %H:%M') for r in absolute_troughs_indices]}", tag="ReportMaking")
    print(f"Filtered peaks/troughs: {filtered}")
    # 2) Phát hiện xu hướng
    filtered, trend_code ,closest_record= detect_last_trend(all_records, filtered)
    return filtered, trend_code, closest_record