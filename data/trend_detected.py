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
from scipy.optimize import curve_fit

def sine_wave(x, amplitude, frequency, phase_shift, vertical_shift):
    return amplitude * np.sin(frequency * x + phase_shift) + vertical_shift

def detect_sine_peaks_troughs(all_records: List[WaterRecord]) -> Tuple[np.ndarray, np.ndarray]:
    data = [r.water_level_0 for r in all_records]
    # 1) Smoothing data by Savitzky-Golay filter
    LoggerFactory().add_log("INFO", "Step 1: Smoothing data by Savitzky-Golay filter", tag="SineDetection")
    smoothed = savgol_filter(data, window_length=5, polyorder=1)
    LoggerFactory().add_log("INFO", f"Smoothed data: {smoothed.tolist()}", tag="SineDetection")

    # Bước 2: Fit data to a sine wave
    LoggerFactory().add_log("INFO", "Step 2: Fitting data to a sine wave", tag="SineDetection")
    x = np.arange(len(smoothed))
    LoggerFactory().add_log("INFO", f"x values: {x.tolist()}", tag="SineDetection")
    guess = [np.ptp(smoothed)/2, 2*np.pi/len(smoothed), 0, np.mean(smoothed)]
    LoggerFactory().add_log("INFO", f"Initial guess for curve_fit: {guess}", tag="SineDetection")
    params, _ = curve_fit(sine_wave, x, smoothed, p0=guess)
    LoggerFactory().add_log("INFO", f"Fitted sine parameters: {params.tolist()}", tag="SineDetection")
    fitted = sine_wave(x, *params)
    LoggerFactory().add_log("INFO", f"Fitted sine values: {fitted.tolist()}", tag="SineDetection")

    # Bước 3: Calcultate gradient to find slope
    LoggerFactory().add_log("INFO", "Step 3: Calculating gradient to find slope", tag="SineDetection")
    dy = np.gradient(fitted)
    #LoggerFactory().add_log("INFO", f"Gradient (dy): {dy.tolist()}", tag="SineDetection")
    slope = np.sign(dy)
    #LoggerFactory().add_log("INFO", f"Slope (sign of dy): {slope.tolist()}", tag="SineDetection")

    # Bước 4: Detect peaks and troughs from slope changes
    LoggerFactory().add_log("INFO", "Step 4: Detecting peaks and troughs from slope changes", tag="SineDetection")
    peaks = np.where((slope[:-1] > 0) & (slope[1:] < 0))[0]
    troughs = np.where((slope[:-1] < 0) & (slope[1:] > 0))[0]
    LoggerFactory().add_log("INFO", f"Peaks indices: {peaks.tolist()}", tag="SineDetection")
    LoggerFactory().add_log("INFO", f"Troughs indices: {troughs.tolist()}", tag="SineDetection")
    print(f"Peaks indices: {[all_records[i] for i in peaks]}")
    print(f"Troughs indices: {[all_records[i] for i in troughs]}")
    LoggerFactory().add_log("INFO", f"Peaks: {[all_records[i] for i in peaks]}", tag="SineDetection")
    LoggerFactory().add_log("INFO", f"Troughs: {[all_records[i] for i in troughs]}", tag="SineDetection")
    return peaks, troughs
    
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
        win = signal[i-half : i+half+1]
        # kiểm tra i có phải max trong cửa sổ và độ nhô ≥ delta
        if signal[i] == win.max() and (signal[i] - win.min()) >= delta:
            peaks.append(i)
            LoggerFactory().add_log("INFO",f"Peak detected at index {i} with value {signal[i]}", tag="PeakDetection")   
            print(f"Peak detected at index {i} with value {signal[i]}")
             
    return np.array(peaks, dtype=int)

