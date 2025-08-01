import React, {useState, useEffect} from 'react';
import ActiveTripsPanel from '../components/trips/ActiveTripsPanel';
import SchedulingPanel from '../components/trips/SchedulingPanel';
import TripsAnalytics from '../components/trips/TripsAnalytics';
import TripsHistory from '../components/trips/TripsHistory';
import LocationAutocomplete from '../components/trips/LocationAutocomplete';
import VehicleStatistics from '../components/trips/VehicleStatistics';
import VehicleList from '../components/trips/VehicleList';
import { createTrip,
  getActiveTrips,
  getDriverAnalytics,
  getVehicleAnalytics,
 } from '../backend/api/trips';

import { getVehicles } from '../backend/api/vehicles'

const Trips = () => {
  // Existing state
  const [vehicles, setVehicles] = useState([]);
  
  // New state for features
  const [activeTrips, setActiveTrips] = useState([]);
  const [drivers, setDrivers] = useState([]);
  const [tripsHistory, setTripsHistory] = useState([]);
  const [analyticsTimeframe, setAnalyticsTimeframe] = useState('week');
  const [driverAnalytics, setDriverAnalytics] = useState({
    drivers: [],
    timeframeSummary: {
      totalTrips: 0,
      completionRate: 0,
      averageTripsPerDay: 0
    }
  });
  const [vehicleAnalytics, setVehicleAnalytics] = useState({
    vehicles: [],
    timeframeSummary: {
      totalDistance: 0
    }
  });
  const [selectedVehicle, setSelectedVehicle] = useState(null);
  const [showScheduleModal, setShowScheduleModal] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Updated trip form state to match new API format
  const [tripForm, setTripForm] = useState({
    name: '',
    description: '',
    vehicleId: '',
    startLocation: '',
    endLocation: '',
    scheduledStartDate: '',
    scheduledStartTime: '',
    scheduledEndDate: '',
    scheduledEndTime: '',
    priority: 'medium',
    temperatureControl: false,
    driverNote: '',
    timeWindowStart: '',
    timeWindowEnd: ''
  });

  // Store coordinates for selected locations
  const [locationCoords, setLocationCoords] = useState({
    start: null,
    end: null
  });

  useEffect(() => {
    const loadVehicles = async () => {
      try {
        setLoading(true);
        setError(null);

        const response = await getVehicles();
        
        // Extract vehicles from the nested response structure
        const vehicleData = response?.data?.data?.data?.vehicles || 
                           response?.data?.data?.vehicles || 
                           response?.data?.vehicles || 
                           response?.vehicles || 
                           [];

        console.log('Loaded vehicles:', vehicleData);
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
          getVehicleAnalytics(analyticsTimeframe)
        ]);
        
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

  const stats = {
    activeVehicles: vehicles.filter(v => v.status === 'available' || v.status === 'active').length,
    idleVehicles: vehicles.filter(v => v.status === 'inactive' || v.status === 'maintenance').length,
  };

  const handleSelectVehicle = vehicle => {
    setSelectedVehicle(vehicle);
  };

  const handleScheduleTrip = () => {
    setShowScheduleModal(true);
  };

  const handleCloseModal = () => {
    setShowScheduleModal(false);
    setTripForm({
      name: '',
      description: '',
      vehicleId: '',
      startLocation: '',
      endLocation: '',
      scheduledStartDate: '',
      scheduledStartTime: '',
      scheduledEndDate: '',
      scheduledEndTime: '',
      priority: 'medium',
      temperatureControl: false,
      driverNote: '',
      timeWindowStart: '',
      timeWindowEnd: ''
    });
    setLocationCoords({
      start: null,
      end: null
    });
  };

  const handleFormChange = (field, value) => {
    setTripForm(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleStartLocationChange = (address, locationData) => {
    handleFormChange('startLocation', address);
    setLocationCoords(prev => ({
      ...prev,
      start: locationData
    }));
  };

  const handleEndLocationChange = (address, locationData) => {
    handleFormChange('endLocation', address);
    setLocationCoords(prev => ({
      ...prev,
      end: locationData
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
          type: "Point",
          coordinates: [locationCoords.start?.lng, locationCoords.start?.lat]
        },
        name: tripForm.startLocation,
        order: 0
      },
      destination: {
        location: {
          type: "Point",
          coordinates: [locationCoords.end?.lng, locationCoords.end?.lat]
        },
        name: tripForm.endLocation,
        order: 99
      },
      waypoints: [], // Can be extended later for intermediate stops
      priority: tripForm.priority,
      vehicle_id: tripForm.vehicleId,
      constraints: tripForm.timeWindowStart && tripForm.timeWindowEnd ? [
        {
          trip_id: "placeholder_trip_id", // Will be set by backend
          type: "time_window",
          value: {
            start: tripForm.timeWindowStart,
            end: tripForm.timeWindowEnd
          },
          priority: 1,
          is_active: true
        }
      ] : [],
      custom_fields: {
        temperature_control: tripForm.temperatureControl ? "yes" : "no",
        driver_note: tripForm.driverNote
      }
    };
  };

  const handleSubmitTrip = async (e) => {
    e.preventDefault();

    // Validate required fields
    if (!tripForm.name || !tripForm.vehicleId || !tripForm.startLocation ||
      !tripForm.endLocation || !tripForm.scheduledStartDate || 
      !tripForm.scheduledStartTime || !tripForm.scheduledEndDate || 
      !tripForm.scheduledEndTime) {
      alert('Please fill in all required fields');
      return;
    }

    if (!locationCoords.start || !locationCoords.end) {
      alert('Please select valid locations from the dropdown suggestions');
      return;
    }

    setIsSubmitting(true);

    try {
      const tripData = formatTripData();
      console.log('Creating trip with data:', tripData);

      const response = await createTrip(tripData);
      console.log('Trip created successfully:', response);

      alert('Trip scheduled successfully!');
      handleCloseModal();
    } catch (error) {
      console.error('Error scheduling trip:', error);
      alert(`Failed to schedule trip: ${error.message || 'Please try again.'}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  const availableVehicles = vehicles.filter(v => v.status === 'available' || v.status === 'active');

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
        <h1 className="text-3xl font-bold mb-6">Trip Management</h1>

        <ActiveTripsPanel activeTrips={activeTrips} /> {/* Add active trips data */}

        <SchedulingPanel 
          availableVehicles={availableVehicles.length}
          availableDrivers={0} // Add driver data
          onScheduleClick={handleScheduleTrip}
        />

        <TripsAnalytics 
          driverData={driverAnalytics} // Add driver analytics data
          vehicleData={vehicleAnalytics} // Add vehicle analytics data
          timeframe={analyticsTimeframe}
          onTimeframeChange={setAnalyticsTimeframe} // Add timeframe change handler
        />

        <TripsHistory trips={[]} /> {/* Add trips history data */}

        <VehicleStatistics stats={stats} />

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-1">
            <VehicleList vehicles={vehicles} onSelectVehicle={handleSelectVehicle} />
          </div>
        </div>

        <div className="mt-6 flex justify-end">
          <button
            className="bg-primary text-primary-foreground px-4 py-2 rounded-md hover:bg-primary/90 transition"
            onClick={handleScheduleTrip}
          >
            Schedule New Trip
          </button>
        </div>

        {/* Updated Schedule Trip Modal */}
        {showScheduleModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[9999] p-4">
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
              <div className="p-6">
                <div className="flex justify-between items-center mb-6">
                  <h2 className="text-2xl font-bold">Schedule New Trip</h2>
                  <button
                    onClick={handleCloseModal}
                    className="text-gray-400 hover:text-gray-600 text-2xl"
                    disabled={isSubmitting}
                  >
                    ×
                  </button>
                </div>

                <form onSubmit={handleSubmitTrip} className="space-y-6">
                  {/* Trip Details Section */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium mb-2">
                        Trip Name <span className="text-red-500">*</span>
                      </label>
                      <input
                        type="text"
                        value={tripForm.name}
                        onChange={(e) => handleFormChange('name', e.target.value)}
                        placeholder="e.g., Morning Delivery Route"
                        className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary"
                        required
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-2">
                        Priority
                      </label>
                      <select
                        value={tripForm.priority}
                        onChange={(e) => handleFormChange('priority', e.target.value)}
                        className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary"
                      >
                        <option value="low">Low</option>
                        <option value="medium">Medium</option>
                        <option value="high">High</option>
                      </select>
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-2">
                      Description
                    </label>
                    <textarea
                      value={tripForm.description}
                      onChange={(e) => handleFormChange('description', e.target.value)}
                      placeholder="Brief description of the trip purpose"
                      rows="2"
                      className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary"
                    />
                  </div>

                  {/* Vehicle Selection */}
                  <div>
                    <label className="block text-sm font-medium mb-2">
                      Select Vehicle <span className="text-red-500">*</span>
                    </label>
                    <select
                      value={tripForm.vehicleId}
                      onChange={(e) => handleFormChange('vehicleId', e.target.value)}
                      className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary"
                      required
                    >
                      <option value="">Choose a vehicle...</option>
                      {availableVehicles.map(vehicle => (
                        <option key={vehicle.id} value={vehicle.id}>
                          {vehicle.make} {vehicle.model} ({vehicle.license_plate || vehicle.registration_number})
                        </option>
                      ))}
                    </select>
                    {availableVehicles.length === 0 && (
                      <p className="text-sm text-red-500 mt-1">No available vehicles</p>
                    )}
                  </div>

                  {/* Location Section */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium mb-2">
                        Start Location <span className="text-red-500">*</span>
                      </label>
                      <LocationAutocomplete
                        value={tripForm.startLocation}
                        onChange={handleStartLocationChange}
                        placeholder="Enter start location or address"
                        className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary"
                        required
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-2">
                        End Location <span className="text-red-500">*</span>
                      </label>
                      <LocationAutocomplete
                        value={tripForm.endLocation}
                        onChange={handleEndLocationChange}
                        placeholder="Enter destination location or address"
                        className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary"
                        required
                      />
                    </div>
                  </div>

                  {/* Schedule Section */}
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div>
                      <label className="block text-sm font-medium mb-2">
                        Start Date <span className="text-red-500">*</span>
                      </label>
                      <input
                        type="date"
                        value={tripForm.scheduledStartDate}
                        onChange={(e) => handleFormChange('scheduledStartDate', e.target.value)}
                        min={new Date().toISOString().split('T')[0]}
                        className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary"
                        required
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-2">
                        Start Time <span className="text-red-500">*</span>
                      </label>
                      <input
                        type="time"
                        value={tripForm.scheduledStartTime}
                        onChange={(e) => handleFormChange('scheduledStartTime', e.target.value)}
                        className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary"
                        required
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-2">
                        End Date <span className="text-red-500">*</span>
                      </label>
                      <input
                        type="date"
                        value={tripForm.scheduledEndDate}
                        onChange={(e) => handleFormChange('scheduledEndDate', e.target.value)}
                        min={tripForm.scheduledStartDate || new Date().toISOString().split('T')[0]}
                        className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary"
                        required
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-2">
                        End Time <span className="text-red-500">*</span>
                      </label>
                      <input
                        type="time"
                        value={tripForm.scheduledEndTime}
                        onChange={(e) => handleFormChange('scheduledEndTime', e.target.value)}
                        className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary"
                        required
                      />
                    </div>
                  </div>

                  {/* Time Window Constraints (Optional) */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium mb-2">
                        Time Window Start (Optional)
                      </label>
                      <input
                        type="time"
                        value={tripForm.timeWindowStart}
                        onChange={(e) => handleFormChange('timeWindowStart', e.target.value)}
                        className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-2">
                        Time Window End (Optional)
                      </label>
                      <input
                        type="time"
                        value={tripForm.timeWindowEnd}
                        onChange={(e) => handleFormChange('timeWindowEnd', e.target.value)}
                        className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary"
                      />
                    </div>
                  </div>

                  {/* Custom Fields */}
                  <div className="space-y-4">
                    <div className="flex items-center">
                      <input
                        type="checkbox"
                        id="temperatureControl"
                        checked={tripForm.temperatureControl}
                        onChange={(e) => handleFormChange('temperatureControl', e.target.checked)}
                        className="mr-2"
                      />
                      <label htmlFor="temperatureControl" className="text-sm font-medium">
                        Temperature Control Required
                      </label>
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-2">
                        Driver Notes
                      </label>
                      <textarea
                        value={tripForm.driverNote}
                        onChange={(e) => handleFormChange('driverNote', e.target.value)}
                        placeholder="Special instructions for the driver..."
                        rows="3"
                        className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary"
                      />
                    </div>
                  </div>

                  {/* Form Actions */}
                  <div className="flex justify-end space-x-3 pt-4">
                    <button
                      type="button"
                      onClick={handleCloseModal}
                      className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 transition"
                      disabled={isSubmitting}
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition disabled:opacity-50"
                      disabled={availableVehicles.length === 0 || isSubmitting}
                    >
                      {isSubmitting ? 'Scheduling...' : 'Schedule Trip'}
                    </button>
                  </div>
                </form>
              </div>
            </div>
          </div>
        )}

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
                  {vehicles.length > 0 ? (
                    vehicles.map(vehicle => (
                      <tr key={vehicle.id} className="border-b border-border hover:bg-accent/10">
                        <td className="py-3 px-4">{vehicle.license_plate || vehicle.registration_number}</td>
                        <td className="py-3 px-4">{vehicle.make} {vehicle.model}</td>
                        <td className="py-3 px-4">{vehicle.year}</td>
                        <td className="py-3 px-4">{vehicle.department}</td>
                        <td className="py-3 px-4">
                          <span className={
                            vehicle.status === 'available' || vehicle.status === 'active'
                              ? "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200 py-1 px-2 rounded-full text-xs"
                              : "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200 py-1 px-2 rounded-full text-xs"
                          }>
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
          </div>
        </div>
      </div>
    </div>
  );
};

export default Trips;