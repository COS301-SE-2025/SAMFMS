"""Scheduling optimization utilities"""

from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum
import asyncio


class Priority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    URGENT = 4


class ScheduleOptimizer:
    """Schedule optimization and conflict resolution utilities"""
    
    def __init__(self):
        self.working_hours_start = 6  # 6 AM
        self.working_hours_end = 22   # 10 PM
        self.max_daily_hours = 10     # Maximum working hours per day
        self.min_break_minutes = 30   # Minimum break between trips
    
    def check_time_conflict(
        self, 
        new_start: datetime, 
        new_end: datetime,
        existing_start: datetime, 
        existing_end: datetime,
        buffer_minutes: int = 30
    ) -> bool:
        """Check if two time periods conflict with buffer time"""
        buffer = timedelta(minutes=buffer_minutes)
        
        # Extend existing period with buffer
        buffered_start = existing_start - buffer
        buffered_end = existing_end + buffer
        
        # Check for overlap
        return not (new_end <= buffered_start or new_start >= buffered_end)
    
    def find_available_time_slots(
        self,
        date: datetime,
        duration_hours: float,
        existing_bookings: List[Dict[str, datetime]],
        working_hours_start: Optional[int] = None,
        working_hours_end: Optional[int] = None
    ) -> List[Dict[str, datetime]]:
        """Find available time slots for a given duration"""
        start_hour = working_hours_start or self.working_hours_start
        end_hour = working_hours_end or self.working_hours_end
        
        # Create working day boundaries
        day_start = date.replace(hour=start_hour, minute=0, second=0, microsecond=0)
        day_end = date.replace(hour=end_hour, minute=0, second=0, microsecond=0)
        
        # Sort existing bookings by start time
        sorted_bookings = sorted(existing_bookings, key=lambda x: x['start_time'])
        
        available_slots = []
        duration_delta = timedelta(hours=duration_hours)
        buffer_delta = timedelta(minutes=self.min_break_minutes)
        
        # Check slot before first booking
        if sorted_bookings:
            first_booking_start = sorted_bookings[0]['start_time']
            if day_start + duration_delta + buffer_delta <= first_booking_start:
                available_slots.append({
                    'start_time': day_start,
                    'end_time': day_start + duration_delta
                })
        else:
            # No bookings, entire day available
            available_slots.append({
                'start_time': day_start,
                'end_time': day_start + duration_delta
            })
            return available_slots
        
        # Check slots between bookings
        for i in range(len(sorted_bookings) - 1):
            current_end = sorted_bookings[i]['end_time']
            next_start = sorted_bookings[i + 1]['start_time']
            
            slot_start = current_end + buffer_delta
            slot_end = slot_start + duration_delta
            
            if slot_end + buffer_delta <= next_start:
                available_slots.append({
                    'start_time': slot_start,
                    'end_time': slot_end
                })
        
        # Check slot after last booking
        if sorted_bookings:
            last_booking_end = sorted_bookings[-1]['end_time']
            slot_start = last_booking_end + buffer_delta
            slot_end = slot_start + duration_delta
            
            if slot_end <= day_end:
                available_slots.append({
                    'start_time': slot_start,
                    'end_time': slot_end
                })
        
        return available_slots
    
    def optimize_schedule_by_priority(
        self,
        trips: List[Dict],
        capacity_constraints: Dict[str, int]
    ) -> List[Dict]:
        """Optimize schedule considering trip priorities and resource constraints"""
        # Sort trips by priority (urgent first) and then by preferred time
        def priority_key(trip):
            priority_value = trip.get('priority', Priority.MEDIUM.value)
            preferred_time = trip.get('preferred_start_time', datetime.max)
            return (-priority_value, preferred_time)
        
        sorted_trips = sorted(trips, key=priority_key)
        scheduled_trips = []
        resource_usage = {resource: 0 for resource in capacity_constraints}
        
        for trip in sorted_trips:
            required_resources = trip.get('required_resources', {})
            
            # Check if resources are available
            can_schedule = True
            for resource, required in required_resources.items():
                if resource in capacity_constraints:
                    if resource_usage[resource] + required > capacity_constraints[resource]:
                        can_schedule = False
                        break
            
            if can_schedule:
                # Update resource usage
                for resource, required in required_resources.items():
                    if resource in resource_usage:
                        resource_usage[resource] += required
                
                scheduled_trips.append(trip)
        
        return scheduled_trips
    
    def calculate_schedule_efficiency(
        self,
        trips: List[Dict],
        total_available_time: float
    ) -> Dict[str, float]:
        """Calculate efficiency metrics for a schedule"""
        if not trips:
            return {
                "utilization_rate": 0.0,
                "average_gap": 0.0,
                "total_productive_time": 0.0
            }
        
        total_trip_time = sum(trip.get('duration_hours', 0) for trip in trips)
        
        # Calculate gaps between trips
        sorted_trips = sorted(trips, key=lambda x: x.get('start_time', datetime.min))
        total_gap_time = 0.0
        
        for i in range(len(sorted_trips) - 1):
            current_end = sorted_trips[i].get('end_time')
            next_start = sorted_trips[i + 1].get('start_time')
            
            if current_end and next_start:
                gap = (next_start - current_end).total_seconds() / 3600  # Convert to hours
                total_gap_time += max(0, gap)
        
        utilization_rate = total_trip_time / total_available_time if total_available_time > 0 else 0
        average_gap = total_gap_time / max(1, len(sorted_trips) - 1)
        
        return {
            "utilization_rate": utilization_rate,
            "average_gap": average_gap,
            "total_productive_time": total_trip_time,
            "total_gap_time": total_gap_time
        }
    
    def suggest_schedule_improvements(
        self,
        current_schedule: List[Dict],
        efficiency_threshold: float = 0.8
    ) -> List[str]:
        """Suggest improvements for schedule optimization"""
        suggestions = []
        
        if not current_schedule:
            return ["No trips scheduled"]
        
        # Calculate current efficiency
        total_time = 8.0  # Assume 8-hour working day
        efficiency = self.calculate_schedule_efficiency(current_schedule, total_time)
        
        if efficiency["utilization_rate"] < efficiency_threshold:
            suggestions.append(
                f"Low utilization rate ({efficiency['utilization_rate']:.1%}). "
                "Consider adding more trips or reducing schedule gaps."
            )
        
        if efficiency["average_gap"] > 2.0:  # More than 2 hours average gap
            suggestions.append(
                f"Large gaps between trips (avg: {efficiency['average_gap']:.1f} hours). "
                "Consider rescheduling to reduce idle time."
            )
        
        # Check for very early or very late trips
        for trip in current_schedule:
            start_time = trip.get('start_time')
            if start_time:
                if start_time.hour < 6:
                    suggestions.append("Some trips start very early. Consider driver fatigue.")
                elif start_time.hour > 20:
                    suggestions.append("Some trips end very late. Consider driver fatigue.")
        
        # Check for back-to-back trips without breaks
        sorted_trips = sorted(current_schedule, key=lambda x: x.get('start_time', datetime.min))
        for i in range(len(sorted_trips) - 1):
            current_end = sorted_trips[i].get('end_time')
            next_start = sorted_trips[i + 1].get('start_time')
            
            if current_end and next_start:
                gap_minutes = (next_start - current_end).total_seconds() / 60
                if gap_minutes < self.min_break_minutes:
                    suggestions.append(
                        f"Insufficient break time between trips "
                        f"({gap_minutes:.0f} minutes). Minimum {self.min_break_minutes} minutes recommended."
                    )
        
        if not suggestions:
            suggestions.append("Schedule looks well optimized!")
        
        return suggestions
    
    def redistribute_workload(
        self,
        overloaded_schedules: List[Dict],
        underutilized_schedules: List[Dict],
        max_transfer_hours: float = 2.0
    ) -> Dict[str, List[Dict]]:
        """Redistribute workload between overloaded and underutilized resources"""
        redistributed = {
            "transfers": [],
            "updated_schedules": []
        }
        
        for overloaded in overloaded_schedules:
            for underutilized in underutilized_schedules:
                overloaded_trips = overloaded.get('trips', [])
                underutilized_trips = underutilized.get('trips', [])
                
                # Find transferable trips (lower priority, short duration)
                transferable_trips = [
                    trip for trip in overloaded_trips
                    if (trip.get('priority', Priority.MEDIUM.value) <= Priority.MEDIUM.value and
                        trip.get('duration_hours', 0) <= max_transfer_hours)
                ]
                
                if transferable_trips:
                    # Transfer one trip
                    trip_to_transfer = transferable_trips[0]
                    
                    # Remove from overloaded
                    overloaded_trips.remove(trip_to_transfer)
                    
                    # Add to underutilized
                    underutilized_trips.append(trip_to_transfer)
                    
                    redistributed["transfers"].append({
                        "trip_id": trip_to_transfer.get('id'),
                        "from_resource": overloaded.get('resource_id'),
                        "to_resource": underutilized.get('resource_id')
                    })
        
        return redistributed
    
    async def auto_reschedule_delayed_trip(
        self,
        delayed_trip: Dict,
        delay_minutes: int,
        affected_trips: List[Dict]
    ) -> List[Dict]:
        """Automatically reschedule trips affected by delays"""
        delay_delta = timedelta(minutes=delay_minutes)
        rescheduled_trips = []
        
        # Update the delayed trip
        if 'start_time' in delayed_trip:
            delayed_trip['start_time'] += delay_delta
        if 'end_time' in delayed_trip:
            delayed_trip['end_time'] += delay_delta
        
        rescheduled_trips.append(delayed_trip)
        
        # Cascade the delay to subsequent trips
        for trip in affected_trips:
            if trip.get('start_time', datetime.min) >= delayed_trip.get('end_time', datetime.min):
                # This trip needs to be rescheduled
                if 'start_time' in trip:
                    trip['start_time'] += delay_delta
                if 'end_time' in trip:
                    trip['end_time'] += delay_delta
                
                rescheduled_trips.append(trip)
        
        return rescheduled_trips
