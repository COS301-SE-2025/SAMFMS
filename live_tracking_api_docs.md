# Live Trip Tracking API Documentation

## Endpoint
```
GET /trips/live/{trip_id}
```

## Request Format

### Via Core Service (Recommended)
Send request to Core service which will route to trip planning service:

```http
GET http://localhost:21004/trips/live/{trip_id}
Content-Type: application/json
Authorization: Bearer {your_token}
```

### Direct to Trip Planning Service
```http
GET http://localhost:21006/trips/live/{trip_id}
Content-Type: application/json
```

### Via RabbitMQ (Internal)
```json
{
  "method": "GET",
  "endpoint": "trips/live/{trip_id}",
  "user_context": {
    "user_id": "user123",
    "data": {}
  }
}
```

## Example Requests

### 1. Get Live Tracking for Trip
```bash
curl -X GET "http://localhost:21004/trips/live/60f7b1c4e4b0c8a5d4e2f1a3" \
  -H "Authorization: Bearer your_token_here" \
  -H "Content-Type: application/json"
```

### 2. JavaScript/Frontend Request
```javascript
const response = await fetch(`http://localhost:21004/trips/live/${tripId}`, {
  method: 'GET',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  }
});

const liveData = await response.json();
```

## Response Format

### Success Response
```json
{
  "success": true,
  "message": "Successfully retrieved live tracking data",
  "data": {
    "trip_id": "60f7b1c4e4b0c8a5d4e2f1a3",
    "vehicle_id": "60f7b1c4e4b0c8a5d4e2f1a4",
    "driver_id": "EMP001",
    "current_location": {
      "latitude": -33.9249,
      "longitude": 18.4241,
      "timestamp": "2025-09-16T10:30:00Z"
    },
    "direction": 45.5,
    "speed": 35.2,
    "route_polyline": [
      [-33.9249, 18.4241],
      [-33.9250, 18.4242],
      [-33.9251, 18.4243]
    ],
    "progress": {
      "distance_completed": 12500,
      "total_distance": 25000,
      "percentage": 50.0,
      "eta": "2025-09-16T11:15:00Z"
    },
    "next_instruction": {
      "text": "Turn right onto Main Street",
      "distance_to_instruction": 250,
      "type": "TurnRight"
    },
    "trip_status": "in_progress",
    "simulation_active": true
  }
}
```

### Error Response
```json
{
  "success": false,
  "error": "Trip not found",
  "message": "Trip with ID 60f7b1c4e4b0c8a5d4e2f1a3 not found",
  "data": null
}
```

## URL Parameters
- `{trip_id}`: The unique identifier of the trip to track (required)

## Use Cases

### 1. Real-time Map Display
Use the response data to display live vehicle position on Leaflet map:

```javascript
// Update vehicle marker position
vehicleMarker.setLatLng([data.current_location.latitude, data.current_location.longitude]);

// Update polyline
routePolyline.setLatLngs(data.route_polyline);

// Show next instruction
instructionPopup.setContent(data.next_instruction.text);
```

### 2. Progress Tracking
```javascript
// Update progress bar
progressBar.style.width = `${data.progress.percentage}%`;

// Show ETA
etaElement.textContent = `ETA: ${new Date(data.progress.eta).toLocaleTimeString()}`;
```

### 3. Vehicle Dashboard
```javascript
// Update speed display
speedDisplay.textContent = `${data.speed} km/h`;

// Update direction indicator
directionArrow.style.transform = `rotate(${data.direction}deg)`;
```

## Polling Recommendations

For real-time updates, poll this endpoint every 5-10 seconds:

```javascript
setInterval(async () => {
  try {
    const response = await fetch(`/trips/live/${tripId}`);
    const data = await response.json();
    updateMapDisplay(data);
  } catch (error) {
    console.error('Failed to fetch live data:', error);
  }
}, 5000); // Poll every 5 seconds
```

## Notes
- The simulation keeps running in the background automatically
- Vehicle position updates every few seconds based on simulation speed
- The polyline includes the complete route from current position to destination
- ETA is calculated based on current progress and remaining distance
- Direction is in degrees (0 = North, 90 = East, 180 = South, 270 = West)