from network.fetcher import DataFetcher
from data.data_handler import DataProcessor
from logger.logger import LoggerFactory
# from notify.telegram_bot import TelegramNotifier
from automation.selenium_controller import SeleniumController
from data.filter import FilterWaterLevel
from data.trend_detected import *
from data.report_making import make_report
import requests
import time
from datetime import datetime, timedelta

#from startup.auto_start import AutoStartManager
logger = LoggerFactory()
fetcher = DataFetcher()
processor = DataProcessor()
automation = SeleniumController()
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
        data = fetcher.fetch()
        if not data:
            logger.add_log("WARNING", "No data fetched", tag="Main")
            return
        # data = fetcher.fetch_test()  # Uncomment for testing
        result = processor.process(data)
        if not result:
            logger.add_log("WARNING", "No records processed", tag="Main")
            print("No records processed")
            return
        result = filterWaterLevel.detect_outlier_by_median(result)
        for i in result:
            logger.add_log("INFO", f"Record: {i}", tag="Main")
            print(f"Record: {i}")
        filtered,trend_code, closest_record = trend_detected_processes(result)
        report = make_report( filtered,trend_code, closest_record)
        print(f"Report: {report}")
        logger.add_log("INFO", f"report:{report}", tag="Main")
        if(datetime.now().hour == 1 or datetime.now().hour == 7 or datetime.now().hour == 13 or datetime.now().hour == 19):
            report = f"Điện báo lúc {datetime.now().strftime('%H')} giờ: " + report
        else:
            report = "checking"
        payload = {'text': report}
        try:
            response = requests.post("https://donuoctrieuduong.xyz/water_level_api/test/update_water.php", json=payload)
            response.raise_for_status()  # ném exception nếu status != 2xx
            processor.clear()  # Xoá bộ đệm sau khi xử lý xong
            # Nếu API trả về JSON, parse và trả về
            return response.json()
        except requests.RequestException as e:
            print(f"Request failed: {e}")
            processor.clear()  # Xoá bộ đệm sau khi xử lý xong
            return None
        
        #notifier.send(f"Result: {result}")
        #automation.run()
    except Exception as e:
        logger.add_log("BUG", str(e), tag="Main")
        processor.clear()

if __name__ == "__main__":
 #   startup.add_to_startup()
    #run_every_hour(main)
    main()