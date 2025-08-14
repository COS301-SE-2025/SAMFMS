import React, { useState, useEffect } from 'react';
import { Plus, MapPin, Clock, User, Calendar } from 'lucide-react';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import ActiveTripsPanel from '../components/trips/ActiveTripsPanel';
import SchedulingPanel from '../components/trips/SchedulingPanel';
import TripsAnalytics from '../components/trips/TripsAnalytics';
import TripsHistory from '../components/trips/TripsHistory';
import TripSchedulingModal from '../components/trips/TripSchedulingModal';
import Notification from '../components/common/Notification';
import {
  createTrip,
  getActiveTrips,
  getDriverAnalytics,
  getVehicleAnalytics,
} from '../backend/api/trips';

import { getVehicles } from '../backend/api/vehicles';
import { getAllDrivers } from '../backend/api/drivers';

// Fix for default markers in react-leaflet
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

// Custom vehicle icon for active trips map
const createVehicleIcon = status => {
  const color =
    status === 'In Transit' ? '#3b82f6' : status === 'At Destination' ? '#22c55e' : '#f59e0b';
  return L.divIcon({
    html: `<div style="background-color: ${color}; width: 20px; height: 20px; border-radius: 50%; border: 2px solid white; display: flex; align-items: center; justify-content: center; box-shadow: 0 2px 4px rgba(0,0,0,0.2);">
             <svg width="12" height="12" viewBox="0 0 24 24" fill="white">
               <path d="M8 7v8a2 2 0 002 2h6M8 7V5a2 2 0 012-2h4.586a1 1 0 01.707.293l4.414 4.414a1 1 0 01.293.707V15a2 2 0 01-2 2h-2M8 7H6a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2v-2"/>
             </svg>
           </div>`,
    className: 'custom-vehicle-marker',
    iconSize: [20, 20],
    iconAnchor: [10, 10],
  });
};

// Mock data for tables
const mockUpcomingTrips = [
  {
    id: 1,
    tripName: 'Delivery to Downtown Office',
    vehicle: 'Ford Transit - ABC123',
    driver: 'John Smith',
    scheduledStart: '2025-08-15 08:00',
    destination: 'Downtown Business District',
    priority: 'High',
    status: 'Scheduled',
  },
  {
    id: 2,
    tripName: 'Client Site Visit',
    vehicle: 'Toyota Camry - XYZ789',
    driver: 'Sarah Johnson',
    scheduledStart: '2025-08-15 10:30',
    destination: 'Tech Park Industrial Area',
    priority: 'Medium',
    status: 'Scheduled',
  },
  {
    id: 3,
    tripName: 'Equipment Transport',
    vehicle: 'Chevrolet Silverado - DEF456',
    driver: 'Mike Wilson',
    scheduledStart: '2025-08-15 14:00',
    destination: 'Construction Site Alpha',
    priority: 'High',
    status: 'Pending Approval',
  },
  {
    id: 4,
    tripName: 'Airport Pickup',
    vehicle: 'Honda Accord - GHI321',
    driver: 'Lisa Brown',
    scheduledStart: '2025-08-16 07:45',
    destination: 'International Airport',
    priority: 'Medium',
    status: 'Scheduled',
  },
];

const mockRecentTrips = [
  {
    id: 101,
    tripName: 'Morning Supply Run',
    vehicle: 'Ford Transit - ABC123',
    driver: 'John Smith',
    completedAt: '2025-08-14 11:30',
    destination: 'Warehouse District',
    duration: '2h 15m',
    status: 'Completed',
    distance: '45.2 miles',
  },
  {
    id: 102,
    tripName: 'Client Meeting Transport',
    vehicle: 'Toyota Camry - XYZ789',
    driver: 'Sarah Johnson',
    completedAt: '2025-08-14 09:15',
    destination: 'Corporate Center',
    duration: '1h 45m',
    status: 'Completed',
    distance: '28.7 miles',
  },
  {
    id: 103,
    tripName: 'Emergency Maintenance',
    vehicle: 'Chevrolet Silverado - DEF456',
    driver: 'Mike Wilson',
    completedAt: '2025-08-13 16:20',
    destination: 'Service Center East',
    duration: '3h 10m',
    status: 'Completed',
    distance: '67.3 miles',
  },
  {
    id: 104,
    tripName: 'Document Delivery',
    vehicle: 'Honda Accord - GHI321',
    driver: 'Lisa Brown',
    completedAt: '2025-08-13 14:00',
    destination: 'Legal District',
    duration: '45m',
    status: 'Completed',
    distance: '12.1 miles',
  },
  {
    id: 105,
    tripName: 'Parts Pickup',
    vehicle: 'Ford F-150 - JKL654',
    driver: 'Tom Davis',
    completedAt: '2025-08-13 10:30',
    destination: 'Auto Parts Supplier',
    duration: '1h 20m',
    status: 'Completed',
    distance: '34.5 miles',
  },
];

