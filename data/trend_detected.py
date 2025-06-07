from typing import List, Tuple

def detect_trend_and_extrema(
    data: List[float],
    step: int = 6
) -> Tuple[List[int], List[int], List[int]]:
    """
    Args:
      data : danh sách giá trị sensor
      step : khoảng cách i → i+step để tính hiệu số (mặc định 6)

    Trả về:
      trends : list cùng độ dài với data, chứa {+1, -1, 0} cho mỗi i
      peaks   : danh sách các chỉ số i của đỉnh
      troughs : danh sách các chỉ số i của đáy
    """
    n = len(data)
    # 1) Tính xu hướng
    trends = [0] * n
    for i in range(n - step):
        diff = data[i + step] - data[i]
        if diff > 0:
            trends[i] = 1
        elif diff < 0:
            trends[i] = -1
        else:
            trends[i] = 0
    # Với các i cuối (i >= n-step), giữ 0 hoặc có thể lặp lại giá trị trước đó
    for i in range(n - step, n):
        trends[i] = 0

    peaks = []
    troughs = []

    # 2) Tìm điểm chuyển xu hướng
    #    Khi trends[i] > 0 và trends[i+1] < 0 ⇒ đỉnh
    #    Khi trends[i] < 0 và trends[i+1] > 0 ⇒ đáy
    for i in range(n - step - 1):
        # xác định vùng cửa sổ để tìm max/min
        start = i + 1
        end = min(n - 1, i + step)

        if trends[i] > 0 and trends[i + 1] < 0:
            # đỉnh: giá trị max trong data[start:end+1]
            window = data[start:end + 1]
            # argmax thủ công (với list)
            rel_idx = max(range(len(window)), key=lambda k: window[k])
            peaks.append(start + rel_idx)

        elif trends[i] < 0 and trends[i + 1] > 0:
            # đáy: giá trị min trong data[start:end+1]
            window = data[start:end + 1]
            rel_idx = min(range(len(window)), key=lambda k: window[k])
            troughs.append(start + rel_idx)

    return trends, peaks, troughs


# -----------------------
# Ví dụ minh hoạ
# -----------------------
if __name__ == "__main__":
    import numpy as np

    # Tạo tín hiệu sine + noise
    t = np.linspace(0, 4 * np.pi, 200)
    raw = list(np.sin(2 * t) + 0.1 * np.random.randn(len(t)))

    trends, peaks, troughs = detect_trend_and_extrema(raw, step=6)

    print("Xu hướng (đầu 30 giá trị):", trends[:30])
    print("Chỉ số đỉnh tìm được:", peaks)
    print("Chỉ số đáy tìm được:", troughs)
