'''
Receives individual heart rate measurements, validates them, and
processes them according to the specifications.
'''

from generated import heartrate_service_pb2 as pb2
from src.utils import logger, data_store

class SubmitHeartrateHandler:
    def __init__(self):
        # self.heart_rate_monitor = heart_rate_monitor
        self.log = logger.get_logger(__name__)
        self.store = data_store.get_data_store()
        
    def handle(self, request, context):
        try:    
            bpm = request.bpm
            timestamp = request.timestamp
            
            # Validate heart rate -> 40-180 is normal for adults
            if bpm < 40 or bpm > 180:
                self.log.warning("Received out-of-range heart rate: %d", bpm)
                return pb2.HeartRateResponse(
                    success=False, 
                    error="Heart rate out of typical range for an adult", 
                    alert_triggered=False, 
                    alert_type=pb2.AlertType.NONE
                )
            
            # Save the bpm measurement - Use measurement id to store and track the data (UUID)
            measurement_id = self.store.save_measurement(bpm, timestamp)
            self.log.info("SubmitHeartrateHandler: Saved bpm measurement with ID %s for bpm %d at %s", measurement_id, bpm, timestamp)
            
            # Check for alerts
            alert_triggered = (bpm < 50 or bpm > 150)
            alert_type = (pb2.AlertType.Value("LOW_HEART_RATE") if bpm < 50
              else pb2.AlertType.Value("HIGH_HEART_RATE") if bpm > 150
              else pb2.AlertType.Value("NONE"))
            self.log.info("SubmitHeartrateHandler: Received bpm measurement: %d at %s, alert: %s", bpm, timestamp, alert_triggered)
            return pb2.HeartRateResponse(
                success=True, 
                error="", 
                alert_triggered=alert_triggered, 
                alert_type=alert_type
            )
        except Exception as e:
                self.log.error("SubmitHeartrateHandler: Error processing BPM measurement: %s", str(e))
                return pb2.HeartRateResponse(
                    success=False, 
                    error="Internal server error processing measurement", 
                    alert_triggered=False, 
                    alert_type=pb2.AlertType.NONE
                )
