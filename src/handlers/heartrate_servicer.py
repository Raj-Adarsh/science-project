import grpc
import time
from src.utils import metrics
from generated import heartrate_service_pb2_grpc as pb2_grpc
from generated import heartrate_service_pb2 as pb2
from src.handlers.submit_heartrate import SubmitHeartrateHandler
from src.handlers.stream_heartrate import StreamHeartRateHandler
from src.handlers.get_heartrate_status import GetHeartRateStatusHandler
from src.handlers.calculate_exercise_zones import CalculateExerciseZonesHandler

class HeartRateMonitorServicer(pb2_grpc.HeartRateMonitorServicer):
    def __init__(self):
        self.submit_heartrate_handler = SubmitHeartrateHandler()
        self.stream_heartrate_handler = StreamHeartRateHandler()
        self.get_heartrate_status_handler = GetHeartRateStatusHandler()
        self.calculate_exercise_zones_handler = CalculateExerciseZonesHandler()

    def SubmitHeartRate(self, request, context):
        start_time = time.time()
        method = "SubmitHeartRate"
        rpc_type = "unary"
        try:
            response = self.submit_heartrate_handler.handle(request, context)
            status_code = grpc.StatusCode.OK
            return response
        except Exception as e:
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            status_code = grpc.StatusCode.INTERNAL
            return pb2.HeartRateResponse(
                success=False,
                error="Internal error in SubmitHeartRateHandler",
                alert_triggered=False,
                alert_type=pb2.AlertType.NONE
            )
        finally:
            duration = time.time() - start_time
            metrics.observe_rpc_latency(method, rpc_type, duration)
            code = context.code().name if context.code() is not None else "OK"
            metrics.record_rpc_handled(method, rpc_type, code)

    def StreamHeartRate(self, request_iterator, context):
        start_time = time.time()
        method = "StreamHeartRate"
        rpc_type = "stream"
        metrics.increment_active_streams()
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
        finally:
            duration = time.time() - start_time
            metrics.observe_rpc_latency(method, rpc_type, duration)
            code = context.code().name if context.code() is not None else "OK"
            metrics.record_rpc_handled(method, rpc_type, code)
            metrics.decrement_active_streams()

    def GetHeartRateStatus(self, request, context):
        start_time = time.time()
        method = "GetHeartRateStatus"
        rpc_type = "unary"
        try:
            response = self.get_heartrate_status_handler.get_status(request, context)
            status_code = grpc.StatusCode.OK
            return response
        except Exception as e:
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            status_code = grpc.StatusCode.INTERNAL
            return pb2.StatusResponse(
                recent_measurements=[],
                alert_active=False,
                alert_type=pb2.AlertType.NONE,
                stats=pb2.HeartRateStats(average_bpm=0.0, min_bpm=0, max_bpm=0)
            )
        finally:
            duration = time.time() - start_time
            metrics.observe_rpc_latency(method, rpc_type, duration)
            code = context.code().name if context.code() is not None else "OK"
            metrics.record_rpc_handled(method, rpc_type, code)

    def CalculateExerciseZones(self, request, context):
        start_time = time.time()
        method = "CalculateExerciseZones"
        rpc_type = "unary"
        try:
            response = self.calculate_exercise_zones_handler.calculate(request, context)
            if response is None:
                status_code = grpc.StatusCode.INVALID_ARGUMENT
                response = pb2.ExerciseZoneResponse(
                    zone1_time=0,
                    zone2_time=0,
                    zone3_time=0,
                    total_duration=0,
                    average_heart_rate=0.0
                )
            else:
                status_code = grpc.StatusCode.OK
            return response
        except Exception as e:
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            status_code = grpc.StatusCode.INTERNAL
            return pb2.ExerciseZoneResponse(
                zone1_time=0,
                zone2_time=0,
                zone3_time=0,
                total_duration=0,
                average_heart_rate=0.0
            )
        finally:
            duration = time.time() - start_time
            metrics.observe_rpc_latency(method, rpc_type, duration)
            code = context.code().name if context.code() is not None else "OK"
            metrics.record_rpc_handled(method, rpc_type, code)
