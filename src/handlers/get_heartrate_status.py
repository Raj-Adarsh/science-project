'''
Returns the current status of heart rate monitoring, including
the recent measurements and any active alerts.
'''
import grpc
from generated import heartrate_service_pb2 as pb2
from src.utils import logger, data_store

class GetHeartRateStatusHandler:
    def __init__(self):
        self.log = logger.get_logger(__name__)
        self.store = data_store.get_data_store()
        self.log.info("GetHeartRateStatusHandler initialized")
        
    def get_status(self, request, context):
        try:
            recent_count = request.recent_count
            self.log.info("GetHeartRateStatusHandler: Retrieving %d recent measurements", recent_count)
            
            # Retrieve recent measurements
            recent_measurements = self.store.get_recent_measurements(recent_count)
            
            # Calling the store method for alert as expected by tests.
            alert_active, alert_type = self.store.get_alert_status()
            stats = self.store.get_stats(recent_measurements)
            self.log.info("GetHeartRateStatusHandler: Found %d measurements, alert_active: %s", len(recent_measurements), alert_active)
            
            return pb2.StatusResponse(
                alert_active=alert_active,
                alert_type=alert_type,
                recent_measurements=recent_measurements,
                stats=stats
            )
        except Exception as e:
            self.log.error("GetHeartRateStatusHandler: Error retrieving heart rate status: %s", str(e))
            context.set_details(f"Internal server error in GetHeartRateStatusHandler: {str(e)}")
            context.set_code(grpc.StatusCode.INTERNAL)
            # Return a default StatusResponse in case of error
            return pb2.StatusResponse(
                recent_measurements=[],
                alert_active=False,
                alert_type=pb2.AlertType.NONE,
                stats=pb2.HeartRateStats(average_bpm=0.0, min_bpm=0, max_bpm=0)
            )
        