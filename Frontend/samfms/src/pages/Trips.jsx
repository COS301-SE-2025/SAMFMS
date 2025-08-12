import React, { useState, useEffect } from 'react';
import ActiveTripsPanel from '../components/trips/ActiveTripsPanel';
import SchedulingPanel from '../components/trips/SchedulingPanel';
import TripsAnalytics from '../components/trips/TripsAnalytics';
import TripsHistory from '../components/trips/TripsHistory';
import LocationAutocomplete from '../components/trips/LocationAutocomplete';
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
  const [selectedVehicle, setSelectedVehicle] = useState(null);
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

  // State for toggling description and driver notes visibility
  const [showDescription, setShowDescription] = useState(false);
  const [showDriverNotes, setShowDriverNotes] = useState(false);

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
    setSelectedVehicle(vehicle);
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
    // Reset toggle state
    setShowDescription(false);
    setShowDriverNotes(false);
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

  const handleStartLocationChange = (address, locationData) => {
    handleFormChange('startLocation', address);
    setLocationCoords(prev => ({
      ...prev,
      start: locationData,
    }));
  };

  const handleEndLocationChange = (address, locationData) => {
    handleFormChange('endLocation', address);
    setLocationCoords(prev => ({
      ...prev,
      end: locationData,
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

  const handleSubmitTrip = async e => {
    e.preventDefault();

    // Validate required fields
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

    setIsSubmitting(true);

    try {
      const tripData = formatTripData();
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
        <div className="animate-fade-in" style={{ animationDelay: '0.1s' }}>
          <ActiveTripsPanel activeTrips={activeTrips} />
        </div>
        <div className="animate-fade-in" style={{ animationDelay: '0.2s' }}>
          <SchedulingPanel
            availableVehicles={availableVehicles.length}
            availableDrivers={availableDrivers.length}
            onScheduleClick={handleScheduleTrip}
          />
        </div>
        <div className="animate-fade-in" style={{ animationDelay: '0.3s' }}>
          <TripsAnalytics
            driverData={driverAnalytics} // Add driver analytics data
            vehicleData={vehicleAnalytics} // Add vehicle analytics data
            timeframe={analyticsTimeframe}
            onTimeframeChange={setAnalyticsTimeframe} // Add timeframe change handler
          />
        </div>
        <div className="animate-fade-in" style={{ animationDelay: '0.4s' }}>
          <TripsHistory trips={[]} />
        </div>
        <div className="animate-fade-in" style={{ animationDelay: '0.5s' }}>
          <VehicleStatistics stats={stats} />
        </div>
        <div
          className="grid grid-cols-1 lg:grid-cols-3 gap-6 animate-fade-in"
          style={{ animationDelay: '0.6s' }}
        >
          <div className="lg:col-span-1">
            <VehicleList vehicles={vehicles} onSelectVehicle={handleSelectVehicle} />
          </div>
        </div>
        <div className="mt-6 flex justify-end animate-fade-in" style={{ animationDelay: '0.7s' }}>
          <button
            className="bg-primary text-primary-foreground px-4 py-2 rounded-md hover:bg-primary/90 transition"
            onClick={handleScheduleTrip}
          >
            Schedule New Trip
          </button>
        </div>
        {/* Updated Schedule Trip Modal */}
        {showScheduleModal && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-[9999] p-4">
            <div className="bg-card dark:bg-card rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto border border-border">
              <div className="p-6">
                <div className="flex justify-between items-center mb-6">
                  <h2 className="text-2xl font-bold text-foreground">Schedule New Trip</h2>
                  <button
                    onClick={handleCloseModal}
                    className="text-muted-foreground hover:text-foreground text-2xl transition-colors"
                    disabled={isSubmitting}
                  >
                    ×
                  </button>
                </div>

                <form onSubmit={handleSubmitTrip} className="space-y-6">
                  {/* Trip Details Section */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium mb-2 text-foreground">
                        Trip Name <span className="text-red-500">*</span>
                      </label>
                      <div className="relative">
                        <input
                          type="text"
                          value={tripForm.name}
                          onChange={e => handleFormChange('name', e.target.value.slice(0, 25))}
                          placeholder="e.g., Morning Delivery Route"
                          maxLength={25}
                          className="w-full border border-input rounded-md px-3 py-2 bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                          required
                        />
                        <div className="absolute right-2 bottom-2 text-xs text-muted-foreground">
                          {tripForm.name.length}/25
                        </div>
                      </div>
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-3 text-foreground">
                        Priority
                      </label>
                      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                        <button
                          type="button"
                          onClick={() => handleFormChange('priority', 'low')}
                          className={`px-3 py-2 rounded-md border ${
                            tripForm.priority === 'low'
                              ? 'bg-green-100 border-green-300 ring-2 ring-green-300'
                              : 'bg-background border-input hover:bg-green-50'
                          } transition-colors`}
                        >
                          <div className="flex items-center justify-center gap-2">
                            <span className="h-3 w-3 rounded-full bg-green-500"></span>
                            <span className="font-medium text-green-700">Low</span>
                          </div>
                        </button>
                        <button
                          type="button"
                          onClick={() => handleFormChange('priority', 'normal')}
                          className={`px-3 py-2 rounded-md border ${
                            tripForm.priority === 'normal'
                              ? 'bg-blue-100 border-blue-300 ring-2 ring-blue-300'
                              : 'bg-background border-input hover:bg-blue-50'
                          } transition-colors`}
                        >
                          <div className="flex items-center justify-center gap-2">
                            <span className="h-3 w-3 rounded-full bg-blue-500"></span>
                            <span className="font-medium text-blue-700">Normal</span>
                          </div>
                        </button>
                        <button
                          type="button"
                          onClick={() => handleFormChange('priority', 'high')}
                          className={`px-3 py-2 rounded-md border ${
                            tripForm.priority === 'high'
                              ? 'bg-amber-100 border-amber-300 ring-2 ring-amber-300'
                              : 'bg-background border-input hover:bg-amber-50'
                          } transition-colors`}
                        >
                          <div className="flex items-center justify-center gap-2">
                            <span className="h-3 w-3 rounded-full bg-amber-500"></span>
                            <span className="font-medium text-amber-700">High</span>
                          </div>
                        </button>
                        <button
                          type="button"
                          onClick={() => handleFormChange('priority', 'urgent')}
                          className={`px-3 py-2 rounded-md border ${
                            tripForm.priority === 'urgent'
                              ? 'bg-red-100 border-red-300 ring-2 ring-red-300'
                              : 'bg-background border-input hover:bg-red-50'
                          } transition-colors`}
                        >
                          <div className="flex items-center justify-center gap-2">
                            <span className="h-3 w-3 rounded-full bg-red-500"></span>
                            <span className="font-medium text-red-700">Urgent</span>
                          </div>
                        </button>
                      </div>
                    </div>
                  </div>

                  {/* Vehicle and Driver Selection - Side by Side */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {/* Vehicle Selection */}
                    <div>
                      <label className="block text-sm font-medium mb-2 text-foreground">
                        Select Vehicle <span className="text-red-500">*</span>
                      </label>
                      <select
                        value={tripForm.vehicleId}
                        onChange={e => handleFormChange('vehicleId', e.target.value)}
                        className={`w-full border ${
                          availableVehicles.length === 0 ? 'border-red-300' : 'border-input'
                        } rounded-md px-3 py-2 bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent`}
                        required
                      >
                        <option value="">Choose a vehicle...</option>
                        {availableVehicles.map(vehicle => (
                          <option key={vehicle.id || vehicle._id} value={vehicle.id || vehicle._id}>
                            {vehicle.make || 'Unknown Make'} {vehicle.model || 'Unknown Model'} (
                            {vehicle.license_plate || vehicle.registration_number || 'No plate'})
                          </option>
                        ))}
                        {vehicles.length > 0 && availableVehicles.length === 0 && (
                          <option value="" disabled>
                            -- No available vehicles --
                          </option>
                        )}
                      </select>
                      {availableVehicles.length === 0 && vehicles.length > 0 && (
                        <p className="text-sm text-red-500 mt-1">
                          No vehicles are currently available for scheduling
                        </p>
                      )}
                      {vehicles.length === 0 && (
                        <p className="text-sm text-red-500 mt-1">
                          Failed to load vehicles. Please refresh the page.
                        </p>
                      )}
                    </div>

                    {/* Driver Selection */}
                    <div>
                      <label className="block text-sm font-medium mb-2 text-foreground">
                        Select Driver <span className="text-red-500">*</span>
                      </label>
                      <select
                        value={tripForm.driverId}
                        onChange={e => handleFormChange('driverId', e.target.value)}
                        className="w-full border border-input rounded-md px-3 py-2 bg-background text-foreground focus:ring-2 focus:ring-primary focus:border-transparent"
                        required
                      >
                        <option value="">Select a driver</option>
                        {drivers.map(driver => (
                          <option key={driver._id} value={driver.employee_id}>
                            {`${driver.first_name} ${driver.last_name} (${driver.employee_id})`}
                          </option>
                        ))}
                      </select>
                    </div>
                  </div>

                  {/* Location Section */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium mb-2 text-foreground">
                        Start Location <span className="text-red-500">*</span>
                      </label>
                      <LocationAutocomplete
                        value={tripForm.startLocation}
                        onChange={handleStartLocationChange}
                        placeholder="Enter start location or address"
                        className="w-full border border-input rounded-md px-3 py-2 bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                        required
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-2 text-foreground">
                        End Location <span className="text-red-500">*</span>
                      </label>
                      <LocationAutocomplete
                        value={tripForm.endLocation}
                        onChange={handleEndLocationChange}
                        placeholder="Enter destination location or address"
                        className="w-full border border-input rounded-md px-3 py-2 bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                        required
                      />
                    </div>
                  </div>

                  {/* Schedule Section */}
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div>
                      <label className="block text-sm font-medium mb-2 text-foreground">
                        Start Date <span className="text-red-500">*</span>
                      </label>
                      <input
                        type="date"
                        value={tripForm.scheduledStartDate}
                        onChange={e => handleFormChange('scheduledStartDate', e.target.value)}
                        min={new Date().toISOString().split('T')[0]}
                        className="w-full border border-input rounded-md px-3 py-2 bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                        required
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-2 text-foreground">
                        Start Time <span className="text-red-500">*</span>
                      </label>
                      <input
                        type="time"
                        value={tripForm.scheduledStartTime}
                        onChange={e => handleFormChange('scheduledStartTime', e.target.value)}
                        className="w-full border border-input rounded-md px-3 py-2 bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                        required
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-2 text-foreground">
                        End Date <span className="text-red-500">*</span>
                      </label>
                      <input
                        type="date"
                        value={tripForm.scheduledEndDate}
                        onChange={e => handleFormChange('scheduledEndDate', e.target.value)}
                        min={tripForm.scheduledStartDate || new Date().toISOString().split('T')[0]}
                        className="w-full border border-input rounded-md px-3 py-2 bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                        required
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-2 text-foreground">
                        End Time <span className="text-red-500">*</span>
                      </label>
                      <input
                        type="time"
                        value={tripForm.scheduledEndTime}
                        onChange={e => handleFormChange('scheduledEndTime', e.target.value)}
                        className="w-full border border-input rounded-md px-3 py-2 bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                        required
                      />
                    </div>
                  </div>

                  {/* Additional Fields */}
                  <div className="space-y-4">
                    {/* Description with toggle button */}
                    <div className="border border-border rounded-lg overflow-hidden">
                      <button
                        type="button"
                        onClick={() => setShowDescription(prev => !prev)}
                        className="flex items-center justify-between w-full p-3 text-sm font-medium text-foreground hover:bg-accent/50 transition-colors"
                      >
                        <div className="flex items-center">
                          <span className="w-6 h-6 rounded-full bg-primary/10 text-primary flex items-center justify-center mr-2">
                            <svg
                              xmlns="http://www.w3.org/2000/svg"
                              width="16"
                              height="16"
                              viewBox="0 0 24 24"
                              fill="none"
                              stroke="currentColor"
                              strokeWidth="2"
                              strokeLinecap="round"
                              strokeLinejoin="round"
                            >
                              <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
                              <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
                            </svg>
                          </span>
                          {showDescription ? 'Hide Trip Description' : 'Add Trip Description'}
                        </div>
                        <svg
                          xmlns="http://www.w3.org/2000/svg"
                          className={`h-5 w-5 transition-transform ${
                            showDescription ? 'rotate-180' : ''
                          }`}
                          fill="none"
                          viewBox="0 0 24 24"
                          stroke="currentColor"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M19 9l-7 7-7-7"
                          />
                        </svg>
                      </button>
                      {showDescription && (
                        <div className="p-3 pt-0 border-t border-border">
                          <div className="relative">
                            <textarea
                              value={tripForm.description}
                              onChange={e =>
                                handleFormChange('description', e.target.value.slice(0, 120))
                              }
                              placeholder="Brief description of the trip purpose"
                              rows="2"
                              maxLength={120}
                              className="w-full border border-input rounded-md px-3 py-2 bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                            />
                            <div className="absolute right-2 bottom-2 text-xs text-muted-foreground">
                              {tripForm.description.length}/120
                            </div>
                          </div>
                        </div>
                      )}
                    </div>

                    {/* Driver Notes with toggle button */}
                    <div className="border border-border rounded-lg overflow-hidden">
                      <button
                        type="button"
                        onClick={() => setShowDriverNotes(prev => !prev)}
                        className="flex items-center justify-between w-full p-3 text-sm font-medium text-foreground hover:bg-accent/50 transition-colors"
                      >
                        <div className="flex items-center">
                          <span className="w-6 h-6 rounded-full bg-primary/10 text-primary flex items-center justify-center mr-2">
                            <svg
                              xmlns="http://www.w3.org/2000/svg"
                              width="16"
                              height="16"
                              viewBox="0 0 24 24"
                              fill="none"
                              stroke="currentColor"
                              strokeWidth="2"
                              strokeLinecap="round"
                              strokeLinejoin="round"
                            >
                              <path d="M18 8h1a4 4 0 0 1 0 8h-1" />
                              <path d="M2 8h16v9a4 4 0 0 1-4 4H6a4 4 0 0 1-4-4V8z" />
                              <line x1="6" y1="1" x2="6" y2="4" />
                              <line x1="10" y1="1" x2="10" y2="4" />
                              <line x1="14" y1="1" x2="14" y2="4" />
                            </svg>
                          </span>
                          {showDriverNotes ? 'Hide Driver Notes' : 'Add Driver Notes'}
                        </div>
                        <svg
                          xmlns="http://www.w3.org/2000/svg"
                          className={`h-5 w-5 transition-transform ${
                            showDriverNotes ? 'rotate-180' : ''
                          }`}
                          fill="none"
                          viewBox="0 0 24 24"
                          stroke="currentColor"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M19 9l-7 7-7-7"
                          />
                        </svg>
                      </button>
                      {showDriverNotes && (
                        <div className="p-3 pt-0 border-t border-border">
                          <div className="relative">
                            <textarea
                              value={tripForm.driverNote}
                              onChange={e =>
                                handleFormChange('driverNote', e.target.value.slice(0, 120))
                              }
                              placeholder="Special instructions for the driver..."
                              rows="3"
                              maxLength={120}
                              className="w-full border border-input rounded-md px-3 py-2 bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                            />
                            <div className="absolute right-2 bottom-2 text-xs text-muted-foreground">
                              {tripForm.driverNote.length}/120
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Form Actions */}
                  <div className="flex justify-end space-x-3 pt-4">
                    <button
                      type="button"
                      onClick={handleCloseModal}
                      className="px-4 py-2 border border-input rounded-md text-foreground bg-background hover:bg-accent transition-colors"
                      disabled={isSubmitting}
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors disabled:opacity-50"
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
      </div>
    </div>
  );
};

export default Trips;
