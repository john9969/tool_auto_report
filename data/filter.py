from datetime import datetime,timedelta
from scipy.signal import savgol_filter
from logger.logger import LoggerFactory
from data.data_handler import WaterRecord
import numpy as np
from config import DElTA
from statistics import median
WINDOW = 7
THRESH = 300
MAX_WATER_LEVEL = 9000  # Maximum water level to consider
class FilterWaterLevel:
    def __init__(self):
        self.delta = DElTA
        self.logger = LoggerFactory()
    

    def detect_outlier_by_median(self, records: list[WaterRecord]) -> list[WaterRecord]:
        window=WINDOW
        thresh=THRESH
        cleaned = []
        half = window // 2
        water_before = [r.water_level_0 for r in records]
        self.logger.add_log("INFO",f"Before detect outlines by median data: {water_before}")
        #pdb.set_trace()  # Debugging breakpoint
        for i in range(len(records)):
            neighbors = []
            # Trường hợp đầu tiên → lấy phải và không lấy trái
            if i < half:
                #self.logger.add_log("INFO", f"Processing left border, index: {i}", tag="FilterWaterLevel")
                right = min(len(records), i + window)
                neighbors = records[i+1:right]
            # Trường hợp cuối cùng → lấy trái và không lấy phải
            elif i >= len(records) - half:
                #self.logger.add_log("INFO", f"Processing right border, index: {i}", tag="FilterWaterLevel")
                left = max(0, i - window)
                neighbors = records[left:i]
            # Trường hợp bình thường → lấy trái và phải
            else:
                #self.logger.add_log("INFO", f"Processing middle, index: {i}", tag="FilterWaterLevel")
                left = i - half
                right = i + half + 1
                neighbors = records[left:i] + records[i+1:right]

            if not neighbors:
                self.logger.add_log("BUG", f"No neighbors found for index {i}, keeping original record", tag="FilterWaterLevel")
                cleaned.append(records[i])  # không có gì để so, giữ nguyên
                continue
            
            list_median = [getattr(it, 'water_level_0') for it in neighbors]
            med = median( list_median)
            if abs( getattr(records[i],'water_level_0') - med) > thresh:
                self.logger.add_log("WARNING", f"Outlier detected at index {i}, value: {getattr(records[i],'water_level_0')}, median: {med}", tag="FilterWaterLevel")
                #cleaned.append(None)  # hoặc giá trị thay thế
            else:
                #self.logger.add_log("INFO", f"Added at index {i} is within threshold, value: {getattr(records[i],'water_level_0')}, median: {med}", tag="FilterWaterLevel")
                cleaned.append(records[i])
        water_after = [r.water_level_0 for r in cleaned]
        self.logger.add_log("INFO",f"After detect outlines by median data: {water_after}")
        self.logger.add_log("INFO", f"Data after fill, total records: {len(cleaned)}", tag="FilterWaterLevel")
        return cleaned
   