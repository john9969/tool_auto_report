from __future__ import annotations
import re
import json
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo  # Python 3.9+
from config import DELTA_MINUTE_EARLY
Hour_Delta = 100
def read_rain_level(filename: str = "rain_level.txt") -> float:
    """
    Đọc dữ liệu mưa từ file có format { rain_level_19h: <số> }
    Trả về giá trị float.
    """
    try:
        with open(filename, "r", encoding="utf-8") as f:
            content = f.read().strip()
        # content ví dụ: "{ rain_level_19h: 25.7 }"
        # Tách phần số
        level_str = content.split(":")[1].replace("}", "").strip()
        print(f"Rain level from file: {float(level_str):.2f}")
        return float(level_str)
    except (FileNotFoundError, ValueError, IndexError) as e:
        print(f"error when read file {filename}: {e}")
        return 0.0
def write_rain_level(level: float, filename: str = "rain_level.txt"):
    """
    Ghi dữ liệu mưa vào file với định dạng { rain_level_19h: <số> }

    :param level: Số liệu mưa (float hoặc int)
    :param filename: Tên file lưu dữ liệu
    """
    data = f"{{ rain_level_19h: {level} }}\n"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(data)
    print(f"Done update rain_level {filename}: {data.strip()}")
@dataclass
class WaterRecord:
    date_time: datetime
    water_level_0:int

_DT_FMT = re.compile(r"^\d{2}/\d{2}/\d{4}$")

def _to_int_or_none(s: str) -> Optional[int]:
    s = (s or "").strip()
    if not s:
        return None
    try:
        return int(s)
    except ValueError:
        return None

def parse_water_records_range(html: str) -> List[WaterRecord]:
    """
    Duyệt từ trên xuống dưới, lấy các hàng có pattern:
      <td>HH</td><td>dd/mm/YYYY</td>
    rồi lấy mốc phút 0/10/20/30/40/50.
    Chỉ trả về các bản ghi có datetime trong [now-20h, now] (GMT+7).
    """
    tz = timezone(timedelta(hours=7))
    now = datetime.now(tz)
    start = now - timedelta(hours=Hour_Delta)

    soup = BeautifulSoup(html, "html.parser")
    out: List[WaterRecord] = []

    # Duyệt từng hàng theo thứ tự xuất hiện
    for tr in soup.select("tr"):
        tds = tr.select("td.NormalPC")
        if len(tds) < 3:
            continue

        # Tìm cặp liên tiếp (hour -> date) theo yêu cầu
        hour_idx = None
        date_idx = None

        for i in range(len(tds) - 1):
            txt_i = tds[i].get_text(strip=True)
            txt_j = tds[i+1].get_text(strip=True)

            h = _to_int_or_none(txt_i)
            if h is not None and 0 <= h <= 23 and _DT_FMT.match(txt_j or ""):
                hour_idx, date_idx = i, i+1
                break

        # Nếu không tìm được đúng thứ tự, thử fallback (date -> hour) cho an toàn
        if hour_idx is None:
            for i in range(len(tds) - 1):
                txt_i = tds[i].get_text(strip=True)
                txt_j = tds[i+1].get_text(strip=True)

                if _DT_FMT.match(txt_i or ""):
                    h = _to_int_or_none(txt_j)
                    if h is not None and 0 <= h <= 23:
                        date_idx, hour_idx = i, i+1
                        break

        if hour_idx is None or date_idx is None:
            continue

        # Parse date & hour
        date_str = tds[date_idx].get_text(strip=True)
        hour_val = _to_int_or_none(tds[hour_idx].get_text(strip=True))
        if hour_val is None:
            continue

        try:
            d = datetime.strptime(date_str, "%d/%m/%Y").date()
        except ValueError:
            continue

        # Vị trí cột đầu tiên của mực nước
        first_water_col = max(hour_idx, date_idx) + 1
        # Map phút -> offset cột: 0, +2, +4, +6, +8, +10
        minute_steps = [0, 2, 4, 6, 8, 10]

        for step_idx, minute in enumerate([0, 10, 20, 30, 40, 50]):
            col_idx = first_water_col + minute_steps[step_idx]
            if col_idx >= len(tds):
                continue
            wl = _to_int_or_none(tds[col_idx].get_text())
            if wl is None:
                continue

            dt = datetime(d.year, d.month, d.day, hour_val, minute, tzinfo=tz)
            if start <= dt:
                out.append(WaterRecord(date_time=dt, water_level_0 = (wl*10)))
    # --- Sort và loại trùng ---
    out.sort(key=lambda r: r.date_time)
    unique_records: List[WaterRecord] = []
    seen_dates = set()
    for rec in out:
        if rec.date_time not in seen_dates:
            seen_dates.add(rec.date_time)
            unique_records.append(rec)
            
    return unique_records