def detect_absolute_peaks_troughs(
    records: List[WaterRecord],
    window_sg:  int     = 17,
    delta_sg:   int = 50
) -> Tuple[List[WaterRecord], List[WaterRecord]]:
    if 0:
        # 1) Chuẩn bị times/values
        times_np  = np.array([r.date_time for r in records], dtype='datetime64[m]')
        values_np = np.array([r.water_level_0 for r in records])

        # 2) Lọc dữ liệu, loại bỏ gai
        
        filter = FilterWaterLevel()
        values_np = filter.smooth_data_by_average(values_np)
        detect_trend_raw = detect_total_trend(records,values_np)
        # 3) Tìm relative peaks/troughs
        peaks   = find_peaks_custom(values_np,
                            windows     = window_sg,
                            delta       = delta_sg)
        troughs = find_peaks_custom(    -values_np,
                            windows     = window_sg,
                            delta       = delta_sg)
    # 1) Using SIN wave detection
    LoggerFactory().add_log("INFO", "Step 1: Detecting peaks and troughs using sine wave detection", tag="ReportMaking")    
    peaks,troughs = detect_sine_peaks_troughs(records)
    
    absolute_peaks   = []
    absolute_troughs = []

    # 4) Với mỗi relative-peak, tìm absolute-peak trong window ±90’
    for idx in peaks:
        rec = records[idx]
        LoggerFactory().add_log("INFO", f"Relative peak at: {rec.date_time.strftime('%Y-%m-%d %H:%M')}  →  {rec.water_level_0}", tag="ReportMaking")
        
        # lấy numpy.datetime64 rồi chuyển về datetime.datetime
        rec_time  = rec.date_time

        left_border    = rec_time - timedelta(minutes=90)
        right_border   = rec_time + timedelta(minutes=90)
        window_recs = [r for r in records 
                   if left_border <= r.date_time <= right_border]
    
        if window_recs:
            abs_peak = max(window_recs, key=lambda r: r.water_level_0)
            absolute_peaks.append(abs_peak)
            LoggerFactory().add_log(
                "INFO",
                f"Absolute peak at: {abs_peak.date_time.strftime('%Y-%m-%d %H:%M')}  →  {abs_peak.water_level_0}",
                tag="ReportMaking"
            )

    for idx in troughs:
        rec = records[idx]
        LoggerFactory().add_log(
            "INFO",
            f"Relative trough at: {rec.date_time.strftime('%Y-%m-%d %H:%M')}  →  {rec.water_level_0}",
            tag="ReportMaking"
        )
        
        rec_time    = rec.date_time
        left_border = rec_time - timedelta(minutes=90)
        right_border= rec_time + timedelta(minutes=90)
        
        window_recs = [r for r in records 
                    if left_border <= r.date_time <= right_border]
        
        if window_recs:
            # tìm đáy tuyệt đối (min)
            abs_trough = min(window_recs, key=lambda r: r.water_level_0)
            absolute_troughs.append(abs_trough)
            LoggerFactory().add_log(
                "INFO",
                f"Absolute trough at: {abs_trough.date_time.strftime('%Y-%m-%d %H:%M')}  →  {abs_trough.water_level_0}",
                tag="ReportMaking"
            )
    return absolute_peaks, absolute_troughs
