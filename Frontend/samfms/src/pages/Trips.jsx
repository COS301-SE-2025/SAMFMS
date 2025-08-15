import React, { useState, useEffect, useCallback } from 'react';
import { Plus } from 'lucide-react';
import ActiveTripsPanel from '../components/trips/ActiveTripsPanel';
import SchedulingPanel from '../components/trips/SchedulingPanel';
import TripsAnalytics from '../components/trips/TripsAnalytics';
import TripsHistory from '../components/trips/TripsHistory';
import TripSchedulingModal from '../components/trips/TripSchedulingModal';
import Notification from '../components/common/Notification';
import OverviewStatsCards from '../components/trips/OverviewStatsCards';
import ActiveTripsMap from '../components/trips/ActiveTripsMap';
import UpcomingTripsStats from '../components/trips/UpcomingTripsStats';
import UpcomingTripsTable from '../components/trips/UpcomingTripsTable';
import RecentTripsStats from '../components/trips/RecentTripsStats';
import RecentTripsTable from '../components/trips/RecentTripsTable';
import {
  createTrip,
  getActiveTrips,
  getDriverAnalytics,
  getVehicleAnalytics,
  listTrips,
  getAllRecentTrips,
  getTripHistoryStats,
} from '../backend/api/trips';
import { getVehicles } from '../backend/api/vehicles';
import { getAllDrivers } from '../backend/api/drivers';
import { mockActiveLocations } from '../data/mockTripsData';

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

  // Trip data state
  const [upcomingTrips, setUpcomingTrips] = useState([]);
  const [recentTrips, setRecentTrips] = useState([]);
  const [upcomingTripsLoading, setUpcomingTripsLoading] = useState(false);
  const [recentTripsLoading, setRecentTripsLoading] = useState(false);

  // Trip history statistics state
  const [tripHistoryStats, setTripHistoryStats] = useState({
    total_trips: 0,
    total_duration_hours: 0,
    total_distance_km: 0,
    average_duration_hours: 0,
    average_distance_km: 0,
    time_period: 'All time',
  });
  const [historyStatsLoading, setHistoryStatsLoading] = useState(false);

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
  const showNotification = useCallback((message, type = 'info') => {
    setNotification({
      isVisible: true,
      message,
      type,
    });
  }, []);

  // Helper function to close notifications
  const closeNotification = () => {
    setNotification(prev => ({
      ...prev,
      isVisible: false,
    }));
  };

  // Helper function to fetch all upcoming trips
  const fetchUpcomingTrips = useCallback(async () => {
    try {
      setUpcomingTripsLoading(true);
      const response = await listTrips();
      console.log('Upcoming trips response:', response);

      // Extract trips from the response structure - based on actual API response
      let trips = [];
      if (response?.data?.data?.data && Array.isArray(response.data.data.data)) {
        trips = response.data.data.data;
      } else if (response?.data?.data && Array.isArray(response.data.data)) {
        trips = response.data.data;
      } else if (Array.isArray(response?.data)) {
        trips = response.data;
      }

      // Filter for scheduled/upcoming trips only
      const upcomingTrips = trips.filter(trip => {
        try {
          return (
            trip.status === 'scheduled' &&
            trip.scheduled_start_time &&
            new Date(trip.scheduled_start_time) > new Date()
          );
        } catch (error) {
          console.warn('Invalid date format for trip:', trip.id);
          return false;
        }
      });

      // Transform API data to match component expectations
      const transformedTrips = upcomingTrips.map(trip => {
        let scheduledStart = 'Unknown';
        try {
          scheduledStart = new Date(trip.scheduled_start_time).toLocaleString();
        } catch (error) {
          console.warn('Invalid date format for trip scheduled start:', trip.id);
        }

        return {
          id: trip.id,
          tripName: trip.name || 'Unnamed Trip',
          vehicle: trip.vehicle_id || 'Unknown Vehicle',
          driver: trip.driver_assignment || 'Unassigned',
          scheduledStart,
          destination: trip.destination?.name || 'Unknown Destination',
          priority:
            trip.priority === 'normal'
              ? 'Medium'
              : trip.priority === 'high'
              ? 'High'
              : trip.priority === 'urgent'
              ? 'High'
              : 'Low',
          status: 'Scheduled',
        };
      });

      console.log('Transformed upcoming trips:', transformedTrips);
      setUpcomingTrips(transformedTrips);
    } catch (error) {
      console.error('Error fetching upcoming trips:', error);
      // Show user-friendly error message
      showNotification('Failed to load upcoming trips. Please try again.', 'error');
      setUpcomingTrips([]);
    } finally {
      setUpcomingTripsLoading(false);
    }
  }, [showNotification]);

  // Helper function to fetch all recent trips using the new dedicated endpoint
  const fetchRecentTrips = useCallback(async () => {
    try {
      setRecentTripsLoading(true);

      // Use the new dedicated endpoint for recent trips
      const response = await getAllRecentTrips(10, 30);
      console.log('Recent trips response:', response);

      // Extract trips from the response structure
      let trips = [];
      if (response?.data?.trips) {
        trips = response.data.trips;
      } else if (response?.data?.data) {
        trips = Array.isArray(response.data.data) ? response.data.data : [];
      } else if (Array.isArray(response?.data)) {
        trips = response.data;
      }

      // Transform API data to match component expectations
      const transformedTrips = trips.map(trip => {
        let completedAt = 'Unknown';
        let duration = 'Unknown';

        try {
          completedAt = new Date(trip.actualEndTime || trip.actual_end_time).toLocaleString();
        } catch (error) {
          console.warn('Invalid date format for trip completion:', trip.id);
        }

        try {
          if (
            (trip.actualStartTime || trip.actual_start_time) &&
            (trip.actualEndTime || trip.actual_end_time)
          ) {
            const startTime = new Date(trip.actualStartTime || trip.actual_start_time);
            const endTime = new Date(trip.actualEndTime || trip.actual_end_time);
            const durationMs = endTime - startTime;
            const durationMinutes = Math.round(durationMs / (1000 * 60));
            const hours = Math.floor(durationMinutes / 60);
            const minutes = durationMinutes % 60;
            duration = hours > 0 ? `${hours}h ${minutes}m` : `${minutes}m`;
          }
        } catch (error) {
          console.warn('Could not calculate duration for trip:', trip.id);
        }

        return {
          id: trip.id,
          tripName: trip.name || 'Unnamed Trip',
          vehicle: trip.vehicleId || trip.vehicle_id || 'Unknown Vehicle',
          driver: trip.driverAssignment || trip.driver_assignment || 'Unknown Driver',
          completedAt,
          destination: trip.destination?.name || 'Unknown Destination',
          duration,
          status: 'Completed',
          distance:
            trip.estimatedDistance || trip.estimated_distance
              ? ((trip.estimatedDistance || trip.estimated_distance) / 1000).toFixed(1)
              : '0',
        };
      });

      console.log('Transformed recent trips:', transformedTrips);
      setRecentTrips(transformedTrips);
    } catch (error) {
      console.error('Error fetching recent trips:', error);
      // Show user-friendly error message
      showNotification('Failed to load recent trips. Please try again.', 'error');
      setRecentTrips([]);
    } finally {
      setRecentTripsLoading(false);
    }
  }, [showNotification]);

  // Helper function to fetch trip history statistics
  const fetchTripHistoryStats = useCallback(
    async (days = null) => {
      try {
        setHistoryStatsLoading(true);
        console.log('Fetching trip history stats for days:', days);

        const response = await getTripHistoryStats(days);
        console.log('Trip history stats response:', response);

        if (response?.data) {
          setTripHistoryStats(response.data);
        }
      } catch (error) {
        console.error('Error fetching trip history stats:', error);
        showNotification('Failed to load trip statistics. Please try again.', 'error');
        // Keep existing stats or use defaults
      } finally {
        setHistoryStatsLoading(false);
      }
    },
    [showNotification]
  );

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

  // Fetch upcoming trips
  useEffect(() => {
    fetchUpcomingTrips();
  }, [fetchUpcomingTrips]);

  // Fetch recent trips
  useEffect(() => {
    fetchRecentTrips();
  }, [fetchRecentTrips]);

  // Refresh trip data when switching tabs
  useEffect(() => {
    if (activeTab === 'upcoming') {
      fetchUpcomingTrips();
    } else if (activeTab === 'recent') {
      fetchRecentTrips();
      fetchTripHistoryStats(); // Also fetch trip statistics for the recent tab
    }
  }, [activeTab, fetchUpcomingTrips, fetchRecentTrips, fetchTripHistoryStats]);

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
              <OverviewStatsCards
                availableVehicles={availableVehicles.length}
                availableDrivers={availableDrivers.length}
              />

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
              <div className="animate-fade-in animate-delay-200">
                <ActiveTripsMap activeLocations={mockActiveLocations} />
              </div>
            </div>
          )}

          {/* Upcoming Tab */}
          {activeTab === 'upcoming' && (
            <div className="space-y-6 animate-fade-in">
              {/* Summary Cards */}
              <div className="animate-fade-in animate-delay-100">
                {upcomingTripsLoading ? (
                  <div className="flex justify-center items-center p-8">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                    <span className="ml-2">Loading upcoming trips...</span>
                  </div>
                ) : (
                  <UpcomingTripsStats upcomingTrips={upcomingTrips} />
                )}
              </div>

              {/* Trips Table */}
              <div className="animate-fade-in animate-delay-200">
                {upcomingTripsLoading ? (
                  <div className="flex justify-center items-center p-8">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                    <span className="ml-2">Loading trips table...</span>
                  </div>
                ) : (
                  <UpcomingTripsTable upcomingTrips={upcomingTrips} />
                )}
              </div>
            </div>
          )}

          {/* Recent Tab */}
          {activeTab === 'recent' && (
            <div className="space-y-6 animate-fade-in">
              {/* Summary Cards */}
              <div className="animate-fade-in animate-delay-100">
                {recentTripsLoading ? (
                  <div className="flex justify-center items-center p-8">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                    <span className="ml-2">Loading recent trips...</span>
                  </div>
                ) : (
                  <RecentTripsStats
                    recentTrips={recentTrips}
                    tripHistoryStats={tripHistoryStats}
                    loading={historyStatsLoading}
                  />
                )}
              </div>

              {/* Trips Table */}
              <div className="animate-fade-in animate-delay-200">
                {recentTripsLoading ? (
                  <div className="flex justify-center items-center p-8">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                    <span className="ml-2">Loading trips table...</span>
                  </div>
                ) : (
                  <RecentTripsTable recentTrips={recentTrips} />
                )}
              </div>

              {/* Keep the existing TripsHistory component as well */}
              <div className="animate-fade-in animate-delay-300">
                <TripsHistory trips={recentTrips} />
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
