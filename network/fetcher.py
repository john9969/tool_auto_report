import requests
import json
from config import API_URL
MINUTE_DEVIDE = 60*24*4
class DataFetcher:
    def fetch(self):
        """
        Fetch water level data, splitting across month boundary if needed,
        print and log fetched data.
        """
        from datetime import datetime, timedelta
        from logger.logger import LoggerFactory

        logger = LoggerFactory()
        now = datetime.now()
        begin = now - timedelta(minutes=MINUTE_DEVIDE) # time range for fetching data
        serial_number = "TD_MW_0011"

        def build_params(dt_start, dt_end):
            table_name = f"water_level_{dt_end.month:02d}_{dt_end.year}"
            return {
                'table_name': table_name,
                'serial_number': serial_number,
                'date_begin': f"{dt_start.year}-{dt_start.month}-{dt_start.day} {dt_start.hour}:{dt_start.minute}:{dt_start.second}",
                'date_end': f"{dt_end.year}-{dt_end.month}-{dt_end.day} {dt_end.hour}:{dt_end.minute}:{dt_end.second}"
            }

        def fetch_range(dt_start, dt_end):
            params = build_params(dt_start, dt_end)
            print(f"[DataFetcher] Requesting: {params}")
            logger.add_log("INFO", f"Request params: {params}", tag="DataFetcher")
            resp = requests.get(API_URL, params=params)
            resp.raise_for_status()
            data = resp.json()
            #print(f"[DataFetcher] Received {len(data)} records")
            logger.add_log("INFO", f"API: {API_URL}?{requests.compat.urlencode(params)}", tag="DataFetcher")
            logger.add_log("INFO", f"Received {len(data)} records", tag="DataFetcher")
            logger.add_log("INFO", f"Data: {data}", tag="DataFetcher")
            return data

        # Single or split request
        if begin.month == now.month:
            data_pack = fetch_range(begin, now)
        else:
            if(begin.month == 12):
                data_pack_1_end_date = datetime( year=begin.year - 1, month=12, day=31, hour=23, minute=59, second=59)
                data_pack_1_begin_date = begin
                data_pack_2_begin_date = now.replace(month=1, year=now.year, day=1, hour=0, minute=0, second=0)
                data_pack_2_end_date = now
            elif ( begin.month == 1 or begin.month == 3 or begin.month == 5 or begin.month == 7 or begin.month == 8 or begin.month == 10 ):
                data_pack_1_end_date = begin.replace(day=31, hour=23, minute=59, second=59)
                data_pack_1_begin_date = begin
                data_pack_2_begin_date = now.replace(day=1, hour=0, minute=0, second=0)
                data_pack_2_end_date = now
            else:
                data_pack_1_end_date = begin.replace(day=30, hour=23, minute=59, second=59)
                data_pack_1_begin_date = begin
                data_pack_2_begin_date = now.replace(day=1, hour=0, minute=0, second=0)
                data_pack_2_end_date = now
                
            data_pack1 = fetch_range(data_pack_1_begin_date, data_pack_1_end_date)
            data_pack2 = fetch_range(data_pack_2_begin_date, data_pack_2_end_date)
            data_pack= data_pack1 + data_pack2
        return data_pack

    def fetch_test(self, file_path="test/data_test.txt"):
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)