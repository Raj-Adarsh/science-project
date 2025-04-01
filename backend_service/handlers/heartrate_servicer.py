import grpc
from proto import heartrate_service_pb2 as pb2
from proto import heartrate_service_pb2_grpc as pb2_grpc

from backend_service.handlers.submit_heartrate import SubmitHeartrateHandler
from backend_service.handlers.stream_heartrate import StreamHeartRateHandler
from backend_service.handlers.get_heartrate_status import GetHeartRateStatusHandler
from backend_service.handlers.calculate_exercise_zones import CalculateExerciseZonesHandler

class HeartRateMonitorServicer(pb2_grpc.HeartRateMonitorServicer):
    def __init__(self):
        self.submit_heartrate_handler = SubmitHeartrateHandler()
        self.stream_heartrate_handler = StreamHeartRateHandler()
        self.get_heartrate_status_handler = GetHeartRateStatusHandler()
        self.calculate_exercise_zones_handler = CalculateExerciseZonesHandler()

    def SubmitHeartRate(self, request, context):
        try:
            return self.submit_heartrate_handler.handle(request, context)
        except Exception as e:
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            return pb2.HeartRateResponse(
                success=False, 
                error="Internal error in SubmitHeartRateHandler", 
                alert_triggered=False, 
                alert_type=pb2.AlertType.NONE
            )


    def StreamHeartRate(self, request_iterator, context):
        try:
            for response in self.stream_heartrate_handler.stream(request_iterator, context):
                yield response
        except Exception as e:
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            yield pb2.HeartRateResponse(
                success=False, 
                error="Internal error in StreamHeartRateHandler", 
                alert_triggered=False, 
                alert_type=pb2.AlertType.NONE
            )
    
    def GetHeartRateStatus(self, request, context):
        try:
            return self.get_heartrate_status_handler.get_status(request, context)
        except Exception as e:
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            return pb2.StatusResponse(
                recent_measurements=[], 
                alert_active=False,
                alert_type=pb2.AlertType.NONE,
                stats=pb2.HeartRateStats(
                    average_bpm=0.0,
                    min_bpm=0,
                    max_bpm=0
                )
            )
        
    def CalculateExerciseZones(self, request, context):
        try:
            # Call the handler
            response = self.calculate_exercise_zones_handler.calculate(request, context)
            # If the handler returned None, it already set the error details
            if response is None:
                return pb2.ExerciseZoneResponse(
                    zone1_time=0,
                    zone2_time=0,
                    zone3_time=0,
                    total_duration=0,
                    average_heart_rate=0.0
                )
            
            # Otherwise return the normal response
            return response
        except Exception as e:
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            return pb2.ExerciseZoneResponse(
                zone1_time=0,
                zone2_time=0,
                zone3_time=0,
                total_duration=0,
                average_heart_rate=0.0
            )
