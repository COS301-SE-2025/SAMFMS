// Route calculation service using OSRM API
export const calculateRoute = async (startLocation, endLocation, waypoints = []) => {
  try {
    // Build the coordinate string for OSRM
    const coordinates = [
      `${startLocation.lng},${startLocation.lat}`,
      ...waypoints.map(wp => `${wp.lng},${wp.lat}`),
      `${endLocation.lng},${endLocation.lat}`,
    ].join(';');

    const url = `https://router.project-osrm.org/route/v1/driving/${coordinates}?overview=full&geometries=geojson`;

    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`OSRM API error: ${response.status}`);
    }

    const data = await response.json();

    if (data.routes && data.routes.length > 0) {
      const route = data.routes[0];

      // Calculate total distance and duration from all legs
      const totalDistance = route.legs.reduce((sum, leg) => sum + leg.distance, 0);
      const totalDuration = route.legs.reduce((sum, leg) => sum + leg.duration, 0);

      return {
        distance: totalDistance, // in meters
        duration: totalDuration, // in seconds
        geometry: route.geometry,
        coordinates: route.geometry.coordinates,
      };
    } else {
      throw new Error('No route found');
    }
  } catch (error) {
    console.error('Route calculation error:', error);
    throw error;
  }
};
