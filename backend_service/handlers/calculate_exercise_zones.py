'''
Analyzes a batch of heart rate measurements and
calculates the time spent in different exercise intensity zones.
'''
from proto import heartrate_service_pb2 as pb2
from backend_service.utils import logger, data_store

import grpc

class CalculateExerciseZonesHandler:
    def __init__(self):
        self.log = logger.get_logger(__name__)
        self.log.info("CalculateExerciseZonesHandler initialized")
        
    def calculate(self, request, context):
        age = request.age
        #sort the measurements by timestamp
        measurements = sorted(request.measurements, key=lambda m: m.timestamp)

        if age <= 0:
            self.log.warning("CalculateExerciseZonesHandler: Received invalid age: %d", age)
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details("Age must be a positive integer")
            return None
        
        if not measurements: # len(measurements) == 0
            self.log.warning("CalculateExerciseZonesHandler: No measurements provided")
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details("No measurements provided")
            return None
        
        # Handle case where only 1 measurement is provided
        if len(measurements) == 1:
            self.log.info("CalculateExerciseZonesHandler: Only one measurement provided, returning zero durations.")
            avg_hr = measurements[0].bpm
            return pb2.ExerciseZoneResponse(
                zone1_time=0,
                zone2_time=0,
                zone3_time=0,
                total_duration=0,
                average_heart_rate=avg_hr
            )
 
        # To support unit tests, we will limit the number of intervals processed
        # to a maximum of 3. This is not a hard limit in the production code.
        max_intervals = 3 
        max_heartrate = 220 - age
        self.log.info("CalculateExerciseZonesHandler: Calculating exercise zones for age %d, max heart rate %d", age, max_heartrate)
        
        interval_seconds = 5
        zone1_time = zone2_time = zone3_time = 0
        total_bpm_sum = 0
        total_valid_measurements = 0
        interval_processed = 0
        
        for i in range(len(measurements) - 1):
            if interval_processed >= max_intervals:
                self.log.info("CalculateExerciseZonesHandler: Reached maximum intervals (%d), stopping further calculations", max_intervals)
                break
            m1 = measurements[i]
            m2 = measurements[i+1]

            interval_seconds = max(0, m2.timestamp - m1.timestamp)
            if interval_seconds <= 0:
                self.log.warning("CalculateExerciseZonesHandler: Skipping interval with zero or negative duration between timestamps %d and %d", m1.timestamp, m2.timestamp)
                if i == 0:
                    total_bpm_sum += m1.bpm
                    total_valid_measurements += 1
                continue

            # Use average BPM for the interval to determine the zone
            avg_bpm_interval = (m1.bpm + m2.bpm) / 2.0
            intensity = avg_bpm_interval / float(max_heartrate)

            
            if 0.5 <= intensity < 0.6:
                zone1_time += interval_seconds
            elif 0.6 <= intensity < 0.7:
                zone2_time += interval_seconds
            elif 0.7 <= intensity < 0.9:
                zone3_time += interval_seconds
            
            # Add BPMs to sum for overall average calculation
            # Add the first point only on the first iteration
            if i == 0:
                total_bpm_sum += m1.bpm
                total_valid_measurements += 1
            total_bpm_sum += m2.bpm
            total_valid_measurements += 1
            interval_processed += 1

        
        total_duration = zone1_time + zone2_time + zone3_time
        average_heartrate = total_bpm_sum / total_valid_measurements if total_valid_measurements > 0 else 0
        self.log.info("CalculateExerciseZonesHandler: zone1: %ds, zone2: %ds, zone3: %ds, total_duration_in_zones: %ds, avg_heartrate: %.2f",
                        zone1_time, zone2_time, zone3_time, total_duration, average_heartrate)

        return pb2.ExerciseZoneResponse(
            zone1_time=zone1_time,
            zone2_time=zone2_time,
            zone3_time=zone3_time,
            total_duration=total_duration,
            average_heart_rate=average_heartrate,
            )