def detect_total_trend(
    records: List[WaterRecord],
    smoothed: np.ndarray,
    threshold_hours = 1
) -> List[Tuple[int, str]]:
    # Compute initial trend: True for upward, False for downward segments
    
    trend = ["up" if smoothed[i+1] > smoothed[i] else "down" for i in range(len(smoothed)-1)]
    print(f"Initial trend: {trend}")
    LoggerFactory().add_log("INFO", f"Initial trend: {trend}", tag="ReportMaking")
    trend_list = []
    for i in range(len(smoothed)-1):
        trend_list.append((int(smoothed[i]), trend[i]))
    # Thêm phần tử cuối, xu hướng giữ nguyên phần tử trước đó
    trend_list.append((int(smoothed[-1]), trend[-1]))
    print(f"Trend raw data: {trend_list}")
    LoggerFactory().add_log("INFO", f"Trend raw data: {trend_list}", tag="ReportMaking")
    
    # Remove small trend runs shorter than threshold
    run_start_idx = 0
    while run_start_idx < len(trend):
        run_end_idx = run_start_idx

        # Tìm vị trí kết thúc chuỗi trend liên tục cùng hướng
        while run_end_idx < len(trend) and trend[run_end_idx] == trend[run_start_idx]:
            run_end_idx += 1

        # Thời gian bắt đầu và kết thúc chuỗi trend
        start_time = records[run_start_idx].date_time
        if run_end_idx < len(smoothed):
            end_time = records[run_end_idx].date_time
        else:
            end_time = records[-1].date_time

        duration_hours = (end_time - start_time).total_seconds() / 3600

        # Nếu thời gian chuỗi quá ngắn và neighbors giống nhau thì thay đổi
        if (0 < run_start_idx < run_end_idx < len(trend)
                and duration_hours < threshold_hours
                and trend[run_start_idx - 1] == trend[run_end_idx]):
            for idx in range(run_start_idx, run_end_idx):
                trend[idx] = trend[run_start_idx - 1]
                trend_list[idx] = (trend_list[idx][0], trend[run_start_idx - 1])

        # Chuyển sang chuỗi tiếp theo
        run_start_idx = run_end_idx
    print(f"Trend after removing short runs: {trend_list}")
    LoggerFactory().add_log("INFO", f"Trend after removing short runs: {trend_list}", tag="ReportMaking")
    return trend_list
    
    
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
    absolute_peaks: List[WaterRecord],
    absolute_troughs: List[WaterRecord],
    delta: int
) -> Tuple[List[WaterRecord], List[WaterRecord]]:
    """
    Kiểm tra điểm cuối cùng và có thể thêm vào absolute_peaks hoặc absolute_troughs,
    rồi log và print trước khi trả về.

    - records: danh sách WaterRecord đã sắp xếp theo date_time tăng dần
    - absolute_peaks: danh sách các peak tuyệt đối hiện tại
    - absolute_troughs: danh sách các trough tuyệt đối hiện tại
    - delta: ngưỡng độ nhô so với đáy/cuội
    """
    # 1) Kết hợp & sort để kiểm tra khoảng 3h
    filtered = ([(r, 'peak')   for r in absolute_peaks] +
                [(r, 'trough') for r in absolute_troughs])
    filtered.sort(key=lambda x: x[0].date_time)

    last_rec  = records[-1]
    last_time = last_rec.date_time
    last_variable   = last_rec.water_level_0

    # Nếu đã có peak/trough trong 3h, log và trả về luôn
    if filtered:
        last_pt_time = filtered[-1][0].date_time
        if (last_time - last_pt_time) < timedelta(hours=3):
            summary_peaks   = [(r.date_time.strftime('%Y-%m-%d %H:%M'), r.water_level_0) for r in absolute_peaks]
            summary_troughs = [(r.date_time.strftime('%Y-%m-%d %H:%M'), r.water_level_0) for r in absolute_troughs]
            LoggerFactory().add_log(
                "INFO",
                f"Found new point within 3h. Peaks: {summary_peaks}, Troughs: {summary_troughs}",
                tag="ReportMaking"
            )
            print(f"Found new point within 3h. Peaks: {summary_peaks}, Troughs: {summary_troughs}")
            return absolute_peaks, absolute_troughs

    # Xác định window 3h, Trường hợp không có peak hoặc trough nào 
    window_start = last_time - timedelta(hours=3)
    rec_3h = next((r for r in records if r.date_time >= window_start), records[0])
    val_3h = rec_3h.water_level_0


    inner_start = window_start + timedelta(minutes=30)
    inner_end   = last_time     - timedelta(minutes=30)
    window_recs = [r for r in records if window_start <= r.date_time] # lọc các bản ghi trong khoảng 3h, trừ 30 phút đầu và cuối

    # Nếu không có bản ghi trong window, log và trả về
    if not window_recs:
        summary_peaks   = [(r.date_time.strftime('%Y-%m-%d %H:%M'), r.water_level_0) for r in absolute_peaks]
        summary_troughs = [(r.date_time.strftime('%Y-%m-%d %H:%M'), r.water_level_0) for r in absolute_troughs]
        LoggerFactory().add_log(
            "INFO",
            f"No records in 3h window. Peaks: {summary_peaks}, Troughs: {summary_troughs}",
            tag="ReportMaking"
        )
        print(f"No records in 3h window. Peaks: {summary_peaks}, Troughs: {summary_troughs}")
        return absolute_peaks, absolute_troughs

    # Tìm candidate và thêm nếu vượt delta
    candidate = max(window_recs, key=lambda r: r.water_level_0)
    if abs(candidate.water_level_0 - last_variable) > delta and inner_start < candidate.date_time <inner_end:
        # Chỉ thêm nếu candidate nằm trong khoảng 30 phút trước và sau:
        absolute_peaks.append(candidate)
    candidate = min(window_recs, key=lambda r: r.water_level_0)
    
    if abs( candidate.water_level_0 - last_variable) > delta and inner_start < candidate.date_time <inner_end:
        absolute_troughs.append(candidate)

    # Cuối cùng: log + print summary rồi return
    summary_peaks   = [(r.date_time.strftime('%Y-%m-%d %H:%M'), r.water_level_0) for r in absolute_peaks]
    summary_troughs = [(r.date_time.strftime('%Y-%m-%d %H:%M'), r.water_level_0) for r in absolute_troughs]
    LoggerFactory().add_log(
        "INFO",
        f"Updated points. Peaks: {summary_peaks}, Troughs: {summary_troughs}",
        tag="ReportMaking"
    )
    print(f"Updated points. Peaks: {summary_peaks}, Troughs: {summary_troughs}")

    return absolute_peaks, absolute_troughs

