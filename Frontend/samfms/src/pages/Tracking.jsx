import React, {useState, useEffect} from 'react';
import TrackingMapWithSidebar from '../components/tracking/TrackingMapWithSidebar';
import {listGeofences} from '../backend/api/geofences';
import {listLocations} from '../backend/api/locations';
import FadeIn from '../components/ui/FadeIn';

const Tracking = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Load geofences on mount
  useEffect(() => {
    const loadGeofences = async () => {
      try {
        setLoading(true);
        const response = await listGeofences();
        const transformedGeofences = (response.data?.data || [])
          .filter(geofence => geofence && typeof geofence === 'object') // Filter out invalid geofences
          .map(geofence => {
            let coordinates = {lat: 0, lng: 0};
            let radius = 500;
            let geometryType = 'circle';

            if (geofence.geometry) {
              geometryType = geofence.geometry.type || 'circle';
              if (geometryType === 'circle') {
                coordinates = {
                  lat: geofence.geometry.center?.latitude || 0,
                  lng: geofence.geometry.center?.longitude || 0,
                };
                radius = geofence.geometry.radius || 500;
              } else if (geometryType === 'polygon' || geometryType === 'rectangle') {
                const firstPoint = geofence.geometry.points?.[0];
                if (firstPoint) {
                  coordinates = {lat: firstPoint.latitude || 0, lng: firstPoint.longitude || 0};
                }
                radius = null;
              }
            }

            return {
              id: geofence.id || `temp-${Date.now()}`,
              name: geofence.name || 'Unnamed Geofence',
              description: geofence.description || '',
              type: geofence.type || 'depot',
              status: geofence.status || 'active',
              geometry: geofence.geometry,
              geometryType: geometryType,
              coordinates: coordinates,
              radius: radius,
            };
          });

        setGeofences(transformedGeofences);
        setError(null);
      } catch (err) {
        console.error('Failed to load geofences:', err);
        setError('Failed to load geofences');
        setGeofences([]);
      } finally {
        setLoading(false);
      }
    };
    loadGeofences();
  }, []);

  // Poll locations every 5 seconds
  useEffect(() => {
    const loadLocations = async () => {
      try {
        const response = await listLocations();
        console.log('Response received from Core: ');
        console.log(response);
        setLocations(response.data?.data || []);
      } catch (err) {
        console.error('Failed to load locations:', err);
      }
    };
    loadLocations();
    const interval = setInterval(loadLocations, 5000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="flex justify-center items-center h-64">
          <div className="text-lg">Loading geofences...</div>
        </div>
      </div>
    );
  }

  return (
    <FadeIn delay={0.1}>
      <div className="w-full h-screen overflow-hidden">
        <div
          className="absolute inset-0 z-0 opacity-10 pointer-events-none"
          style={{
            backgroundImage: 'url("/logo/logo_icon_dark.svg")',
            backgroundSize: '200px',
            backgroundRepeat: 'repeat',
            filter: 'blur(1px)',
          }}
          aria-hidden="true"
        />

        <div className="relative z-10 w-full h-full">
          {error && (
            <FadeIn delay={0.3}>
              <div className="absolute top-4 left-4 right-4 z-50 p-4 bg-red-100 border border-red-400 text-red-700 rounded">
                {error}
              </div>
            </FadeIn>
          )}

          {/* Map with Sidebar */}
          <FadeIn delay={0.4}>
            <TrackingMapWithSidebar />
          </FadeIn>
        </div>
      </div>
    </FadeIn>
  );
};

export default Tracking;
