from __future__ import annotations
import re
import json
from dataclasses import dataclass
from typing import Optional, List
from bs4 import BeautifulSoup
from datetime import datetime, timezone, timedelta
Hour_Delta = 72
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
    records = data.get("Data", [])

    if not records:
        return None

    # Sắp xếp theo DateCreate (mới nhất trước)
    records.sort(key=lambda x: datetime.fromisoformat(x["DateCreate"].replace("Z", "+00:00")), reverse=True)
    bac_value = records[0].get("BAC", 0)
    # Lấy BAC của bản ghi đầu tiên (mới nhất)
    return round(float(bac_value))