from dataclasses import dataclass
from datetime import datetime
from logger.logger import LoggerFactory

@dataclass
class WaterRecord:
    date_time: datetime
    water_level_0: int
    water_level_1: int
    water_level_2: int

class DataProcessor:
    def __init__(self):
        self.logger = LoggerFactory()
        self.buffer: list[WaterRecord] = []
    def clear(self):
        """
        Clear the buffer of WaterRecord instances.
        """
        self.buffer.clear()
        self.logger.add_log("INFO", "Buffer cleared", tag="DataProcessor")
    def process(self, data):
        """
        Convert list of JSON dicts into WaterRecord instances, buffer them,
        and log each step.
        """
        if not isinstance(data, list):
            self.logger.add_log("WARNING", "Input data is not a list", tag="DataProcessor")
            return []

        for index, item in enumerate(data):
            try:
                record = WaterRecord(
                    date_time=datetime.strptime(item.get("thoigianReport", ""), "%Y-%m-%dT%H:%M:%S"),
                    water_level_0=int(item.get("mucNuoc", 0)*10),
                    water_level_1=int(item.get("mucNuoc", 0)*10),
                    water_level_2=int(item.get("mucNuoc", 0)*10)
                )
                if(record.water_level_0 > 0):
                    self.buffer.append(record)
                    
                self.logger.add_log("INFO", f"Buffered record[{index}]: {record}", tag="DataProcessor")
            except Exception as e:
                self.logger.add_log("BUG", f"Failed to parse record[{index}]: {e}", tag="DataProcessor")
        self.buffer.reverse()
        self.logger.add_log("INFO", f"Total records buffered: {len(self.buffer)}", tag="DataProcessor")
        return self.buffer