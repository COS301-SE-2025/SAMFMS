import React, { useState, useEffect } from 'react';
import VehicleList from '../components/trips/VehicleList';
import TrackingMap from '../components/tracking/TrackingMap';
import GeofenceManager from '../components/tracking/GeofenceManager';
import LocationHistory from '../components/tracking/LocationHistory';
import { listGeofences } from '../backend/api/geofences';
import { listLocations } from '../backend/api/locations';
import { getVehicles } from '../backend/api/vehicles';
import FadeIn from '../components/ui/FadeIn';

const Tracking = () => {
  const [locations, setLocations] = useState([]);
  const [vehicles, setVehicles] = useState([]);
  const [selectedVehicle, setSelectedVehicle] = useState(null);
  const [geofences, setGeofences] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Load vehicle data
  useEffect(() => {
    const loadVehicles = async () => {
      try {
        const response = await getVehicles();
        setVehicles(response.vehicles || []);
      } catch (err) {
        console.error('Failed to load vehicles:', err);
      }
    };
    loadVehicles();
  }, []);

  // Load geofences on mount
  useEffect(() => {
    const loadGeofences = async () => {
      try {
        setLoading(true);
        const response = await listGeofences();
        const transformedGeofences =
          response.data?.data?.map(geofence => {
            let coordinates = { lat: 0, lng: 0 };
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
                  coordinates = { lat: firstPoint.latitude || 0, lng: firstPoint.longitude || 0 };
                }
                radius = null;
              }
            }

            return {
              id: geofence.id,
              name: geofence.name,
              description: geofence.description,
              type: geofence.type,
              status: geofence.status,
              geometry: geofence.geometry,
              geometryType: geometryType,
              coordinates: coordinates,
              radius: radius,
            };
          }) || [];

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

  const handleSelectVehicle = vehicle => {
    setSelectedVehicle(vehicle);
  };

  const handleGeofenceChange = updatedGeofences => {
    setGeofences(updatedGeofences);
  };

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
      <div className="relative container mx-auto px-4 py-8">
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

        <div className="relative z-10">
          <FadeIn delay={0.2}>
            <h1 className="text-3xl font-bold mb-6">Vehicle Tracking</h1>
          </FadeIn>

          {error && (
            <FadeIn delay={0.3}>
              <div className="mb-4 p-4 bg-red-100 border border-red-400 text-red-700 rounded">
                {error}
              </div>
            </FadeIn>
          )}

          {/* Map & list */}
          <FadeIn delay={0.4}>
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
              <div className="lg:col-span-2">
                <TrackingMap
                  locations={locations}
                  selectedVehicle={selectedVehicle}
                  geofences={geofences}
                />
              </div>
              <div className="lg:col-span-1">
                <VehicleList vehicles={vehicles} onSelectVehicle={handleSelectVehicle} />
              </div>
            </div>
          </FadeIn>

          {/* Geofences */}
          <FadeIn delay={0.5}>
            <div className="mt-8">
              <GeofenceManager
                onGeofenceChange={handleGeofenceChange}
                currentGeofences={geofences}
              />
            </div>
          </FadeIn>

          {/* History */}
          <FadeIn delay={0.6}>
            <div className="mt-8 mb-8">
              <LocationHistory vehicles={locations} />
            </div>
          </FadeIn>
        </div>
      </div>
    </FadeIn>
  );
};

export default Tracking;
