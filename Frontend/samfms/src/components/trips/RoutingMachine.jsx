import { useEffect, useRef } from 'react';
import L from 'leaflet';
import { useMap } from 'react-leaflet';

// Fix for marker icons in React-Leaflet
L.Marker.prototype.options.icon = L.icon({
  iconUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41],
});

// Custom routing function that creates a curved route
const getRoute = async (startLocation, endLocation, waypoints = []) => {
  try {
    // Create a curved path between points for a more realistic route appearance
    const allPoints = [
      [startLocation.lng, startLocation.lat],
      ...waypoints.map(wp => [wp.lng, wp.lat]),
      [endLocation.lng, endLocation.lat],
    ];

    // Calculate total distance
    let totalDistance = 0;
    const routeCoords = [];

    for (let i = 0; i < allPoints.length - 1; i++) {
      const start = allPoints[i];
      const end = allPoints[i + 1];

      const from = L.latLng(start[1], start[0]);
      const to = L.latLng(end[1], end[0]);
      totalDistance += from.distanceTo(to);

      // Create curved path between points
      const steps = Math.max(10, Math.floor(from.distanceTo(to) / 1000)); // More steps for longer distances

      for (let j = 0; j <= steps; j++) {
        const ratio = j / steps;

        // Linear interpolation
        const lat = start[1] + (end[1] - start[1]) * ratio;
        const lng = start[0] + (end[0] - start[0]) * ratio;

        // Add slight curve for more realistic appearance
        const curveFactor = Math.sin(ratio * Math.PI) * 0.002; // Adjust curve intensity

        routeCoords.push([lat + curveFactor, lng + curveFactor * 0.5]);
      }
    }

    return {
      coordinates: routeCoords,
      distance: totalDistance,
      duration: (totalDistance / 1000) * 60, // Rough estimate: 1km per minute
      success: true,
    };
  } catch (error) {
    console.error('Route calculation error:', error);
    return null;
  }
};

const RoutingMachine = ({
  startLocation,
  endLocation,
  waypoints = [],
  onRouteCalculated,
  isCalculating,
  setIsCalculating,
}) => {
  const map = useMap();
  const routePolylineRef = useRef(null);
  const currentRouteRef = useRef(null);

  useEffect(() => {
    console.log('RoutingMachine useEffect triggered', {
      hasMap: !!map,
      startLocation,
      endLocation,
      waypoints,
    });

    // Create a stable key for the current route to prevent unnecessary re-renders
    const routeKey = `${startLocation?.lat}-${startLocation?.lng}-${endLocation?.lat}-${
      endLocation?.lng
    }-${waypoints?.length || 0}`;

    // If this is the same route we're already showing, don't recreate
    if (currentRouteRef.current === routeKey) {
      console.log('Route unchanged, skipping recreation');
      return;
    }

    // Function to clean up any existing route display
    const cleanupRoutes = () => {
      try {
        if (routePolylineRef.current && map) {
          map.removeLayer(routePolylineRef.current);
          routePolylineRef.current = null;
        }
        // Clear the current route reference
        currentRouteRef.current = null;
      } catch (error) {
        console.warn('Error during route cleanup:', error);
      }
    };

    if (!map || !startLocation || !endLocation) {
      console.log('Missing required data for routing:', {
        hasMap: !!map,
        hasStart: !!startLocation,
        hasEnd: !!endLocation,
      });
      cleanupRoutes();
      return;
    }

    // Validate coordinates
    if (
      isNaN(startLocation.lat) ||
      isNaN(startLocation.lng) ||
      isNaN(endLocation.lat) ||
      isNaN(endLocation.lng)
    ) {
      console.error('Invalid coordinates:', { startLocation, endLocation });
      if (setIsCalculating) {
        setIsCalculating(false);
      }
      return;
    }

    console.log('Starting route calculation...');

    // Set loading state
    if (setIsCalculating) {
      setIsCalculating(true);
    }

    // Clean up any existing routes
    cleanupRoutes();

    // Set the current route key to prevent unnecessary re-renders
    currentRouteRef.current = routeKey;

    // Calculate and display route
    const calculateRoute = async () => {
      try {
        console.log('Calculating route using custom routing...');

        const routeData = await getRoute(startLocation, endLocation, waypoints);

        if (routeData && routeData.success) {
          console.log('Route calculated successfully:', routeData);

          // Create polyline for the route with better styling
          const polyline = L.polyline(routeData.coordinates, {
            color: '#1e40af',
            weight: 5,
            opacity: 0.8,
            lineCap: 'round',
            lineJoin: 'round',
          });

          // Add to map
          polyline.addTo(map);
          routePolylineRef.current = polyline;

          // Fit map bounds to show the entire route
          const bounds = polyline.getBounds();
          map.fitBounds(bounds, { padding: [20, 20] });

          // Call the route calculated callback
          if (onRouteCalculated) {
            onRouteCalculated({
              distance: routeData.distance,
              duration: routeData.duration,
              coordinates: routeData.coordinates,
              bounds: bounds,
            });
          }

          // Clear loading state
          if (setIsCalculating) {
            setIsCalculating(false);
          }
        } else {
          // Fallback to straight line
          console.log('Route calculation failed, showing straight line fallback...');
          showFallbackRoute();
        }
      } catch (error) {
        console.error('Error calculating route:', error);
        showFallbackRoute();
      }
    };

    // Fallback straight line route
    const showFallbackRoute = () => {
      const straightLineCoords = [
        [startLocation.lat, startLocation.lng],
        [endLocation.lat, endLocation.lng],
      ];

      const fallbackPolyline = L.polyline(straightLineCoords, {
        color: '#6b7280',
        weight: 3,
        opacity: 0.7,
        dashArray: '10, 10',
      });

      fallbackPolyline.addTo(map);
      routePolylineRef.current = fallbackPolyline;

      // Fit map bounds
      const bounds = fallbackPolyline.getBounds();
      map.fitBounds(bounds, { padding: [20, 20] });

      // Calculate approximate distance for fallback
      const distance = map.distance(
        [startLocation.lat, startLocation.lng],
        [endLocation.lat, endLocation.lng]
      );
      const estimatedDuration = (distance / 1000) * 60; // Rough estimate: 1 km per minute

      if (onRouteCalculated) {
        onRouteCalculated({
          distance: distance,
          duration: estimatedDuration,
          coordinates: straightLineCoords,
          isFallback: true,
        });
      }

      // Clear loading state
      if (setIsCalculating) {
        setIsCalculating(false);
      }
    };

    // Start route calculation
    calculateRoute();

    // Cleanup function
    return cleanupRoutes;
  }, [map, startLocation, endLocation, waypoints, onRouteCalculated, setIsCalculating]);

  return null;
};

export default RoutingMachine;
