from network.fetcher import DataFetcher
from data.data_handler import DataProcessor
from logger.logger import LoggerFactory
from notify.telegram_bot import TelegramNotifier
from automation.selenium_controller import SeleniumController
from data.filter import FilterWaterLevel
#from startup.auto_start import AutoStartManager
logger = LoggerFactory()
fetcher = DataFetcher()
processor = DataProcessor()
notifier = TelegramNotifier()
automation = SeleniumController()
filterWaterLevel = FilterWaterLevel()
#startup = AutoStartManager()

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
            
        notifier.send(f"Result: {result}")
        automation.run()
    except Exception as e:
        logger.add_log("BUG", str(e), tag="Main")

if __name__ == "__main__":
 #   startup.add_to_startup()
    main()