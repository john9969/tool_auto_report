from data.data_process import parse_water_records_range,parse_rain_record
from logger.logger import LoggerFactory
from automation.selenium_controller import selenium_controller
from data.filter import FilterWaterLevel
from data.trend_detected import *
from network.fetcher import API
from data.report_making import make_report
import requests
from config import API_URL_GET_WATER_LEVEL,API_URL_GET_RAIN_LEVEL
import traceback
import time
from datetime import datetime, timedelta

logger = LoggerFactory()
filterWaterLevel = FilterWaterLevel()
def run_every_hour(task_func):

    while True:
        now = datetime.now()
        # Tính thời điểm đầu giờ kế tiếp
        next_hour = (now + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
        wait_seconds = (next_hour - now).total_seconds()
        print(f"[{now.strftime('%Y-%m-%d %H:%M:%S')}] waiting time {wait_seconds:.0f}s for next task...")
        time.sleep(wait_seconds)
        #time.sleep(1)
        # Gọi hàm nhiệm vụ
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Running task...")
        try:
            task_func()
        except Exception as e:
            print(f"Error: {e}")
            
def main():
    try:
        logger.add_log("INFO", "**********************START MAIN APP**********************", tag="Main")
        api_get_water_level = API(API_URL_GET_WATER_LEVEL)
        api_get_rain_level = API(API_URL_GET_RAIN_LEVEL)
        water_html_data = api_get_water_level.fetch()
        rain_json_data = api_get_rain_level.fetch()
        
        if not water_html_data:
            logger.add_log("WARNING", "No data fetched", tag="Main")
            return
        # data = fetcher.fetch_test()  # Uncomment for testing
        all_records = parse_water_records_range(water_html_data)
        rain_record = parse_rain_record(rain_json_data)
        if not all_records:
            logger.add_log("WARNING", "No records processed", tag="Main")
            print("No records processed")
            return
        #for water in all_records:
            #print(f"date: {water.date_time} water:{water.water_level_0}")
        all_records = filterWaterLevel.detect_outlier_by_median(all_records)
        for i in all_records:
            logger.add_log("INFO", f"Record: {i}", tag="Main")
            #print(f"Record: {i}")
        list_report_point = trend_detected_processes(all_records)
        report = make_report(list_report_point,rain_record)
        print(f"Report: {report}")
        logger.add_log("INFO", f"report:{report}", tag="Main")
        if(datetime.now().hour == 1 or datetime.now().hour == 7 or datetime.now().hour == 13 or datetime.now().hour == 19):
            report
        else:
            report = "checking"
        payload = {'text': "Trạm hà nội " + report}
        selenium_controller(report)
        try:
            response = requests.post("https://donuoctrieuduong.xyz/water_level_api/test/update_water.php", json=payload)
            response.raise_for_status()  # ném exception nếu status != 2xx
            # Nếu API trả về JSON, parse và trả về
            
            return response.json()
        except requests.RequestException as e:
            traceback.print_exc()
            print(f"Request failed: {e}")
            return None
        
    except Exception as e:
        logger.add_log("BUG", str(e), tag="Main")
        traceback.print_exc()
if __name__ == "__main__":
 #   startup.add_to_startup()
    #run_every_hour(main)
    main()
