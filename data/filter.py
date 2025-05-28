from datetime import timedelta
from logger.logger import LoggerFactory
from data.data_handler import WaterRecord
from config import DElTA

import pdb
class FilterWaterLevel:
    def __init__(self):
        self.delta = DElTA
        self.logger = LoggerFactory()

    def fill_lack_value(self, records: list[WaterRecord]) -> list[WaterRecord]:
        """
        Detect and fill missing 10-minute intervals in a list of WaterRecord.
        Validate water levels against delta and interpolate missing entries.
        """
        
        pdb.set_trace()  # Debugging breakpoint
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
            next_rec = records[i + 1]
            filled.append(current)
            interval = (next_rec.date_time - current.date_time).total_seconds() / 60
            steps = int(interval // 10)
            self.logger.add_log("INFO", f"Processing record[{i}]: {current}, next: {next_rec}, interval: {interval} minutes, steps: {steps}", tag="FilterWaterLevel")
            print(f"Processing record[{i}]: {current}, next: {next_rec}, interval: {interval} minutes, steps: {steps}")
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
                self.logger.add_log("WARNING", f"All water levels out of range at index {i+1}, setting to -9999", tag="FilterWaterLevel")
                print(f"Set water_level_0/1/2 at index {i+1} to -9999")
                for attr in ['water_level_0', 'water_level_1', 'water_level_2']:
                    setattr(next_rec, attr, -9999)
            # Insert missing
            for step in range(1, steps):
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
                self.logger.add_log("INFO", f"Inserted missing record at {missing_time}: {new_rec}", tag="FilterWaterLevel")
                print(f"Inserted missing record at {missing_time}: {new_rec}")
                filled.append(new_rec)
        filled.append(records[-1])
        self.logger.add_log("INFO", f"Filtering complete, total records: {len(filled)}", tag="FilterWaterLevel")
        return filled