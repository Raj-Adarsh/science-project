import uuid
from proto.heartrate_service_pb2 import HeartRateMeasurement, HeartRateStats, AlertType

class InMemoryDataStore:
    def __init__(self):
        self.measurements = []  # Stored as list of tuples: (measurement_id, HeartRateMeasurement)

    def save_measurement(self, bpm, timestamp):
        measurement_id = str(uuid.uuid4())
        triggered_alert = (bpm < 50 or bpm > 150)
        measurement = HeartRateMeasurement(
            bpm=bpm,
            timestamp=timestamp,
            triggered_alert=triggered_alert
        )
        self.measurements.append((measurement_id, measurement))
        return measurement_id

    def get_recent_measurements(self, count):
        # Return only the HeartRateMeasurement parts from the stored tuples
        return [m for _, m in self.measurements[-count:]]
    
    def clear_all_measurements(self):
        """
        Clear all stored measurements from the data store.
        """
        self.measurements = []
        return True 

    # def calculate_stats(self, measurements):
    #     if not measurements:
    #         return HeartRateStats(
    #             average_bpm=0.0,
    #             min_bpm=0,
    #             max_bpm=0
    #         )
    #     bpms = [m.bpm for m in measurements]
    #     avg_bpm = sum(bpms) / len(bpms)
    #     min_bpm = min(bpms)
    #     max_bpm = max(bpms)
    #     return HeartRateStats(
    #         average_bpm=avg_bpm,
    #         min_bpm=min_bpm,
    #         max_bpm=max_bpm
    #     )
        
    def get_alert_status(self):
        """
        Returns a tuple (alert_active, alert_type) based on stored measurements.
        - If any measurement has bpm > 150, a high alert is active.
        - Else if any measurement has bpm < 50, a low alert is active.
        - Otherwise, no alert is active.
        """
        if not self.measurements:
            return False, AlertType.NONE

        # Check all stored measurements
        high_alert = any(m.bpm > 150 for _, m in self.measurements)
        low_alert = any(m.bpm < 50 for _, m in self.measurements)

        if high_alert:
            return True, AlertType.HIGH_HEART_RATE
        elif low_alert:
            return True, AlertType.LOW_HEART_RATE
        else:
            return False, AlertType.NONE

    def get_stats(self, measurements):
        """
        Calculate statistics (average, min, and max bpm) for the given list of measurements.
        """
        if not measurements:
            return HeartRateStats(average_bpm=0.0, min_bpm=0, max_bpm=0)
        bpms = [m.bpm for m in measurements]
        avg_bpm = sum(bpms) / len(bpms)
        min_bpm = min(bpms)
        max_bpm = max(bpms)
        return HeartRateStats(average_bpm=avg_bpm, min_bpm=min_bpm, max_bpm=max_bpm)

#Lazy Singleton Object for DataStore
_data_store = None

def get_data_store():
    global _data_store
    if _data_store is None:
        _data_store = InMemoryDataStore()
    return _data_store
