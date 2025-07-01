from dataclasses import dataclass
from datetime import datetime
from logger.logger import LoggerFactory

@dataclass
class WaterRecord:
    id: int
    serial_number: str
    date_time: datetime
    water_level_0: int
    water_level_1: int
    water_level_2: int
    vol: float

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
                    id=int(item.get("id", 0)),
                    serial_number=item.get("serial_number", ""),
                    date_time=datetime.strptime(item.get("created_at", ""), "%Y-%m-%d %H:%M:%S"),
                    water_level_0=int(item.get("water_lever_0", item.get("water_level_0", 0))),
                    water_level_1=int(item.get("water_lever_1", item.get("water_level_1", 0))),
                    water_level_2=int(item.get("water_lever_2", item.get("water_level_2", 0))),
                    vol=float(item.get("vol", 0))
                )
                self.buffer.append(record)
                self.logger.add_log("INFO", f"Buffered record[{index}]: {record}", tag="DataProcessor")
            except Exception as e:
                self.logger.add_log("BUG", f"Failed to parse record[{index}]: {e}", tag="DataProcessor")

        self.logger.add_log("INFO", f"Total records buffered: {len(self.buffer)}", tag="DataProcessor")
        return self.buffer