def parse_rain_record(json_data:str) -> int:
    # Parse dữ liệu từ JSON nếu là string
    
    
    if isinstance(json_data, str):
        data = json.loads(json_data)
    else:
        data = json_data

    # Lấy danh sách trong "Data"
    records: List[Dict[str, Any]] = data.get("Data", [])

    if not records:
        return 0
    def _parse_iso_utc(s: str) -> datetime:
    # Handle trailing 'Z' and make it timezone-aware UTC
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    BKK = ZoneInfo("Asia/Bangkok")

    enriched: List[Dict[str, Any]] = []
    for r in records:
        dc = r.get("DateCreate")
        if not dc:
            continue
        try:
            dt_utc = _parse_iso_utc(dc)
            dt_local = dt_utc.astimezone(BKK)  # convert to +7
            r["_dt_utc"] = dt_utc
            r["_dt_local"] = dt_local
            enriched.append(r)
        except Exception:
            # Bad timestamp format; skip this record
            continue
    enriched.sort(key=lambda x: x["_dt_utc"])
    # 3) Get the latest record and the record at (latest - 7h)
    latest: Optional[Dict[str, Any]] = enriched[-1] if enriched else None

    def find_at_or_before(target_dt_local: datetime) -> Optional[Dict[str, Any]]:
        """Find the newest record whose local time <= target_dt_local."""
        candidates = [r for r in enriched if r["_dt_local"] <= target_dt_local]
        return candidates[-1] if candidates else None
    hour = (datetime.now() + timedelta(minutes= DELTA_MINUTE_EARLY)).hour
    if hour == 0:
        target_local = latest["_dt_local"] - timedelta(hours=5) #17/08/2025: Thêm sửa báo sai lượng mưa
                                                                #25/08/2025: Thêm phần cộng lượng mưa ngày hôm trước
        print(f"Target_local: {target_local}")
        rec_minus_5h = find_at_or_before(target_local)
        if rec_minus_5h:
            print(f"Rain -7h: {rec_minus_5h.get('BAC', 0)}")
            # print(f"Rain lastest: {latest.get('BAC', 0)}")
            rain_level = latest.get("BAC", 0) - rec_minus_5h.get("BAC", 0)
            write_rain_level(rain_level)
            
    rec_minus_6h: Optional[Dict[str, Any]] = None
    if latest:
        target_local = latest["_dt_local"] - timedelta(hours=6) #17/08/2025: Thêm sửa báo sai lượng mưa
        print(f"Target_local: {target_local}")
        rec_minus_6h = find_at_or_before(target_local)
        if rec_minus_6h:
            print(f"Rain -7h: {rec_minus_6h.get('BAC', 0)}")
            # print(f"Rain lastest: {latest.get('BAC', 0)}")
            rain_level = latest.get("BAC", 0) - rec_minus_6h.get("BAC", 0)
        else:
            rain_level = latest.get("BAC", 0)
    else:
        return 0  
    if hour == 1:
        rain_level += read_rain_level()       
    # Lấy BAC của bản ghi đầu tiên (mới nhất)
    print(f"Rain level: {rain_level}")
    if 0.1 <= rain_level <= 0.4:
        return 9999
    return round(rain_level)