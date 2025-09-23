# Geoapify Routing API Integration

This document describes the integration of the Geoapify Routing API into the SAMFMS trip planning system.

## Overview

The routing integration automatically fetches detailed route information when trips are scheduled, including:

- **Route geometry**: Coordinates for drawing the route on a map
- **Turn-by-turn instructions**: Human-readable navigation directions  
- **Speed limits**: For each road segment (when available)
- **Road details**: Road class, surface type, lane count, etc.
- **Distance and time**: Total route distance and estimated travel time

## Components

### 1. Routing Service (`services/routing_service.py`)

The main service that interfaces with the Geoapify Routing API.

#### Key Methods:
- `calculate_route()`: Raw API calls to Geoapify
- `get_route_geometry()`: Get coordinates only
- `get_detailed_route_info()`: Get comprehensive route data as dictionary
- `get_detailed_route_info_object()`: Get comprehensive route data as DetailedRouteInfo object
- `format_waypoints_from_trip()`: Convert trip waypoints to routing format

#### Configuration:
- **API Key**: `8c5cae4820744254b3cb03ebd9b9ce13` (embedded)
- **Base URL**: `https://api.geoapify.com/v1/routing`
- **Default Mode**: `drive` (can be configured per request)

### 2. Enhanced Schemas (`schemas/entities.py`)

Extended the schema to support comprehensive routing data storage:

#### New Schema Classes:
- `TurnByTurnInstruction`: Navigation instructions with type, distance, time
- `RoadDetail`: Road segment details including speed limits, surface, tolls
- `DetailedRouteInfo`: Comprehensive route information from Geoapify API
- `RouteInfo`: Maintained as original basic route information

#### DetailedRouteInfo Schema:
```python
class DetailedRouteInfo(BaseModel):
    # Basic route information
    distance: float
    duration: float
    coordinates: List[List[float]]
    
    # Route characteristics
    toll: bool
    ferry: bool
    
    # Turn-by-turn navigation
    instructions: List[TurnByTurnInstruction]
    
    # Detailed road information
    road_details: List[RoadDetail]
    
    # API response metadata
    raw_response: Optional[Dict[str, Any]]
    
    # Timestamp when route was fetched
    fetched_at: datetime
```

#### Updated Trip Schema:
```python
class Trip(BaseModel):
    # ... other fields ...
    
    # Route information
    route_info: Optional[RouteInfo]  # Basic route info (preserved for compatibility)
    detailed_route_info: Optional[DetailedRouteInfo]  # Comprehensive Geoapify data
    
    # ... other fields ...
```

### 3. Trip Service Integration (`services/trip_service.py`)

Modified the trip creation flow to **always** fetch detailed route information.

#### Integration Points:
- **Trip Creation**: Always fetch `detailed_route_info` from Geoapify API regardless of whether `route_info` is provided
- **Route Fetching**: New `_fetch_detailed_route_info()` method
- **Session Management**: Proper cleanup of HTTP sessions
- **Database Storage**: Proper serialization of nested Pydantic objects to dictionaries

#### Workflow:
1. User creates trip with origin/destination (and optional waypoints)
2. System **always** calls Geoapify Routing API to fetch detailed route information
3. Store detailed route data in `detailed_route_info` field
4. If no basic `route_info` was provided, also create basic route info from detailed data
5. Extract distance/duration for trip planning estimates
6. Store all data properly serialized in database

## API Usage

### Supported Features

The integration uses these Geoapify API features:

- **Transportation Modes**: drive, truck, bicycle, walk, etc.
- **Route Details**: `instruction_details`, `route_details` 
- **Avoidance**: tolls, highways, ferries
- **Traffic Models**: free_flow, approximated

### Request Format

```
GET https://api.geoapify.com/v1/routing?
  waypoints=lat1,lon1|lat2,lon2&
  mode=drive&
  details=instruction_details,route_details&
  format=json&
  apiKey=8c5cae4820744254b3cb03ebd9b9ce13
```

### Response Data

The service extracts and stores:

- **Basic Info**: distance (meters), duration (seconds)
- **Geometry**: Array of [lat, lng] coordinates
- **Instructions**: Turn-by-turn navigation steps
- **Road Details**: Speed limits, road class, surface type
- **Route Flags**: toll roads, ferries, tunnels, bridges

## Integration Benefits

### For Trip Planning:
- **Automatic Route Calculation**: No manual route input required
- **Accurate Estimates**: Real-world distance and time estimates
- **Traffic Awareness**: Optional traffic model integration
- **Route Optimization**: Built-in route optimization

### For Navigation:
- **Turn-by-Turn Guidance**: Ready-to-use navigation instructions
- **Visual Routes**: Coordinates for map display
- **Road Information**: Speed limits and road characteristics
- **Route Alternatives**: Support for route avoidance preferences

### For Analytics:
- **Route History**: Complete route data stored with trips
- **Performance Metrics**: Actual vs estimated travel times
- **Route Analysis**: Road types, toll usage, etc.

## Error Handling

The integration includes robust error handling:

- **API Failures**: Graceful degradation if routing API is unavailable
- **Network Issues**: Timeout and retry logic
- **Invalid Waypoints**: Validation and error messages
- **Quota Limits**: Proper error reporting for API limits
- **Serialization Issues**: Proper conversion of Pydantic objects to dictionaries for database storage

### Common Issues Fixed:

**"'dict' object has no attribute 'distance'"**: 
- Fixed by ensuring proper serialization of DetailedRouteInfo objects before database storage
- All nested Pydantic objects are converted to dictionaries using `.dict()` method
- Handles both object and dictionary forms when reading route data

## Testing

Run the integration test:

```bash
cd /path/to/trip_planning
python test_routing_integration.py
```

The test verifies:
- Basic route geometry fetching
- Detailed route information
- Multi-waypoint routing
- Schema validation
- Waypoint formatting

## Configuration

### API Limits (Free Plan)
- **Daily Quota**: 3,000 credits/day
- **Cost per Route**: 1 credit for basic route between 2 waypoints
- **Additional Costs**: +1 credit for route_details, +1 for elevation

### Route Calculation Costs
- Basic route (2 waypoints): 1 credit
- With detailed info: 2 credits  
- Routes over 500km: +1 credit per 500km
- Multi-waypoint: 1 credit per waypoint pair

## Future Enhancements

Potential improvements:

1. **Route Alternatives**: Request multiple route options
2. **Real-time Traffic**: Integrate live traffic data
3. **Vehicle-specific Routing**: Use truck/bicycle modes based on vehicle type
4. **Route Caching**: Cache routes to reduce API calls
5. **Offline Fallback**: Use cached/simplified routes when API unavailable

## Monitoring

The integration logs:
- API request/response details
- Route calculation performance
- Error conditions and fallbacks
- Usage metrics for quota monitoring

Check logs for routing-related messages:
```
[RoutingService] Making request to: https://api.geoapify.com/...
[RoutingService] API response received successfully
[TripService] Successfully fetched route info: 45000m, 2700s
```