// Mock active trip locations for map
const mockActiveLocations = [
  {
    id: 1,
    vehicleName: 'Ford Transit - ABC123',
    driver: 'John Smith',
    position: [37.7749, -122.4194],
    status: 'In Transit',
    destination: 'Downtown Office',
    progress: 65,
  },
  {
    id: 2,
    vehicleName: 'Toyota Camry - XYZ789',
    driver: 'Sarah Johnson',
    position: [37.7849, -122.4094],
    status: 'At Destination',
    destination: 'Client Site',
    progress: 100,
  },
  {
    id: 3,
    vehicleName: 'Chevrolet Silverado - DEF456',
    driver: 'Mike Wilson',
    position: [37.7649, -122.4294],
    status: 'Loading',
    destination: 'Construction Site',
    progress: 25,
  },
];

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

  // Notification state
  const [notification, setNotification] = useState({
    isVisible: false,
    message: '',
    type: 'info',
  });

  // Tab state
  const [activeTab, setActiveTab] = useState('overview');

  const tabs = [
    { id: 'overview', label: 'Overview' },
    { id: 'active', label: 'Active' },
    { id: 'upcoming', label: 'Upcoming' },
    { id: 'recent', label: 'Recent' },
    { id: 'analytics', label: 'Analytics' },
  ];

  // Helper function to show notifications
  const showNotification = (message, type = 'info') => {
    setNotification({
      isVisible: true,
      message,
      type,
    });
  };

  // Helper function to close notifications
  const closeNotification = () => {
    setNotification(prev => ({
      ...prev,
      isVisible: false,
    }));
  };

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

        // Extract drivers from the nested response structure - response.data.data.drivers
        let driversData = [];

        if (response?.data?.data?.data?.drivers) {
          // Handle nested data structure: response.data.data.data.drivers
          driversData = response.data.data.data.drivers;
        } else if (response?.data?.data?.drivers) {
          // Handle nested data structure: response.data.data.drivers
          driversData = response.data.data.drivers;
        } else if (response?.data?.drivers) {
          // Handle simpler structure: response.data.drivers
          driversData = response.data.drivers;
        } else if (response?.drivers) {
          // Handle direct structure: response.drivers
          driversData = response.drivers;
        } else {
          driversData = [];
        }

        // More permissive filtering to include drivers with different status formats
        const availableDrivers = driversData.filter(driver => {
          // Check if driver exists and has a valid structure
          if (!driver) return false;

          // More inclusive filtering logic - accept available, active, and drivers without status
          const status = (driver.status || '').toLowerCase();
          return (
            status === 'available' ||
            status === 'active' ||
            status === '' || // Include drivers with no status
            !driver.status || // Include drivers where status is not defined
            driver.is_active !== false // Include drivers where is_active is not explicitly false
          );
        });

        console.log('All drivers from API: ', driversData);
        console.log('Available drivers after filtering: ', availableDrivers);
        setDrivers(availableDrivers);
      } catch (error) {
        console.error('Error loading drivers:', error);
        setDrivers([]);
      }
    };

    loadDrivers();
  }, []);

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
        showNotification('Please fill in all required fields', 'error');
        return;
      }

      if (!locationCoords.start || !locationCoords.end) {
        showNotification('Please select valid locations from the dropdown suggestions', 'error');
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
        // Handle both old field names (scheduledStartDate) and new ones (startDate)
        const startDate = enhancedTripData.startDate || enhancedTripData.scheduledStartDate;
        const startTime = enhancedTripData.startTime || enhancedTripData.scheduledStartTime;
        const endDate = enhancedTripData.endDate || enhancedTripData.scheduledEndDate;
        const endTime = enhancedTripData.endTime || enhancedTripData.scheduledEndTime;

        // Ensure proper datetime format (ISO 8601)
        const startDateTime = startDate && startTime ? `${startDate}T${startTime}:00Z` : null;
        const endDateTime = endDate && endTime ? `${endDate}T${endTime}:00Z` : null;

        tripData = {
          name: enhancedTripData.name,
          description: enhancedTripData.description || '',
          scheduled_start_time: startDateTime,
          scheduled_end_time: endDateTime,
          origin: {
            name: enhancedTripData.startLocation,
            location: {
              type: 'Point',
              coordinates: [
                enhancedTripData.coordinates?.start?.lng || locationCoords.start?.lng,
                enhancedTripData.coordinates?.start?.lat || locationCoords.start?.lat,
              ],
              address: enhancedTripData.startLocation,
            },
            order: 1,
          },
          destination: {
            name: enhancedTripData.endLocation,
            location: {
              type: 'Point',
              coordinates: [
                enhancedTripData.coordinates?.end?.lng || locationCoords.end?.lng,
                enhancedTripData.coordinates?.end?.lat || locationCoords.end?.lat,
              ],
              address: enhancedTripData.endLocation,
            },
            order: 2,
          },
          priority: enhancedTripData.priority || 'normal',
          vehicle_id: enhancedTripData.vehicleId,
          driver_assignment: enhancedTripData.driverId,
          // Enhanced route information
          waypoints: enhancedTripData.waypoints || [],
          route_info: enhancedTripData.routeInfo || null,
          driver_note: enhancedTripData.driverNotes || enhancedTripData.driverNote || '',
        };
      } else {
        // Fallback to existing format method
        tripData = formatTripData();
      }

      console.log('Creating trip with data:', tripData);

      // Validate the trip data before sending
      if (!tripData.scheduled_start_time || !tripData.scheduled_end_time) {
        throw new Error('Start and end times are required');
      }

      if (!tripData.origin?.location || !tripData.destination?.location) {
        throw new Error('Start and end locations are required');
      }

      // Validate coordinates
      const startCoords = tripData.origin.location.coordinates;
      const endCoords = tripData.destination.location.coordinates;

      if (
        !startCoords ||
        !Array.isArray(startCoords) ||
        startCoords.length !== 2 ||
        startCoords.some(coord => coord === null || coord === undefined)
      ) {
        throw new Error('Invalid start location coordinates');
      }

      if (
        !endCoords ||
        !Array.isArray(endCoords) ||
        endCoords.length !== 2 ||
        endCoords.some(coord => coord === null || coord === undefined)
      ) {
        throw new Error('Invalid end location coordinates');
      }

      if (!tripData.vehicle_id || !tripData.driver_assignment) {
        throw new Error('Vehicle and driver selection are required');
      }

      const response = await createTrip(tripData);
      console.log('Trip created successfully:', response);

      if (response.data.status === 'success') {
        showNotification('Trip scheduled successfully!', 'success');
      } else {
        showNotification(`Failed to create trip: ${response.data.message}`, 'error');
      }
      handleCloseModal();
    } catch (error) {
      console.error('Error scheduling trip:', error);
      showNotification(`Failed to schedule trip: ${error.message || 'Please try again.'}`, 'error');
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
        {/* Header with Title and Schedule Button */}
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-3xl font-bold animate-fade-in text-foreground">Trip Management</h1>
          <button
            className="bg-primary text-primary-foreground px-4 py-2 rounded-md hover:bg-primary/90 transition animate-fade-in flex items-center gap-2"
            onClick={handleScheduleTrip}
          >
            <Plus size={18} />
            Schedule New Trip
          </button>
        </div>

        {/* Tab Navigation */}
        <div className="mb-6">
          <div className="border-b border-border">
            <nav className="-mb-px flex space-x-8" aria-label="Tabs">
              {tabs.map(tab => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm transition-colors ${
                    activeTab === tab.id
                      ? 'border-primary text-primary'
                      : 'border-transparent text-muted-foreground hover:text-foreground hover:border-muted-foreground'
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </nav>
          </div>
        </div>

        {/* Tab Content */}
        <div className="tab-content">
          {/* Overview Tab */}
          {activeTab === 'overview' && (
            <div className="space-y-6 animate-fade-in">
              {/* Stats Cards */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 animate-fade-in animate-delay-100">
                {/* Available Vehicles Card */}
                <div className="group bg-gradient-to-br from-blue-50 to-blue-100 dark:from-blue-950 dark:to-blue-900 border border-blue-200 dark:border-blue-800 rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-105 p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-blue-600 dark:text-blue-300 mb-2">
                        Available Vehicles
                      </p>
                      <p className="text-3xl font-bold text-blue-900 dark:text-blue-100 transition-colors duration-300">
                        {availableVehicles.length}
                      </p>
                      <div className="flex items-center mt-2">
                        <div className="w-2 h-2 bg-blue-500 rounded-full mr-2 animate-pulse"></div>
                        <p className="text-xs text-blue-600 dark:text-blue-400">Ready for trips</p>
                      </div>
                    </div>
                    <div className="h-14 w-14 bg-blue-500 dark:bg-blue-600 rounded-xl flex items-center justify-center shadow-md group-hover:shadow-lg group-hover:scale-110 transition-all duration-300">
                      <svg
                        className="h-7 w-7 text-white"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2.5}
                          d="M8 7v8a2 2 0 002 2h6M8 7V5a2 2 0 012-2h4.586a1 1 0 01.707.293l4.414 4.414a1 1 0 01.293.707V15a2 2 0 01-2 2h-2M8 7H6a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2v-2"
                        />
                      </svg>
                    </div>
                  </div>
                </div>

                {/* Available Drivers Card */}
                <div className="group bg-gradient-to-br from-green-50 to-green-100 dark:from-green-950 dark:to-green-900 border border-green-200 dark:border-green-800 rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-105 p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-green-600 dark:text-green-300 mb-2">
                        Available Drivers
                      </p>
                      <p className="text-3xl font-bold text-green-900 dark:text-green-100 transition-colors duration-300">
                        {availableDrivers.length}
                      </p>
                      <div className="flex items-center mt-2">
                        <div className="w-2 h-2 bg-green-500 rounded-full mr-2 animate-pulse"></div>
                        <p className="text-xs text-green-600 dark:text-green-400">Ready to drive</p>
                      </div>
                    </div>
                    <div className="h-14 w-14 bg-green-500 dark:bg-green-600 rounded-xl flex items-center justify-center shadow-md group-hover:shadow-lg group-hover:scale-110 transition-all duration-300">
                      <svg
                        className="h-7 w-7 text-white"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2.5}
                          d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
                        />
                      </svg>
                    </div>
                  </div>
                </div>
              </div>

              <div className="animate-fade-in animate-delay-200">
                <SchedulingPanel
                  availableVehicles={availableVehicles.length}
                  availableDrivers={availableDrivers.length}
                  onScheduleClick={handleScheduleTrip}
                />
              </div>
            </div>
          )}

          {/* Active Tab */}
          {activeTab === 'active' && (
            <div className="space-y-6 animate-fade-in">
              <div className="animate-fade-in animate-delay-100">
                <ActiveTripsPanel activeTrips={activeTrips} />
              </div>

              {/* Active Trips Map */}
              <div className="bg-card border border-border rounded-xl shadow-lg overflow-hidden animate-fade-in animate-delay-200">
                <div className="p-4 border-b border-border">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <MapPin className="h-5 w-5 text-primary" />
                      <h3 className="text-lg font-semibold">Active Trip Locations</h3>
                    </div>
                    <div className="text-sm text-muted-foreground">
                      {mockActiveLocations.length} vehicles tracked
                    </div>
                  </div>
                </div>
                <div className="h-96 relative">
                  <MapContainer
                    center={[37.7749, -122.4194]}
                    zoom={12}
                    style={{ height: '100%', width: '100%' }}
                    className="rounded-b-xl"
                    zoomControl={false}
                  >
                    <TileLayer
                      url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                      attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                    />
                    {mockActiveLocations.map(location => (
                      <Marker
                        key={location.id}
                        position={location.position}
                        icon={createVehicleIcon(location.status)}
                      >
                        <Popup>
                          <div className="text-sm">
                            <h4 className="font-semibold">{location.vehicleName}</h4>
                            <p className="text-muted-foreground">Driver: {location.driver}</p>
                            <p className="text-muted-foreground">
                              Going to: {location.destination}
                            </p>
                            <div className="flex items-center gap-2 mt-2">
                              <div
                                className={`w-2 h-2 rounded-full ${
                                  location.status === 'In Transit'
                                    ? 'bg-blue-500'
                                    : location.status === 'At Destination'
                                    ? 'bg-green-500'
                                    : 'bg-orange-500'
                                }`}
                              ></div>
                              <span className="text-xs">{location.status}</span>
                            </div>
                            <div className="mt-1">
                              <div className="flex justify-between text-xs">
                                <span>Progress</span>
                                <span>{location.progress}%</span>
                              </div>
                              <div className="w-full bg-muted rounded-full h-1.5 mt-1">
                                <div
                                  className="bg-primary h-1.5 rounded-full transition-all duration-300"
                                  style={{ width: `${location.progress}%` }}
                                ></div>
                              </div>
                            </div>
                          </div>
                        </Popup>
                      </Marker>
                    ))}
                  </MapContainer>

                  {/* Map Controls Overlay */}
                  <div className="absolute top-4 right-4 flex flex-col gap-2 z-[1000]">
                    <div className="bg-white dark:bg-card border border-border rounded-lg shadow-lg p-2">
                      <div className="flex items-center gap-2 text-sm">
                        <div className="flex items-center gap-1">
                          <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
                          <span className="text-muted-foreground">In Transit</span>
                        </div>
                        <div className="flex items-center gap-1">
                          <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                          <span className="text-muted-foreground">At Destination</span>
                        </div>
                        <div className="flex items-center gap-1">
                          <div className="w-3 h-3 bg-orange-500 rounded-full"></div>
                          <span className="text-muted-foreground">Loading</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Upcoming Tab */}
          {activeTab === 'upcoming' && (
            <div className="space-y-6 animate-fade-in">
              {/* Summary Cards */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 animate-fade-in animate-delay-100">
                <div className="bg-gradient-to-br from-blue-50 to-blue-100 dark:from-blue-950 dark:to-blue-900 border border-blue-200 dark:border-blue-800 rounded-xl shadow-lg p-4">
                  <div className="flex items-center gap-3">
                    <div className="h-10 w-10 bg-blue-500 rounded-lg flex items-center justify-center">
                      <Calendar className="h-5 w-5 text-white" />
                    </div>
                    <div>
                      <p className="text-sm font-medium text-blue-600 dark:text-blue-300">
                        Total Scheduled
                      </p>
                      <p className="text-2xl font-bold text-blue-900 dark:text-blue-100">
                        {mockUpcomingTrips.length}
                      </p>
                    </div>
                  </div>
                </div>
                <div className="bg-gradient-to-br from-red-50 to-red-100 dark:from-red-950 dark:to-red-900 border border-red-200 dark:border-red-800 rounded-xl shadow-lg p-4">
                  <div className="flex items-center gap-3">
                    <div className="h-10 w-10 bg-red-500 rounded-lg flex items-center justify-center">
                      <Clock className="h-5 w-5 text-white" />
                    </div>
                    <div>
                      <p className="text-sm font-medium text-red-600 dark:text-red-300">
                        High Priority
                      </p>
                      <p className="text-2xl font-bold text-red-900 dark:text-red-100">
                        {mockUpcomingTrips.filter(trip => trip.priority === 'High').length}
                      </p>
                    </div>
                  </div>
                </div>
                <div className="bg-gradient-to-br from-orange-50 to-orange-100 dark:from-orange-950 dark:to-orange-900 border border-orange-200 dark:border-orange-800 rounded-xl shadow-lg p-4">
                  <div className="flex items-center gap-3">
                    <div className="h-10 w-10 bg-orange-500 rounded-lg flex items-center justify-center">
                      <User className="h-5 w-5 text-white" />
                    </div>
                    <div>
                      <p className="text-sm font-medium text-orange-600 dark:text-orange-300">
                        Pending Approval
                      </p>
                      <p className="text-2xl font-bold text-orange-900 dark:text-orange-100">
                        {
                          mockUpcomingTrips.filter(trip => trip.status === 'Pending Approval')
                            .length
                        }
                      </p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Trips Table */}
              <div className="bg-card border border-border rounded-xl shadow-lg overflow-hidden animate-fade-in animate-delay-200">
                <div className="p-4 border-b border-border">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Calendar className="h-5 w-5 text-primary" />
                      <h3 className="text-lg font-semibold">Upcoming Trips</h3>
                    </div>
                    <div className="text-sm text-muted-foreground">
                      {mockUpcomingTrips.length} trips scheduled
                    </div>
                  </div>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead className="bg-muted/50">
                      <tr>
                        <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                          Trip Details
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                          Vehicle & Driver
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                          Schedule
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                          Destination
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                          Priority
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                          Status
                        </th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-border">
                      {mockUpcomingTrips.map(trip => (
                        <tr key={trip.id} className="hover:bg-muted/30 transition-colors">
                          <td className="px-4 py-4">
                            <div className="flex items-center gap-2">
                              <div className="w-8 h-8 bg-blue-100 dark:bg-blue-900 rounded-full flex items-center justify-center">
                                <MapPin className="h-4 w-4 text-blue-600 dark:text-blue-300" />
                              </div>
                              <div>
                                <div className="font-medium text-foreground">{trip.tripName}</div>
                                <div className="text-sm text-muted-foreground">ID: #{trip.id}</div>
                              </div>
                            </div>
                          </td>
                          <td className="px-4 py-4">
                            <div>
                              <div className="font-medium text-foreground">{trip.vehicle}</div>
                              <div className="text-sm text-muted-foreground flex items-center gap-1">
                                <User className="h-3 w-3" />
                                {trip.driver}
                              </div>
                            </div>
                          </td>
                          <td className="px-4 py-4">
                            <div className="flex items-center gap-1 text-sm">
                              <Clock className="h-3 w-3 text-muted-foreground" />
                              <span>{trip.scheduledStart}</span>
                            </div>
                          </td>
                          <td className="px-4 py-4">
                            <span className="text-sm">{trip.destination}</span>
                          </td>
                          <td className="px-4 py-4">
                            <span
                              className={`px-2 py-1 text-xs font-medium rounded-full ${
                                trip.priority === 'High'
                                  ? 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300'
                                  : trip.priority === 'Medium'
                                  ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300'
                                  : 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300'
                              }`}
                            >
                              {trip.priority}
                            </span>
                          </td>
                          <td className="px-4 py-4">
                            <span
                              className={`px-2 py-1 text-xs font-medium rounded-full ${
                                trip.status === 'Scheduled'
                                  ? 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300'
                                  : 'bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-300'
                              }`}
                            >
                              {trip.status}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}

          {/* Recent Tab */}
          {activeTab === 'recent' && (
            <div className="space-y-6 animate-fade-in">
              {/* Summary Cards */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4 animate-fade-in animate-delay-100">
                <div className="bg-gradient-to-br from-green-50 to-green-100 dark:from-green-950 dark:to-green-900 border border-green-200 dark:border-green-800 rounded-xl shadow-lg p-4">
                  <div className="flex items-center gap-3">
                    <div className="h-10 w-10 bg-green-500 rounded-lg flex items-center justify-center">
                      <Clock className="h-5 w-5 text-white" />
                    </div>
                    <div>
                      <p className="text-sm font-medium text-green-600 dark:text-green-300">
                        Completed
                      </p>
                      <p className="text-2xl font-bold text-green-900 dark:text-green-100">
                        {mockRecentTrips.length}
                      </p>
                    </div>
                  </div>
                </div>
                <div className="bg-gradient-to-br from-purple-50 to-purple-100 dark:from-purple-950 dark:to-purple-900 border border-purple-200 dark:border-purple-800 rounded-xl shadow-lg p-4">
                  <div className="flex items-center gap-3">
                    <div className="h-10 w-10 bg-purple-500 rounded-lg flex items-center justify-center">
                      <MapPin className="h-5 w-5 text-white" />
                    </div>
                    <div>
                      <p className="text-sm font-medium text-purple-600 dark:text-purple-300">
                        Total Distance
                      </p>
                      <p className="text-2xl font-bold text-purple-900 dark:text-purple-100">
                        {mockRecentTrips
                          .reduce((total, trip) => total + parseFloat(trip.distance), 0)
                          .toFixed(1)}
                        mi
                      </p>
                    </div>
                  </div>
                </div>
                <div className="bg-gradient-to-br from-indigo-50 to-indigo-100 dark:from-indigo-950 dark:to-indigo-900 border border-indigo-200 dark:border-indigo-800 rounded-xl shadow-lg p-4">
                  <div className="flex items-center gap-3">
                    <div className="h-10 w-10 bg-indigo-500 rounded-lg flex items-center justify-center">
                      <User className="h-5 w-5 text-white" />
                    </div>
                    <div>
                      <p className="text-sm font-medium text-indigo-600 dark:text-indigo-300">
                        Active Drivers
                      </p>
                      <p className="text-2xl font-bold text-indigo-900 dark:text-indigo-100">
                        {new Set(mockRecentTrips.map(trip => trip.driver)).size}
                      </p>
                    </div>
                  </div>
                </div>
                <div className="bg-gradient-to-br from-teal-50 to-teal-100 dark:from-teal-950 dark:to-teal-900 border border-teal-200 dark:border-teal-800 rounded-xl shadow-lg p-4">
                  <div className="flex items-center gap-3">
                    <div className="h-10 w-10 bg-teal-500 rounded-lg flex items-center justify-center">
                      <Clock className="h-5 w-5 text-white" />
                    </div>
                    <div>
                      <p className="text-sm font-medium text-teal-600 dark:text-teal-300">
                        Avg Duration
                      </p>
                      <p className="text-2xl font-bold text-teal-900 dark:text-teal-100">2h 3m</p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Trips Table */}
              <div className="bg-card border border-border rounded-xl shadow-lg overflow-hidden animate-fade-in animate-delay-200">
                <div className="p-4 border-b border-border">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Clock className="h-5 w-5 text-primary" />
                      <h3 className="text-lg font-semibold">Recent Trips</h3>
                    </div>
                    <div className="text-sm text-muted-foreground">
                      {mockRecentTrips.length} completed trips
                    </div>
                  </div>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead className="bg-muted/50">
                      <tr>
                        <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                          Trip Details
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                          Vehicle & Driver
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                          Completed
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                          Destination
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                          Duration
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                          Distance
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                          Status
                        </th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-border">
                      {mockRecentTrips.map(trip => (
                        <tr key={trip.id} className="hover:bg-muted/30 transition-colors">
                          <td className="px-4 py-4">
                            <div className="flex items-center gap-2">
                              <div className="w-8 h-8 bg-green-100 dark:bg-green-900 rounded-full flex items-center justify-center">
                                <MapPin className="h-4 w-4 text-green-600 dark:text-green-300" />
                              </div>
                              <div>
                                <div className="font-medium text-foreground">{trip.tripName}</div>
                                <div className="text-sm text-muted-foreground">ID: #{trip.id}</div>
                              </div>
                            </div>
                          </td>
                          <td className="px-4 py-4">
                            <div>
                              <div className="font-medium text-foreground">{trip.vehicle}</div>
                              <div className="text-sm text-muted-foreground flex items-center gap-1">
                                <User className="h-3 w-3" />
                                {trip.driver}
                              </div>
                            </div>
                          </td>
                          <td className="px-4 py-4">
                            <div className="flex items-center gap-1 text-sm">
                              <Clock className="h-3 w-3 text-muted-foreground" />
                              <span>{trip.completedAt}</span>
                            </div>
                          </td>
                          <td className="px-4 py-4">
                            <span className="text-sm">{trip.destination}</span>
                          </td>
                          <td className="px-4 py-4">
                            <span className="text-sm font-medium">{trip.duration}</span>
                          </td>
                          <td className="px-4 py-4">
                            <span className="text-sm text-muted-foreground">{trip.distance}</span>
                          </td>
                          <td className="px-4 py-4">
                            <span className="px-2 py-1 text-xs font-medium rounded-full bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300">
                              {trip.status}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Keep the existing TripsHistory component as well */}
              <div className="animate-fade-in animate-delay-300">
                <TripsHistory trips={[]} />
              </div>
            </div>
          )}

          {/* Analytics Tab */}
          {activeTab === 'analytics' && (
            <div className="space-y-6 animate-fade-in">
              <div className="animate-fade-in animate-delay-100">
                <TripsAnalytics
                  driverData={driverAnalytics}
                  vehicleData={vehicleAnalytics}
                  timeframe={analyticsTimeframe}
                  onTimeframeChange={setAnalyticsTimeframe}
                />
              </div>
            </div>
          )}
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

        {/* Notification Component */}
        <Notification
          message={notification.message}
          type={notification.type}
          isVisible={notification.isVisible}
          onClose={closeNotification}
        />
      </div>
    </div>
  );
};

export default Trips;
