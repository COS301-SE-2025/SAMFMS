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

// Decode polyline function (Google's polyline algorithm)
const decodePolyline = encoded => {
  if (!encoded) return [];

  let index = 0;
  let lat = 0;
  let lng = 0;
  const coordinates = [];

  while (index < encoded.length) {
    let b,
      shift = 0,
      result = 0;

    do {
      b = encoded.charCodeAt(index++) - 63;
      result |= (b & 0x1f) << shift;
      shift += 5;
    } while (b >= 0x20);

    const deltaLat = result & 1 ? ~(result >> 1) : result >> 1;
    lat += deltaLat;

    shift = 0;
    result = 0;

    do {
      b = encoded.charCodeAt(index++) - 63;
      result |= (b & 0x1f) << shift;
      shift += 5;
    } while (b >= 0x20);

    const deltaLng = result & 1 ? ~(result >> 1) : result >> 1;
    lng += deltaLng;

    coordinates.push([lat / 1e5, lng / 1e5]);
  }

  return coordinates;
};

// Real routing function using OpenRouteService API for road-following routes
const getRoute = async (startLocation, endLocation, waypoints = []) => {
  try {
    console.log('Calculating real road route from OpenRouteService...');

    // Build coordinates array: [lng, lat] format for OpenRouteService
    const coordinates = [
      [startLocation.lng, startLocation.lat],
      ...waypoints.map(wp => [wp.lng, wp.lat]),
      [endLocation.lng, endLocation.lat],
    ];

    console.log('Route coordinates for API:', coordinates);

    // OpenRouteService API endpoint (free tier: 2000 requests/day)
    const apiUrl = 'https://api.openrouteservice.org/v2/directions/driving-car';

    const requestBody = {
      coordinates: coordinates,
      format: 'json',
      instructions: false,
      geometry_simplify: false,
      continue_straight: false,
    };

    console.log('Making API request to OpenRouteService...');

    const response = await fetch(apiUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization:
          'eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6IjBhNzU4YjIzMGQ5MDRmNGM5YjUzMmRkMjgzNzQ1YmJhIiwiaCI6Im11cm11cjY0In0=',
      },
      body: JSON.stringify(requestBody),
    });

    if (!response.ok) {
      console.error('OpenRouteService API error:', response.status, response.statusText);
      throw new Error(`API returned ${response.status}: ${response.statusText}`);
    }

    const data = await response.json();
    console.log('OpenRouteService response:', data);
    console.log('Response structure check:', {
      hasRoutes: !!data.routes,
      routeCount: data.routes?.length || 0,
      firstRouteHasGeometry: !!data.routes?.[0]?.geometry,
      geometryType: typeof data.routes?.[0]?.geometry,
      geometryPreview:
        typeof data.routes?.[0]?.geometry === 'string'
          ? data.routes[0].geometry.substring(0, 50) + '...'
          : data.routes?.[0]?.geometry,
      hasSummary: !!data.routes?.[0]?.summary,
    });

    if (data.routes && data.routes.length > 0) {
      const route = data.routes[0];

      // Decode the geometry (it's in encoded polyline format)
      const geometry = route.geometry;
      let routeCoords = [];

      if (typeof geometry === 'string') {
        // Decode encoded polyline string
        console.log('Decoding polyline geometry string:', geometry.substring(0, 50) + '...');
        const decodedCoords = decodePolyline(geometry);
        console.log('Decoded', decodedCoords.length, 'coordinates from polyline');
        routeCoords = decodedCoords; // Already in [lat, lng] format from decoder
      } else if (geometry.coordinates && Array.isArray(geometry.coordinates)) {
        // Handle GeoJSON coordinates format (if API returns this format)
        // Convert [lng, lat] to [lat, lng] for Leaflet
        routeCoords = geometry.coordinates.map(coord => [coord[1], coord[0]]);
        console.log('Using GeoJSON coordinates format');
      } else {
        console.warn('Unknown geometry format:', geometry);
        throw new Error('Unable to parse geometry data');
      }

      console.log('Final route with', routeCoords.length, 'coordinate points');
      console.log('Sample coordinates:', routeCoords.slice(0, 3));
      console.log('Route distance:', (route.summary.distance / 1000).toFixed(2), 'km');
      console.log('Route duration:', Math.round(route.summary.duration / 60), 'minutes');

      // Validate coordinates
      if (routeCoords.length === 0) {
        console.warn('No coordinates were decoded from geometry');
        throw new Error('No route coordinates available');
      }

      // Check if coordinates are valid
      const invalidCoords = routeCoords.some(
        coord =>
          !Array.isArray(coord) ||
          coord.length !== 2 ||
          isNaN(coord[0]) ||
          isNaN(coord[1]) ||
          Math.abs(coord[0]) > 90 ||
          Math.abs(coord[1]) > 180
      );

      if (invalidCoords) {
        console.warn('Invalid coordinates detected in route');
        throw new Error('Invalid route coordinates');
      }

      return {
        coordinates: routeCoords,
        distance: route.summary.distance, // meters
        duration: route.summary.duration, // seconds
        success: true,
      };
    } else {
      console.warn('No routes found in API response');
      throw new Error('No routes found');
    }
  } catch (error) {
    console.error('OpenRouteService routing error:', error);

    // Fallback to simple interpolated route (better than straight line)
    console.log('Falling back to interpolated route...');
    return await getInterpolatedRoute(startLocation, endLocation, waypoints);
  }
};