def filter_peaks_troughs(
    absolute_peaks: List[WaterRecord],
    absolute_troughs: List[WaterRecord],
) -> List[Tuple[WaterRecord, str]]:
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
    all_pt: List[Tuple[WaterRecord, str]] = (
        [(r, 'peak') for r in absolute_peaks] +
        [(r, 'trough') for r in absolute_troughs]
    )
    all_pt.sort(key=lambda x: x[0].date_time)

    # 2) Duyệt và gộp những nhóm cùng loại liên tiếp
    filtered: List[Tuple[WaterRecord, str]] = []
    i = 0
    n = len(all_pt)

    while i < n:
        rec_i, type_i = all_pt[i]
        # nhóm bắt đầu tại i
        group = [rec_i]
        j = i + 1
        # thu thập hết nhóm cùng type
        while j < n and all_pt[j][1] == type_i:
            group.append(all_pt[j][0])
            j += 1
        if(len(group) == 0):
            i = j
            continue
        # nếu là peak, chọn peak cao nhất; nếu trough, chọn trough thấp nhất
        if len(group) > 1 and type_i == 'peak':
            
            best = max(group, key=lambda r: r.water_level_0)
            LoggerFactory().add_log("WARNING",f"Found dubplicate peak, choose the best: {best}")
        elif len(group) > 1:
            best = min(group, key=lambda r: r.water_level_0)
            LoggerFactory().add_log("WARNING",f"Found dubplicate trough, choose the best: {best}")
        filtered.append((best, type_i))
        # tiếp tục từ sau nhóm
        i = j

    return filtered

def trend_detected_processes(
    all_records: List[WaterRecord],
) -> Tuple[List[WaterRecord], List[WaterRecord], str]:
    """
    Xử lý phát hiện xu hướng và đỉnh/đáy từ danh sách bản ghi.
    Trả về danh sách đỉnh, đáy và mã xu hướng.
    """
    # 1) Filter
    print(detect_sine_peaks_troughs(all_records))
    # 1) Phát hiện đỉnh/đáy
    absolute_peaks, absolute_troughs = detect_absolute_peaks_troughs(all_records)
    absolute_peaks, absolute_troughs= check_last_point(all_records, absolute_peaks, absolute_troughs, delta=10)
    filtered = filter_peaks_troughs(absolute_peaks, absolute_troughs)
    LoggerFactory().add_log("INFO", f"Absolute peaks after filtered: {absolute_peaks}", tag="ReportMaking")
    LoggerFactory().add_log("INFO", f"Absolute troughs after filtered: {absolute_troughs}", tag="ReportMaking")
    LoggerFactory().add_log("INFO", f"Filtered peaks/troughs: {filtered}", tag="ReportMaking")
    print(f"Absolute peaks after filtered: {absolute_peaks}")   
    print(f"Absolute troughs after filtered: {absolute_troughs}")
    print(f"Filtered peaks/troughs: {filtered}")
    # 2) Phát hiện xu hướng
    filtered, trend_code ,closest_record= detect_last_trend(all_records, filtered)
    return filtered, trend_code, closest_record