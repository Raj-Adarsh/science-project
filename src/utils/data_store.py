import redis
import uuid
import json
import os
from generated.heartrate_service_pb2 import HeartRateMeasurement, HeartRateStats, AlertType
from src.utils import metrics

class RedisDataStore:
    def __init__(self, redis_url=None):
        if redis_url is None:
            redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
        self.redis = redis.StrictRedis.from_url(redis_url, decode_responses=True)
        self.key = "heart_rate_measurements"  # Redis key to store measurements

    def save_measurement(self, bpm, timestamp):
        measurement_id = str(uuid.uuid4())
        triggered_alert = (bpm < 50 or bpm > 150)
        measurement = {
            "id": measurement_id,
            "bpm": bpm,
            "timestamp": timestamp,
            "triggered_alert": triggered_alert
        }
        # Append the measurement as a JSON string to the Redis list.
        self.redis.rpush(self.key, json.dumps(measurement))
        # Record metrics if alert is triggered
        if triggered_alert:
            if bpm < 50:
                metrics.record_alert(AlertType.Name(AlertType.LOW_HEART_RATE))
            else:  # bpm > 150
                metrics.record_alert(AlertType.Name(AlertType.HIGH_HEART_RATE))

        return measurement_id

    def get_recent_measurements(self, count):
        # Get the last 'count' items from the list.
        items = self.redis.lrange(self.key, -count, -1)
        measurements = []
        for item in items:
            data = json.loads(item)
            m = HeartRateMeasurement(
                bpm=data["bpm"],
                timestamp=data["timestamp"],
                triggered_alert=data["triggered_alert"]
            )
            measurements.append(m)
        return measurements

    def clear_all_measurements(self):
        self.redis.delete(self.key)
        return True

    def get_alert_status(self):
        # Check all stored measurements for alert conditions.
        items = self.redis.lrange(self.key, 0, -1)
        if not items:
            return False, AlertType.NONE

        high_alert = any(json.loads(item)["bpm"] > 150 for item in items)
        low_alert = any(json.loads(item)["bpm"] < 50 for item in items)

        if high_alert:
            return True, AlertType.HIGH_HEART_RATE
        elif low_alert:
            return True, AlertType.LOW_HEART_RATE
        else:
            return False, AlertType.NONE

    def get_stats(self, measurements):
        if not measurements:
            return HeartRateStats(average_bpm=0.0, min_bpm=0, max_bpm=0)
        bpms = [m.bpm for m in measurements]
        avg_bpm = sum(bpms) / len(bpms)
        min_bpm = min(bpms)
        max_bpm = max(bpms)
        return HeartRateStats(average_bpm=avg_bpm, min_bpm=min_bpm, max_bpm=max_bpm)

# Lazy Singleton for the DataStore
_data_store = None

def get_data_store():
    global _data_store
    if _data_store is None:
        redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
        _data_store = RedisDataStore(redis_url)
    return _data_store