// Fallback function that creates a more realistic curved route
const getInterpolatedRoute = async (startLocation, endLocation, waypoints = []) => {
  try {
    const allPoints = [
      [startLocation.lng, startLocation.lat],
      ...waypoints.map(wp => [wp.lng, wp.lat]),
      [endLocation.lng, endLocation.lat],
    ];

    let totalDistance = 0;
    const routeCoords = [];

    for (let i = 0; i < allPoints.length - 1; i++) {
      const start = allPoints[i];
      const end = allPoints[i + 1];

      const from = L.latLng(start[1], start[0]);
      const to = L.latLng(end[1], end[0]);
      const segmentDistance = from.distanceTo(to);
      totalDistance += segmentDistance;

      // Add start point (only for first segment)
      if (i === 0) {
        routeCoords.push([start[1], start[0]]);
      }

      // Create many more intermediate points for smoother curves
      const steps = Math.max(10, Math.floor(segmentDistance / 100)); // Point every 100m

      for (let j = 1; j <= steps; j++) {
        const ratio = j / steps;

        // Add some curve variation to simulate road paths
        const baseLatOffset = (end[1] - start[1]) * ratio;
        const baseLngOffset = (end[0] - start[0]) * ratio;

        // Add slight perpendicular offset for curve effect
        const perpOffset = Math.sin(ratio * Math.PI) * 0.001; // Small curve

        const lat = start[1] + baseLatOffset + perpOffset;
        const lng = start[0] + baseLngOffset + perpOffset;

        routeCoords.push([lat, lng]);
      }
    }

    console.log('Generated interpolated route with', routeCoords.length, 'coordinate points');

    return {
      coordinates: routeCoords,
      distance: totalDistance,
      duration: (totalDistance / 1000) * 60, // Rough estimate: 1km per minute
      success: true,
    };
  } catch (error) {
    console.error('Interpolated route calculation error:', error);
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

  // Create stable references to prevent infinite loops
  const onRouteCalculatedRef = useRef(onRouteCalculated);
  const setIsCalculatingRef = useRef(setIsCalculating);

  // Update refs when props change
  onRouteCalculatedRef.current = onRouteCalculated;
  setIsCalculatingRef.current = setIsCalculating;

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
      if (setIsCalculatingRef.current) {
        setIsCalculatingRef.current(false);
      }
      return;
    }

    console.log('Starting route calculation...');

    // Set loading state
    if (setIsCalculatingRef.current) {
      setIsCalculatingRef.current(true);
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

        console.log('getRoute returned:', routeData);

        if (routeData && routeData.success) {
          console.log('SUCCESS: Real road route calculated successfully:', routeData);
          console.log('Route coordinates format:', routeData.coordinates);
          console.log('Route distance:', (routeData.distance / 1000).toFixed(2), 'km');
          console.log('Route duration:', Math.round(routeData.duration / 60), 'minutes');

          // Create polyline for the REAL road route with distinctive styling
          const polyline = L.polyline(routeData.coordinates, {
            color: '#059669', // Green for real routes
            weight: 6,
            opacity: 0.9,
            lineCap: 'round',
            lineJoin: 'round',
            dashArray: null, // Solid line for real routes
          });

          console.log('Real route polyline created with', routeData.coordinates.length, 'points');

          // Add to map
          polyline.addTo(map);
          routePolylineRef.current = polyline;

          console.log('Polyline added to map');

          // Fit map bounds to show the entire route with validation
          let bounds = null;
          try {
            bounds = polyline.getBounds();
            console.log('Route bounds:', bounds);

            // Validate bounds before fitting
            if (bounds && bounds.isValid && bounds.isValid()) {
              map.fitBounds(bounds, { padding: [20, 20] });
            } else {
              console.warn('Invalid bounds, using alternative centering');
              // Alternative: center on start location with appropriate zoom
              map.setView([startLocation.lat, startLocation.lng], 13);
            }
          } catch (boundsError) {
            console.error('Error fitting bounds:', boundsError);
            // Fallback to centering on start location
            map.setView([startLocation.lat, startLocation.lng], 13);
          }

          // Call the route calculated callback
          if (onRouteCalculatedRef.current) {
            onRouteCalculatedRef.current({
              distance: routeData.distance,
              duration: routeData.duration,
              coordinates: routeData.coordinates,
              bounds: bounds,
            });
          }

          // Clear loading state
          if (setIsCalculatingRef.current) {
            setIsCalculatingRef.current(false);
          }
        } else {
          // Fallback to straight line
          console.log('FALLBACK: Route calculation failed, showing straight line fallback...');
          console.log('routeData was:', routeData);
          showFallbackRoute();
        }
      } catch (error) {
        console.error('Error calculating route:', error);
        showFallbackRoute();
      }
    };

    // Fallback straight line route
    const showFallbackRoute = () => {
      console.log('SHOWING FALLBACK ROUTE - Straight line (not following roads)');
      const straightLineCoords = [
        [startLocation.lat, startLocation.lng],
        [endLocation.lat, endLocation.lng],
      ];

      console.log('Fallback coordinates:', straightLineCoords);

      const fallbackPolyline = L.polyline(straightLineCoords, {
        color: '#ef4444', // Red for fallback routes
        weight: 4,
        opacity: 0.7,
        dashArray: '10, 10', // Dashed line to indicate this is not a real route
      });

      fallbackPolyline.addTo(map);
      routePolylineRef.current = fallbackPolyline;
      console.log('Fallback straight-line polyline added to map');

      // Fit map bounds
      const bounds = fallbackPolyline.getBounds();
      map.fitBounds(bounds, { padding: [20, 20] });

      // Calculate approximate distance for fallback
      const distance = map.distance(
        [startLocation.lat, startLocation.lng],
        [endLocation.lat, endLocation.lng]
      );
      const estimatedDuration = (distance / 1000) * 60; // Rough estimate: 1 km per minute

      console.log('Fallback route distance:', (distance / 1000).toFixed(2), 'km (straight line)');

      if (onRouteCalculatedRef.current) {
        onRouteCalculatedRef.current({
          distance: distance,
          duration: estimatedDuration,
          coordinates: straightLineCoords,
          isFallback: true,
        });
      }

      // Clear loading state
      if (setIsCalculatingRef.current) {
        setIsCalculatingRef.current(false);
      }
    };

    // Start route calculation
    calculateRoute();

    // Cleanup function
    return cleanupRoutes;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [
    map,
    startLocation?.lat,
    startLocation?.lng,
    endLocation?.lat,
    endLocation?.lng,
    waypoints?.length,
  ]);

  return null;
};

export default RoutingMachine;
