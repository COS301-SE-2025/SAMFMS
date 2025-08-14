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

// Custom routing function using OpenRouteService (free alternative)
const getRoute = async (startLocation, endLocation, waypoints = []) => {
  try {
    // For now, let's create a simple route approximation
    // You can replace this with any routing service you prefer
    const coords = [
      [startLocation.lng, startLocation.lat],
      ...waypoints.map(wp => [wp.lng, wp.lat]),
      [endLocation.lng, endLocation.lat],
    ];

    // Calculate approximate distance
    let totalDistance = 0;
    for (let i = 0; i < coords.length - 1; i++) {
      const from = L.latLng(coords[i][1], coords[i][0]);
      const to = L.latLng(coords[i + 1][1], coords[i + 1][0]);
      totalDistance += from.distanceTo(to);
    }

    // Create a simple curved path between points
    const routeCoords = [];
    for (let i = 0; i < coords.length - 1; i++) {
      const start = coords[i];
      const end = coords[i + 1];

      // Add intermediate points for a curved path
      const steps = 10;
      for (let j = 0; j <= steps; j++) {
        const ratio = j / steps;
        const lat = start[1] + (end[1] - start[1]) * ratio;
        const lng = start[0] + (end[0] - start[0]) * ratio;

        // Add slight curve for more realistic appearance
        const curveFactor = Math.sin(ratio * Math.PI) * 0.001;
        routeCoords.push([lat + curveFactor, lng + curveFactor]);
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

    // Create waypoints array for routing
    const routeWaypoints = [
      L.latLng(startLocation.lat, startLocation.lng),
      ...waypoints.map(wp => L.latLng(wp.lat, wp.lng)),
      L.latLng(endLocation.lat, endLocation.lng),
    ];

    console.log('Route waypoints:', routeWaypoints);

    // Try to create actual routing control first
    try {
      console.log('Creating Leaflet Routing Machine control...');
      console.log('L.Routing available:', !!L.Routing);

      if (!L.Routing) {
        throw new Error('L.Routing is not available - leaflet-routing-machine not loaded');
      }

      const routingControl = L.Routing.control({
        waypoints: routeWaypoints,
        // Use Leaflet Routing Machine's default router (which handles routing internally)
        routeWhileDragging: false,
        addWaypoints: false,
        draggableWaypoints: false,
        createMarker: () => null, // Don't create default markers
        show: false, // Hide the routing instructions panel
        lineOptions: {
          styles: [
            {
              color: '#ffffff', // White outline
              weight: 8,
              opacity: 0.8,
            },
            {
              color: '#1e40af', // Blue route line
              weight: 5,
              opacity: 1.0,
              lineCap: 'round',
              lineJoin: 'round',
            },
          ],
        },
      });

      routingControl.on('routesfound', e => {
        console.log('Leaflet Routing Machine route found:', e.routes[0]);
        const route = e.routes[0];

        // Cancel the timeout since we got a successful route
        if (timeoutRef.current) {
          clearTimeout(timeoutRef.current);
          timeoutRef.current = null;
        }

        // Clear loading state
        if (setIsCalculating) {
          setIsCalculating(false);
        }

        // Fit map bounds to show the entire route
        if (route.bounds) {
          map.fitBounds(
            [
              [route.bounds.getSouth(), route.bounds.getWest()],
              [route.bounds.getNorth(), route.bounds.getEast()],
            ],
            { padding: [20, 20] }
          );
        }

        if (onRouteCalculated) {
          onRouteCalculated({
            distance: route.summary.totalDistance,
            duration: route.summary.totalTime,
            coordinates: route.coordinates,
            bounds: route.bounds,
            isRealRoute: true,
          });
        }
      });

      routingControl.on('routingerror', error => {
        console.error('Leaflet Routing Machine error:', error);

        // Cancel the timeout
        if (timeoutRef.current) {
          clearTimeout(timeoutRef.current);
          timeoutRef.current = null;
        }

        // Remove the failed routing control
        try {
          if (routingControlRef.current) {
            map.removeControl(routingControlRef.current);
            routingControlRef.current = null;
          }
        } catch (e) {
          console.warn('Error removing failed routing control:', e);
        }

        // Show fallback route
        showFallbackRoute();
      });

      console.log('Adding routing control to map...');
      routingControl.addTo(map);
      routingControlRef.current = routingControl;

      // Set a timeout to show fallback if routing takes too long
      timeoutRef.current = setTimeout(() => {
        console.log('Leaflet Routing Machine taking too long, showing fallback route...');
        if (routingControlRef.current) {
          try {
            map.removeControl(routingControlRef.current);
            routingControlRef.current = null;
          } catch (e) {
            console.warn('Error removing slow routing control:', e);
          }
        }
        showFallbackRoute();
      }, 8000); // 8 second timeout for user experience
    } catch (error) {
      console.error('Failed to create routing control:', error);
      // Show fallback route if routing control creation fails
      showFallbackRoute();
    }

    // Fallback route function
    function showFallbackRoute() {
      console.log('Showing fallback straight line route...');
      const straightLineCoords = [
        [startLocation.lat, startLocation.lng],
        [endLocation.lat, endLocation.lng],
      ];

      const fallbackPolyline = L.polyline(straightLineCoords, {
        color: '#6b7280', // Gray color to distinguish from real routes
        weight: 4,
        opacity: 0.7,
        dashArray: '10, 10',
      });

      fallbackPolyline.addTo(map);
      fallbackPolylineRef.current = fallbackPolyline;

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
          isRealRoute: false,
        });
      }

      // Clear loading state
      if (setIsCalculating) {
        setIsCalculating(false);
      }
    }

    // Cleanup function
    return cleanupRoutes;
  }, [map, startLocation, endLocation, waypoints, onRouteCalculated, setIsCalculating]);

  return null;
};

export default RoutingMachine;
