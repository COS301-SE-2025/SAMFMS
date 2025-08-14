import React, { useState, useEffect } from 'react';
import ActiveTripsPanel from '../components/trips/ActiveTripsPanel';
import SchedulingPanel from '../components/trips/SchedulingPanel';
import TripsAnalytics from '../components/trips/TripsAnalytics';
import TripsHistory from '../components/trips/TripsHistory';
import TripSchedulingModal from '../components/trips/TripSchedulingModal';
import VehicleStatistics from '../components/trips/VehicleStatistics';
import VehicleList from '../components/trips/VehicleList';
import Pagination from '../components/vehicles/Pagination';
import {
  createTrip,
  getActiveTrips,
  getDriverAnalytics,
  getVehicleAnalytics,
} from '../backend/api/trips';

import { getVehicles } from '../backend/api/vehicles';
import { getAllDrivers } from '../backend/api/drivers';

const Trips = () => {
  // Existing state
  const [vehicles, setVehicles] = useState([]);

  // New state for features
  const [activeTrips, setActiveTrips] = useState([]);
  const [drivers, setDrivers] = useState([]);
  const [analyticsTimeframe, setAnalyticsTimeframe] = useState('week');
  const [driverAnalytics, setDriverAnalytics] = useState({
    drivers: [],
    timeframeSummary: {
      totalTrips: 0,
      completionRate: 0,
      averageTripsPerDay: 0,
    },
  });
  const [vehicleAnalytics, setVehicleAnalytics] = useState({
    vehicles: [],
    timeframeSummary: {
      totalDistance: 0,
    },
  });
  const [showScheduleModal, setShowScheduleModal] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Pagination state for vehicle overview table
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(5);

  // Get current date and time for default values
  const getCurrentDate = () => {
    const now = new Date();
    return now.toISOString().split('T')[0]; // Format: YYYY-MM-DD
  };

  const getCurrentTime = () => {
    const now = new Date();
    return now.toTimeString().slice(0, 5); // Format: HH:MM
  };

  // Updated trip form state to match new API format
  const [tripForm, setTripForm] = useState({
    name: '',
    description: '',
    vehicleId: '',
    driverId: '',
    startLocation: '',
    endLocation: '',
    scheduledStartDate: getCurrentDate(),
    scheduledStartTime: getCurrentTime(),
    scheduledEndDate: '',
    scheduledEndTime: '',
    priority: 'normal',
    temperatureControl: false,
    driverNote: '',
    timeWindowStart: '',
    timeWindowEnd: '',
  });

  // Store coordinates for selected locations
  const [locationCoords, setLocationCoords] = useState({
    start: null,
    end: null,
  });

  useEffect(() => {
    const loadVehicles = async () => {
      try {
        setLoading(true);
        setError(null);

        const response = await getVehicles();

        // Extract vehicles from the nested response structure with improved path handling
        let vehicleData =
          response?.data?.data?.data?.vehicles ||
          response?.data?.data?.vehicles ||
          response?.data?.vehicles ||
          response?.vehicles;

        // Additional fallbacks for different API response structures
        if (!vehicleData && response?.data?.data) {
          // Sometimes the API returns an array directly in data.data
          vehicleData = Array.isArray(response.data.data) ? response.data.data : [];
        } else if (!vehicleData) {
          vehicleData = [];
        }

        console.log('Loaded vehicles response:', response);
        console.log('Extracted vehicle data:', vehicleData);
        setVehicles(vehicleData);
      } catch (error) {
        console.error('Error loading vehicles:', error);
        setError('Failed to load vehicles');
        setVehicles([]);
      } finally {
        setLoading(false);
      }
    };

    loadVehicles();
  }, []);

  useEffect(() => {
    const loadActiveTrips = async () => {
      try {
        const response = await getActiveTrips();
        setActiveTrips(response.trips); // Update to use the new structure
      } catch (error) {
        console.error('Error loading active trips:', error);
      }
    };

    const loadAnalytics = async () => {
      try {
        const [driverData, vehicleData] = await Promise.all([
          getDriverAnalytics(analyticsTimeframe),
          getVehicleAnalytics(analyticsTimeframe),
        ]);

        console.log('Driver data: ', driverData);
        console.log('Vehicle data: ', vehicleData);

        // No need to access .data since the API returns the correct structure
        setDriverAnalytics(driverData);
        setVehicleAnalytics(vehicleData);
      } catch (error) {
        console.error('Error loading analytics:', error);
      }
    };

    loadActiveTrips();
    loadAnalytics();

    // Set up polling for active trips
    const pollInterval = setInterval(loadActiveTrips, 30000); // Poll every 30 seconds

    return () => clearInterval(pollInterval);
  }, [analyticsTimeframe]); // Re-run when timeframe changes

  useEffect(() => {
    const loadDrivers = async () => {
      try {
        const response = await getAllDrivers();
        console.log('Response received for drivers: ', response);

        const data = response.data.data;
        // Extract drivers from the nested response structure
        const driversData = data?.drivers || [];

        // Filter for available drivers (is_active: false)
        const availableDrivers = driversData.filter(driver => driver.status === 'available');

        console.log('Available drivers: ', availableDrivers);
        setDrivers(availableDrivers);
      } catch (error) {
        console.error('Error loading drivers:', error);
      }
    };

    loadDrivers();
  }, []);

  const stats = {
    activeVehicles: vehicles.filter(v => v.status === 'available' || v.status === 'active').length,
    idleVehicles: vehicles.filter(v => v.status === 'inactive' || v.status === 'maintenance')
      .length,
  };

  // Pagination logic for vehicle overview table
  const totalPages = Math.ceil(vehicles.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const currentVehicles = vehicles.slice(startIndex, startIndex + itemsPerPage);

  const goToNextPage = () => {
    setCurrentPage(prev => Math.min(prev + 1, totalPages));
  };

  const goToPrevPage = () => {
    setCurrentPage(prev => Math.max(prev - 1, 1));
  };

  const changeItemsPerPage = e => {
    setItemsPerPage(parseInt(e.target.value));
    setCurrentPage(1); // Reset to first page
  };

  const handleSelectVehicle = vehicle => {
    // Vehicle selection logic can be added here if needed
  };

  const handleScheduleTrip = () => {
    // Update the form with current date and time values when opening
    setTripForm(prev => ({
      ...prev,
      scheduledStartDate: getCurrentDate(),
      scheduledStartTime: getCurrentTime(),
    }));
    setShowScheduleModal(true);
  };

  const handleCloseModal = () => {
    setShowScheduleModal(false);
    setTripForm({
      name: '',
      description: '',
      vehicleId: '',
      driverId: '',
      startLocation: '',
      endLocation: '',
      scheduledStartDate: getCurrentDate(),
      scheduledStartTime: getCurrentTime(),
      scheduledEndDate: '',
      scheduledEndTime: '',
      priority: 'normal',
      temperatureControl: false,
      driverNote: '',
    });
    // Reset location coordinates
    setLocationCoords({
      start: null,
      end: null,
    });
  };

  const handleFormChange = (field, value) => {
    // Log vehicle selection changes to help with debugging
    if (field === 'vehicleId' && value) {
      const selectedVehicle = vehicles.find(v => (v.id || v._id) === value);
      console.log('Selected vehicle:', selectedVehicle);
    }

    setTripForm(prev => ({
      ...prev,
      [field]: value,
    }));
  };
  const formatTripData = () => {
    const startDateTime = `${tripForm.scheduledStartDate}T${tripForm.scheduledStartTime}:00Z`;
    const endDateTime = `${tripForm.scheduledEndDate}T${tripForm.scheduledEndTime}:00Z`;

    return {
      name: tripForm.name,
      description: tripForm.description,
      scheduled_start_time: startDateTime,
      scheduled_end_time: endDateTime,
      origin: {
        location: {
          type: 'Point',
          coordinates: [locationCoords.start?.lng, locationCoords.start?.lat],
        },
        name: tripForm.startLocation,
        order: 0,
      },
      destination: {
        location: {
          type: 'Point',
          coordinates: [locationCoords.end?.lng, locationCoords.end?.lat],
        },
        name: tripForm.endLocation,
        order: 99,
      },
      waypoints: [], // Can be extended later for intermediate stops
      priority: tripForm.priority,
      vehicle_id: tripForm.vehicleId,
      driver_assignment: tripForm.driverId,
      constraints: [], // Time window constraints removed as per requirements
      custom_fields: {
        driver_note: tripForm.driverNote,
      },
    };
  };

  const handleSubmitTrip = async enhancedTripData => {
    // If called from form event, prevent default and use old logic
    if (enhancedTripData && enhancedTripData.preventDefault) {
      enhancedTripData.preventDefault();

      // Validate required fields for old form
      if (
        !tripForm.name ||
        !tripForm.vehicleId ||
        !tripForm.startLocation ||
        !tripForm.endLocation ||
        !tripForm.scheduledStartDate ||
        !tripForm.scheduledStartTime ||
        !tripForm.scheduledEndDate ||
        !tripForm.scheduledEndTime
      ) {
        alert('Please fill in all required fields');
        return;
      }

      if (!locationCoords.start || !locationCoords.end) {
        alert('Please select valid locations from the dropdown suggestions');
        return;
      }

      // Use old data format
      enhancedTripData = null;
    }

    setIsSubmitting(true);

    try {
      // Use enhanced trip data if provided, otherwise format current trip form
      let tripData;
      if (enhancedTripData) {
        // Enhanced data from the new modal with route information
        const startDateTime = `${enhancedTripData.scheduledStartDate}T${enhancedTripData.scheduledStartTime}:00Z`;
        const endDateTime = `${enhancedTripData.scheduledEndDate}T${enhancedTripData.scheduledEndTime}:00Z`;

        tripData = {
          name: enhancedTripData.name,
          description: enhancedTripData.description,
          scheduled_start_time: startDateTime,
          scheduled_end_time: endDateTime,
          origin: {
            name: enhancedTripData.startLocation,
            coordinates: enhancedTripData.coordinates?.start || locationCoords.start,
          },
          destination: {
            name: enhancedTripData.endLocation,
            coordinates: enhancedTripData.coordinates?.end || locationCoords.end,
          },
          priority: enhancedTripData.priority,
          vehicle_id: enhancedTripData.vehicleId,
          driver_assignment: enhancedTripData.driverId,
          // Enhanced route information
          waypoints: enhancedTripData.waypoints || [],
          route_info: enhancedTripData.routeInfo || null,
          driver_note: enhancedTripData.driverNote,
        };
      } else {
        // Fallback to existing format method
        tripData = formatTripData();
      }

      console.log('Creating trip with data:', tripData);

      const response = await createTrip(tripData);
      console.log('Trip created successfully:', response);

      if (response.data.status === 'success') {
        alert('Trip scheduled successfully!');
      } else {
        alert('Failed to create trip: ', response.data.message);
      }
      handleCloseModal();
    } catch (error) {
      console.error('Error scheduling trip:', error);
      alert(`Failed to schedule trip: ${error.message || 'Please try again.'}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  // More permissive filtering to include vehicles with different status formats
  const availableVehicles = vehicles.filter(v => {
    // Check if vehicle exists and has a valid structure
    if (!v) return false;

    // More inclusive filtering logic - accept available, operational, and inactive vehicles
    const status = (v.status || '').toLowerCase();
    return (
      status === 'available' ||
      status === 'operational' ||
      status === 'active' ||
      status === '' || // Include vehicles with no status
      !v.status
    ); // Include vehicles where status is not defined
  });

  console.log('Filtered available vehicles:', availableVehicles);
  const availableDrivers = drivers;

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
            <p className="mt-2">Loading vehicles...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
          <p>{error}</p>
          <button
            onClick={() => window.location.reload()}
            className="mt-2 bg-red-500 text-white px-4 py-2 rounded hover:bg-red-600"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="relative container mx-auto px-4 py-8">
      {/* Background pattern */}
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
        <h1 className="text-3xl font-bold mb-6 animate-fade-in text-foreground">Trip Management</h1>
        <div className="animate-fade-in animate-delay-100">
          <ActiveTripsPanel activeTrips={activeTrips} />
        </div>
        <div className="animate-fade-in animate-delay-200">
          <SchedulingPanel
            availableVehicles={availableVehicles.length}
            availableDrivers={availableDrivers.length}
            onScheduleClick={handleScheduleTrip}
          />
        </div>
        <div className="animate-fade-in animate-delay-300">
          <TripsAnalytics
            driverData={driverAnalytics} // Add driver analytics data
            vehicleData={vehicleAnalytics} // Add vehicle analytics data
            timeframe={analyticsTimeframe}
            onTimeframeChange={setAnalyticsTimeframe} // Add timeframe change handler
          />
        </div>
        <div className="animate-fade-in animate-delay-400">
          <TripsHistory trips={[]} />
        </div>
        <div className="animate-fade-in animate-delay-500">
          <VehicleStatistics stats={stats} />
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 animate-fade-in animate-delay-600">
          <div className="lg:col-span-1">
            <VehicleList vehicles={vehicles} onSelectVehicle={handleSelectVehicle} />
          </div>
        </div>
        <div className="mt-6 flex justify-end animate-fade-in animate-delay-700">
          <button
            className="bg-primary text-primary-foreground px-4 py-2 rounded-md hover:bg-primary/90 transition"
            onClick={handleScheduleTrip}
          >
            Schedule New Trip
          </button>
        </div>
        {/* Enhanced Trip Scheduling Modal with Map */}
        <TripSchedulingModal
          showModal={showScheduleModal}
          onClose={handleCloseModal}
          onSubmit={handleSubmitTrip}
          tripForm={tripForm}
          onFormChange={handleFormChange}
          vehicles={vehicles}
          drivers={drivers}
          isSubmitting={isSubmitting}
          availableVehicles={availableVehicles}
        />
        {/* Trip History Section */}
        <div className="mt-8">
          <h2 className="text-xl font-semibold mb-4">Vehicle Overview</h2>
          <div className="bg-card rounded-lg shadow-md p-6 border border-border">
            <div className="overflow-x-auto">
              <table className="w-full border-collapse">
                <thead>
                  <tr className="border-b border-border">
                    <th className="text-left py-3 px-4">License Plate</th>
                    <th className="text-left py-3 px-4">Make & Model</th>
                    <th className="text-left py-3 px-4">Year</th>
                    <th className="text-left py-3 px-4">Department</th>
                    <th className="text-left py-3 px-4">Status</th>
                    <th className="text-left py-3 px-4">Mileage</th>
                    <th className="text-left py-3 px-4">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {currentVehicles.length > 0 ? (
                    currentVehicles.map(vehicle => (
                      <tr key={vehicle.id} className="border-b border-border hover:bg-accent/10">
                        <td className="py-3 px-4">
                          {vehicle.license_plate || vehicle.registration_number}
                        </td>
                        <td className="py-3 px-4">
                          {vehicle.make} {vehicle.model}
                        </td>
                        <td className="py-3 px-4">{vehicle.year}</td>
                        <td className="py-3 px-4">{vehicle.department}</td>
                        <td className="py-3 px-4">
                          <span
                            className={
                              vehicle.status === 'available' || vehicle.status === 'active'
                                ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200 py-1 px-2 rounded-full text-xs'
                                : 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200 py-1 px-2 rounded-full text-xs'
                            }
                          >
                            {vehicle.status.charAt(0).toUpperCase() + vehicle.status.slice(1)}
                          </span>
                        </td>
                        <td className="py-3 px-4">{vehicle.mileage.toLocaleString()} km</td>
                        <td className="py-3 px-4">
                          <button
                            className="text-primary hover:text-primary/80"
                            onClick={() => handleSelectVehicle(vehicle)}
                          >
                            View Details
                          </button>
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan={7} className="py-3 px-4 text-center text-muted-foreground">
                        No vehicle data available
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
            {/* Add Pagination */}
            {vehicles.length > 0 && (
              <Pagination
                currentPage={currentPage}
                totalPages={totalPages}
                itemsPerPage={itemsPerPage}
                goToNextPage={goToNextPage}
                goToPrevPage={goToPrevPage}
                changeItemsPerPage={changeItemsPerPage}
              />
            )}
          </div>
        </div>

        {/* Trip Scheduling Modal */}
        <TripSchedulingModal
          showModal={showScheduleModal}
          onClose={handleCloseModal}
          onSubmit={handleSubmitTrip}
          tripForm={tripForm}
          onFormChange={handleFormChange}
          vehicles={vehicles}
          drivers={drivers}
          isSubmitting={isSubmitting}
          availableVehicles={availableVehicles}
        />
      </div>
    </div>
  );
};

export default Trips;
