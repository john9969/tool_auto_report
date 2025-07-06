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
    
    def fill_lack_value(self, records: list[WaterRecord]) -> list[WaterRecord]:
        """
        Detect and fill missing 10-minute intervals in a list of WaterRecord.
        Validate water levels against delta and interpolate missing entries.
        """
        
        #pdb.set_trace()  # Debugging breakpoint
        if not records:
            print("No records to filter")
            self.logger.add_log("WARNING", "No records to filter", tag="FilterWaterLevel")
            return []
        # Ensure sorted
        
        new_records = sorted(records, key=lambda r: r.date_time)
        if(new_records != records):
            self.logger.add_log("BUG", "Records were not sorted, sorting them now", tag="FilterWaterLevel")
            self.logger.add_log("BUG",f"original data get from server: {records}", tag="FilterWaterLevel")
            self.logger.add_log("BUG", f"sorted data: {new_records}", tag="FilterWaterLevel")
            print("Records were not sorted, sorting them now")
            records = new_records
        filled = []
        for i in range(len(records) - 1):
            current = records[i]
            if getattr(current, 'water_level_0') == -9999:
                self.logger.add_log("WARNING", f"Record {current} has water_level_0 set to -9999, skipping", tag="FilterWaterLevel")
                print(f"Skipping record {current} with water_level_0 = -9999")
                continue
            next_rec = records[i + 1]
            filled.append(current)
            interval = next_rec.date_time.minute - current.date_time.minute
            if interval < 0:
                interval += 60
            steps = int(interval // 10)
            self.logger.add_log("INFO", f"Processing record[{i+1}]: current: {current}, next: {next_rec}, interval: {interval} minutes, steps: {steps}", tag="FilterWaterLevel")
            print(f"Processing record[{i+1}]: {current}, next: {next_rec}, interval: {interval} minutes, steps: {steps}")
            max_delta = self.delta * (steps if steps > 1 else 1)
            # Validate next_rec
            valid = False
            for attr in ['water_level_0', 'water_level_1', 'water_level_2']:
                curr_val = getattr(current, 'water_level_0')
                next_val = getattr(next_rec, attr)
                if abs(next_val - curr_val) <= max_delta:
                    if attr != 'water_level_0':
                        setattr(next_rec, 'water_level_0', next_val)
                        self.logger.add_log("WARNING", f"water_level_0 adjusted to {next_val} from {attr}", tag="FilterWaterLevel")
                        print(f"Adjusted water_level_0 using {attr}: {next_val}")
                    valid = True
                    break

            if not valid:
                self.logger.add_log("WARNING", f"Element {next_rec} is out of range, setting to -9999", tag="FilterWaterLevel")
                print(f"Set water_level_0/1/2 at index {i+1} to -9999")
                for attr in ['water_level_0', 'water_level_1', 'water_level_2']:
                    setattr(next_rec, attr, -9999)
            else :
                self.logger.add_log("INFO", f"Element {next_rec} is OK", tag="FilterWaterLevel")            # Insert missing
            if steps != 1: self.logger.add_log("WARNING", f"There are {steps} missing records between {current.date_time} and {next_rec.date_time}", tag="FilterWaterLevel")
            for step in range(1, steps):
                self.logger.add_log("INFO", f"--------------Start inserting record at step {step} \ {steps}-----------------", tag="FilterWaterLevel")
                missing_time = current.date_time + timedelta(minutes=10 * step)
                fraction = step / steps
                # Interpolation for each level
                def interpolate(curr, next_):
                    val_next = next_ if next_ != -9999 else curr
                    return int(val_next * fraction + curr * (1 - fraction))

                wl0 = interpolate(current.water_level_0, next_rec.water_level_0)
                wl2 = wl1 = wl0
                vol = next_rec.vol * fraction + current.vol * (1 - fraction)
                
                new_rec = WaterRecord(
                    id=-1,
                    serial_number=current.serial_number,
                    date_time=missing_time,
                    water_level_0=wl0,
                    water_level_1=wl1,
                    water_level_2=wl2,
                    vol=vol
                )
                self.logger.add_log("INFO", f"Finish inserting missing record at {missing_time}: {new_rec}", tag="FilterWaterLevel")
                print(f"Inserted missing record at {missing_time}: {new_rec}")
                filled.append(new_rec)
        filled.append(records[-1])
        self.logger.add_log("INFO", f"Filtering complete, total records: {len(filled)}", tag="FilterWaterLevel")
        self.logger.add_log("INFO", f"Filtered data: {filled}", tag="FilterWaterLevel")
        return filled