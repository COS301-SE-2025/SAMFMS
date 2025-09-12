import React, {useState, useEffect, useCallback} from 'react';
import {
  X,
  MapPin,
  Clock,
  User,
  Car,
  Calendar,
  Route,
  FileText,
  CheckCircle,
  ChevronRight,
  ChevronLeft,
  ChevronUp,
  Flag,
} from 'lucide-react';
import TripPlanningMap from './TripPlanningMap';
import LocationAutocomplete from './LocationAutocomplete';
import SearchableDropdown from '../ui/SearchableDropdown';
import { getAvailableDrivers, getAvailableVehicles } from '../../backend/api/trips';

const TripSchedulingModal = ({
  showModal,
  onClose,
  onSubmit,
  tripForm,
  onFormChange,
  vehicles,
  drivers,
  isSubmitting,
  availableVehicles,
}) => {
  // Step management
  const [currentStep, setCurrentStep] = useState(1);
  const totalSteps = 3;

  // Map state
  const [mapLocations, setMapLocations] = useState({
    start: null,
    end: null,
    waypoints: [],
  });
  const [routeInfo, setRouteInfo] = useState(null);

  // Optional field toggles
  const [showDescription, setShowDescription] = useState(false);
  const [showDriverNotes, setShowDriverNotes] = useState(false);

  // Options for step 2/3 Driver and Vehicle dropdowns
  const [vehicleOptions, setVehicleOptions] = useState([]);
  const [driverOptions, setDriverOptions] = useState([]);
  const [loadingDrivers, setLoadingDrivers] = useState(false);
  const [loadingVehicles, setLoadingVehicles] = useState(false);

  // Step navigation functions
  const nextStep = useCallback(() => {
    if (currentStep < totalSteps) {
      setCurrentStep(currentStep + 1);
    }
  }, [currentStep, totalSteps]);

  const prevStep = useCallback(() => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
    }
  }, [currentStep]);

  // Form validation for each step
  const isStepValid = useCallback(
    step => {
      switch (step) {
        case 1:
          return tripForm.name && tripForm.priority && tripForm.startDate && tripForm.startTime && tripForm.endDate && tripForm.endTime;
        case 2:
          return (
            tripForm.vehicleId &&
            tripForm.driverId
          );
        case 3:
          return tripForm.startLocation && tripForm.endLocation;
        default:
          return false;
      }
    },
    [tripForm]
  );

  // For the change in Vehicle in step 2/3 Vehicle dropdown
  useEffect(() => {
    if (availableVehicles || vehicles) {
      const formattedVehicles = (availableVehicles || vehicles).map(vehicle => ({
        value: vehicle._id || vehicle.id,
        label: `${vehicle.make} ${vehicle.model} - ${vehicle.license_plate || vehicle.licensePlate || vehicle.registration}`
      }));
      setVehicleOptions(formattedVehicles);
    }
  }, [availableVehicles, vehicles]);

  // Function to fetch available vehicles based on time range
  const fetchAvailableVehicles = useCallback(async () => {
    if (!tripForm.startDate || !tripForm.startTime || !tripForm.endDate || !tripForm.endTime) {
      return;
    }

    const startDateTime = `${tripForm.startDate}T${tripForm.startTime}:00`;
    const endDateTime = `${tripForm.endDate}T${tripForm.endTime}:00`;

    console.log('Fetching available vehicles for timeframe:', { startDateTime, endDateTime });

    setLoadingVehicles(true);
    try {
      const response = await getAvailableVehicles(startDateTime, endDateTime);
      console.log('Raw vehicle API response:', response);
      
      // Handle the nested response structure: response.data.data.vehicles
      let availableVehiclesList = [];
      if (response && response.data && response.data.data && response.data.data.vehicles) {
        availableVehiclesList = response.data.data.vehicles;
      } else if (response && response.data && response.data.vehicles) {
        availableVehiclesList = response.data.vehicles;
      }
      
      if (availableVehiclesList && availableVehiclesList.length > 0) {
        // Format available vehicles for the dropdown
        const formattedAvailableVehicles = availableVehiclesList.map(vehicle => ({
          value: vehicle._id,
          label: `${vehicle.make} ${vehicle.model} - ${vehicle.license_plate || vehicle.licensePlate || vehicle.registration_number}`
        }));
        
        setVehicleOptions(formattedAvailableVehicles);
        console.log('Updated vehicle options with available vehicles:', formattedAvailableVehicles);
        
        // Clear selected vehicle if it's no longer available
        if (tripForm.vehicleId && !availableVehiclesList.find(v => v._id === tripForm.vehicleId)) {
          onFormChange('vehicleId', '');
        }
      } else {
        console.warn('No vehicles data in response:', response);
        setVehicleOptions([]);
      }
    } catch (error) {
      console.error('Error fetching available vehicles:', error);
      // Fallback to all vehicles if API fails
      if (vehicles) {
        const formattedVehicles = vehicles.map(vehicle => ({
          value: vehicle._id || vehicle.id,
          label: `${vehicle.make} ${vehicle.model} - ${vehicle.license_plate || vehicle.licensePlate || vehicle.registration}`
        }));
        setVehicleOptions(formattedVehicles);
      }
    } finally {
      setLoadingVehicles(false);
    }
  }, [tripForm.startDate, tripForm.startTime, tripForm.endDate, tripForm.endTime, tripForm.vehicleId, vehicles, onFormChange]);

  // For the change in Driver in step 2/3 Driver dropdown
  useEffect(() => {
    if (drivers) {
      const formattedDrivers = drivers.map(driver => ({
        value: driver.employee_id,
        label: `${driver.first_name} ${driver.last_name || ''} ${driver.employee_id ? `(${driver.employee_id})` : ''}`
      }));
      setDriverOptions(formattedDrivers);
    }
  }, [drivers]);

  // Function to fetch available drivers based on time range
  const fetchAvailableDrivers = useCallback(async () => {
    if (!tripForm.startDate || !tripForm.startTime || !tripForm.endDate || !tripForm.endTime) {
      return;
    }

    const startDateTime = `${tripForm.startDate}T${tripForm.startTime}:00`;
    const endDateTime = `${tripForm.endDate}T${tripForm.endTime}:00`;

    console.log('Fetching available drivers for timeframe:', { startDateTime, endDateTime });

    setLoadingDrivers(true);
    try {
      const response = await getAvailableDrivers(startDateTime, endDateTime);
      console.log('Raw driver API response:', response);
      
      // Handle the nested response structure: response.data.data.available_drivers
      let availableDriversList = [];
      if (response && response.data && response.data.data && response.data.data.available_drivers) {
        availableDriversList = response.data.data.available_drivers;
      } else if (response && response.data && response.data.available_drivers) {
        availableDriversList = response.data.available_drivers;
      }
      
      if (availableDriversList && availableDriversList.length > 0) {
        // Format available drivers for the dropdown
        const formattedAvailableDrivers = availableDriversList.map(driver => ({
          value: driver.employee_id,
          label: `${driver.first_name} ${driver.last_name || ''} ${driver.employee_id ? `(${driver.employee_id})` : ''}`
        }));
        
        setDriverOptions(formattedAvailableDrivers);
        console.log('Updated driver options with available drivers:', formattedAvailableDrivers);
        
        // Clear selected driver if they're no longer available
        if (tripForm.driverId && !availableDriversList.find(d => d.employee_id === tripForm.driverId)) {
          onFormChange('driverId', '');
        }
      } else {
        console.warn('No drivers data in response:', response);
        setDriverOptions([]);
      }
    } catch (error) {
      console.error('Error fetching available drivers:', error);
      // Fallback to all drivers if API fails
      if (drivers) {
        const formattedDrivers = drivers.map(driver => ({
          value: driver.employee_id,
          label: `${driver.first_name} ${driver.last_name || ''} ${driver.employee_id ? `(${driver.employee_id})` : ''}`
        }));
        setDriverOptions(formattedDrivers);
      }
    } finally {
      setLoadingDrivers(false);
    }
  }, [tripForm.startDate, tripForm.startTime, tripForm.endDate, tripForm.endTime, tripForm.driverId, drivers, onFormChange]);

  // Fetch available drivers when date/time changes and we have complete timeframe
  useEffect(() => {
    const timeoutId = setTimeout(() => {
      fetchAvailableDrivers();
      fetchAvailableVehicles();
    }, 500); // Debounce the API call

    return () => clearTimeout(timeoutId);
  }, [fetchAvailableDrivers, fetchAvailableVehicles]);

  // Initialize default date/time values when step 1 is opened
  useEffect(() => {
    if (currentStep === 1 && (!tripForm.startDate || !tripForm.startTime)) {
      const now = new Date();
      const currentDate = now.toISOString().split('T')[0]; // YYYY-MM-DD format
      const currentTime = now.toTimeString().slice(0, 5); // HH:MM format

      // Set default values if not already set
      if (!tripForm.startDate) {
        onFormChange('startDate', currentDate);
      }
      if (!tripForm.startTime) {
        onFormChange('startTime', currentTime);
      }
      if (!tripForm.endDate) {
        onFormChange('endDate', currentDate);
      }
      if (!tripForm.endTime) {
        // Set end time to 1 hour after start time by default
        const endTime = new Date();
        endTime.setHours(endTime.getHours() + 1);
        const endTimeString = endTime.toTimeString().slice(0, 5);
        onFormChange('endTime', endTimeString);
      }
    }
  }, [currentStep, tripForm.startDate, tripForm.startTime, tripForm.endDate, tripForm.endTime, onFormChange]);

  // Handle start date change and ensure end date is not less than start date
  const handleStartDateChange = useCallback((value) => {
    onFormChange('startDate', value);

    // If end date is set and is less than new start date, update end date
    if (tripForm.endDate && value > tripForm.endDate) {
      onFormChange('endDate', value);
    }
  }, [onFormChange, tripForm.endDate]);

  // Handle start time change and ensure end time is valid when dates are same
  const handleStartTimeChange = useCallback((value) => {
    onFormChange('startTime', value);

    // If start and end dates are the same and end time is less than start time, update end time
    if (tripForm.startDate === tripForm.endDate && tripForm.endTime && value > tripForm.endTime) {
      onFormChange('endTime', value);
    }
  }, [onFormChange, tripForm.startDate, tripForm.endDate, tripForm.endTime]);

  // Handle end date change and ensure it's not less than start date
  const handleEndDateChange = useCallback((value) => {
    // Don't allow end date to be less than start date
    if (tripForm.startDate && value < tripForm.startDate) {
      return; // Prevent the change
    }
    onFormChange('endDate', value);
  }, [onFormChange, tripForm.startDate]);

  // Handle end time change and ensure it's valid when dates are same
  const handleEndTimeChange = useCallback((value) => {
    // If dates are the same, don't allow end time to be less than start time
    if (tripForm.startDate === tripForm.endDate && tripForm.startTime && value < tripForm.startTime) {
      return; // Prevent the change
    }
    onFormChange('endTime', value);
  }, [onFormChange, tripForm.startDate, tripForm.endDate, tripForm.startTime]);

  // Handle keyboard navigation
  const handleKeyDown = useCallback(
    e => {
      if (e.key === 'Enter' && !isSubmitting) {
        e.preventDefault();

        if (currentStep < totalSteps && isStepValid(currentStep)) {
          nextStep();
        } else if (currentStep === totalSteps && isStepValid(currentStep)) {
          // Submit the form
          const enhancedTripData = {
            ...tripForm,
            routeInfo,
            waypoints: mapLocations.waypoints,
            coordinates: {
              start: mapLocations.start,
              end: mapLocations.end,
            },
          };
          onSubmit(enhancedTripData);
        }
      }
    },
    [
      currentStep,
      isSubmitting,
      totalSteps,
      tripForm,
      routeInfo,
      mapLocations,
      onSubmit,
      nextStep,
      isStepValid,
    ]
  );

  // Add keyboard event listener
  useEffect(() => {
    if (showModal) {
      document.addEventListener('keydown', handleKeyDown);
      return () => {
        document.removeEventListener('keydown', handleKeyDown);
      };
    }
  }, [showModal, handleKeyDown]);

  // Handle location changes from autocomplete
  const handleStartLocationChange = (location, coordinates) => {
    console.log('Start location changed:', {location, coordinates});
    onFormChange('startLocation', location);
    if (coordinates) {
      const newMapLocations = {
        ...mapLocations,
        start: {lat: coordinates.lat, lng: coordinates.lng},
      };
      console.log('Updated map locations (start):', newMapLocations);
      setMapLocations(newMapLocations);
    }
  };

  const handleEndLocationChange = (location, coordinates) => {
    console.log('End location changed:', {location, coordinates});
    onFormChange('endLocation', location);
    if (coordinates) {
      const newMapLocations = {
        ...mapLocations,
        end: {lat: coordinates.lat, lng: coordinates.lng},
      };
      console.log('Updated map locations (end):', newMapLocations);
      setMapLocations(newMapLocations);
    }
  };

  // Handle map location selection
  const handleMapStartLocationChange = coords => {
    const newMapLocations = {...mapLocations, start: coords};
    setMapLocations(newMapLocations);
    onFormChange('startLocation', `${coords.lat.toFixed(6)}, ${coords.lng.toFixed(6)}`);
  };

  const handleMapEndLocationChange = coords => {
    const newMapLocations = {...mapLocations, end: coords};
    setMapLocations(newMapLocations);
    onFormChange('endLocation', `${coords.lat.toFixed(6)}, ${coords.lng.toFixed(6)}`);
  };

  const handleWaypointAdd = coords => {
    const newMapLocations = {
      ...mapLocations,
      waypoints: [...mapLocations.waypoints, coords],
    };
    setMapLocations(newMapLocations);
  };

  const handleWaypointRemove = index => {
    const newMapLocations = {
      ...mapLocations,
      waypoints: mapLocations.waypoints.filter((_, i) => i !== index),
    };
    setMapLocations(newMapLocations);
  };

  const handleRouteCalculated = route => {
    console.log('Route calculated:', route);
    setRouteInfo(route);
  };

  // Enhanced form submission with route data including polyline
  const handleSubmit = e => {
    e.preventDefault();
    const enhancedTripData = {
      ...tripForm,
      routeInfo,
      polyline: routeInfo?.polyline || null, // Include raw polyline for backend
      decodedPolyline: routeInfo?.coordinates || null, // Include decoded coordinates
      waypoints: mapLocations.waypoints,
      coordinates: {
        start: mapLocations.start,
        end: mapLocations.end,
      },
    };
    onSubmit(enhancedTripData);
  };

  // Reset when modal closes
  useEffect(() => {
    if (!showModal) {
      setCurrentStep(1);
      setMapLocations({start: null, end: null, waypoints: []});
      setRouteInfo(null);
      setShowDescription(false);
      setShowDriverNotes(false);
    }
  }, [showModal]);

  // Debug logging for prop values
  useEffect(() => {
    console.log('TripSchedulingModal props received:');
    console.log('availableVehicles:', availableVehicles);
    console.log('vehicles:', vehicles);
    console.log('drivers:', drivers);
  }, [availableVehicles, vehicles, drivers]);

  // Debug logging for vehicles and drivers
  useEffect(() => {
    console.log('TripSchedulingModal - Received props:');
    console.log('- vehicles:', vehicles);
    console.log('- drivers:', drivers);
    console.log('- availableVehicles:', availableVehicles);
  }, [vehicles, drivers, availableVehicles]);

  // Debug logging for props
  useEffect(() => {
    console.log('TripSchedulingModal props:', {
      availableVehicles: availableVehicles?.length || 0,
      vehicles: vehicles?.length || 0,
      drivers: drivers?.length || 0,
      availableVehiclesData: availableVehicles,
      driversData: drivers,
    });
  }, [availableVehicles, vehicles, drivers]);

  if (!showModal) return null;

  const stepTitles = [
    {title: 'Trip Details & Schedule', subtitle: 'Name, priority, and timing', icon: FileText},
    {title: 'Vehicle & Driver', subtitle: 'Assign vehicle and available driver', icon: Calendar},
    {title: 'Route Planning', subtitle: 'Set locations and map route', icon: MapPin},
  ];

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-[9999] p-4">
      <div className="bg-background dark:bg-card rounded-xl shadow-2xl max-w-4xl w-full max-h-[95vh] overflow-hidden border border-border">
        {/* Enhanced Header */}
        <div className="bg-gradient-to-r from-primary-50 to-primary-100 dark:from-primary-900/20 dark:to-primary-800/20 px-6 py-4 border-b border-border">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="w-10 h-10 bg-primary/10 rounded-lg flex items-center justify-center">
                {React.createElement(stepTitles[currentStep - 1].icon, {
                  className: 'w-5 h-5 text-primary',
                })}
              </div>
              <div>
                <h2 className="text-2xl font-bold text-foreground">
                  {stepTitles[currentStep - 1].title}
                </h2>
                <p className="text-sm text-muted-foreground">
                  {stepTitles[currentStep - 1].subtitle}
                </p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="w-10 h-10 rounded-lg hover:bg-black/10 dark:hover:bg-white/10 flex items-center justify-center text-muted-foreground hover:text-foreground transition-all duration-200 group"
              disabled={isSubmitting}
            >
              <X className="w-5 h-5 group-hover:scale-110 transition-transform" />
            </button>
          </div>

          {/* Progress Bar */}
          <div className="mt-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs text-muted-foreground">
                Step {currentStep} of {totalSteps}
              </span>
              <span className="text-xs text-muted-foreground">
                {Math.round((currentStep / totalSteps) * 100)}%
              </span>
            </div>
            <div className="w-full bg-muted rounded-full h-2">
              <div
                className="bg-primary h-2 rounded-full transition-all duration-300"
                style={{width: `${(currentStep / totalSteps) * 100}%`}}
              ></div>
            </div>
          </div>
        </div>

        <div className="overflow-y-auto max-h-[calc(95vh-140px)]">
          <div className="p-6">
            <form onSubmit={handleSubmit} className="space-y-6">
              {/* Step 1: Trip Details */}
              {currentStep === 1 && (
                <div className="space-y-8">
                  <div className="space-y-6">
                    {/* Trip Name */}
                    <div className="space-y-2">
                      <label className="block text-sm font-medium text-foreground">
                        Trip Name <span className="text-red-500">*</span>
                      </label>
                      <div className="relative">
                        <input
                          type="text"
                          value={tripForm.name}
                          onChange={e => onFormChange('name', e.target.value.slice(0, 25))}
                          placeholder="e.g., Morning Delivery Route"
                          maxLength={25}
                          className="w-full border border-input rounded-lg px-4 py-3 bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary transition-all duration-200 hover:border-primary/50"
                          required
                        />
                        <div className="absolute right-3 top-3 text-xs text-muted-foreground">
                          {tripForm.name.length}/25
                        </div>
                      </div>
                    </div>

                    {/* Priority Selection */}
                    <div className="space-y-3">
                      <label className="block text-sm font-medium text-foreground">
                        Priority Level <span className="text-red-500">*</span>
                      </label>
                      <div className="grid grid-cols-2 gap-3">
                        {[
                          {value: 'low', label: 'Low', color: 'green', icon: '🟢'},
                          {value: 'normal', label: 'Normal', color: 'blue', icon: '🔵'},
                          {value: 'high', label: 'High', color: 'amber', icon: '🟠'},
                          {value: 'urgent', label: 'Urgent', color: 'red', icon: '🔴'},
                        ].map(priority => (
                          <button
                            key={priority.value}
                            type="button"
                            onClick={() => onFormChange('priority', priority.value)}
                            className={`p-4 rounded-lg border-2 transition-all duration-200 flex items-center gap-3 ${tripForm.priority === priority.value
                              ? 'border-primary bg-primary/10'
                              : 'border-border hover:border-primary/50 hover:bg-muted/50'
                              }`}
                          >
                            <span className="text-xl">{priority.icon}</span>
                            <span className="font-medium">{priority.label}</span>
                          </button>
                        ))}
                      </div>
                    </div>

                    {/* Optional Description */}
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <label className="block text-sm font-medium text-foreground">
                          Description
                        </label>
                        <button
                          type="button"
                          onClick={() => setShowDescription(!showDescription)}
                          className="text-primary text-sm hover:underline flex items-center gap-1"
                        >
                          {showDescription ? 'Hide' : 'Add'} Description
                          {showDescription ? (
                            <ChevronUp className="w-4 h-4" />
                          ) : (
                            <ChevronRight className="w-4 h-4" />
                          )}
                        </button>
                      </div>
                      {showDescription && (
                        <textarea
                          value={tripForm.description}
                          onChange={e => onFormChange('description', e.target.value)}
                          placeholder="Add any additional details about this trip..."
                          rows={4}
                          className="w-full border border-input rounded-lg px-4 py-3 bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary transition-all duration-200 hover:border-primary/50 resize-none"
                        />
                      )}
                    </div>

                    {/* Optional Driver Notes */}
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <label className="block text-sm font-medium text-foreground">
                          Driver Notes
                        </label>
                        <button
                          type="button"
                          onClick={() => setShowDriverNotes(!showDriverNotes)}
                          className="text-primary text-sm hover:underline flex items-center gap-1"
                        >
                          {showDriverNotes ? 'Hide' : 'Add'} Notes
                          {showDriverNotes ? (
                            <ChevronUp className="w-4 h-4" />
                          ) : (
                            <ChevronRight className="w-4 h-4" />
                          )}
                        </button>
                      </div>
                      {showDriverNotes && (
                        <textarea
                          value={tripForm.driverNotes}
                          onChange={e => onFormChange('driverNotes', e.target.value)}
                          placeholder="Special instructions for the driver..."
                          rows={3}
                          className="w-full border border-input rounded-lg px-4 py-3 bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary transition-all duration-200 hover:border-primary/50 resize-none"
                        />
                      )}
                    </div>

                    {/* Scheduled Date & Time */}
                    <div className="space-y-4">
                      <h4 className="flex items-center gap-2 text-lg font-medium text-foreground">
                        <Calendar className="w-5 h-5 text-primary" />
                        Trip Schedule
                      </h4>
                      
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        {/* Start Date & Time */}
                        <div className="space-y-4">
                          <h5 className="flex items-center gap-2 text-base font-medium text-foreground">
                            <Clock className="w-4 h-4 text-green-600" />
                            Start Time <span className="text-red-500">*</span>
                          </h5>
                          <div className="grid grid-cols-2 gap-3">
                            <div className="space-y-2">
                              <label className="block text-sm font-medium text-foreground">
                                Date
                              </label>
                              <input
                                type="date"
                                value={tripForm.startDate}
                                onChange={e => handleStartDateChange(e.target.value)}
                                min={new Date().toISOString().split('T')[0]}
                                className="w-full border border-input rounded-lg px-4 py-3 bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary transition-all duration-200 hover:border-primary/50"
                                required
                              />
                            </div>
                            <div className="space-y-2">
                              <label className="block text-sm font-medium text-foreground">
                                Time
                              </label>
                              <input
                                type="time"
                                value={tripForm.startTime}
                                onChange={e => handleStartTimeChange(e.target.value)}
                                className="w-full border border-input rounded-lg px-4 py-3 bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary transition-all duration-200 hover:border-primary/50"
                                required
                              />
                            </div>
                          </div>
                        </div>

                        {/* End Date & Time */}
                        <div className="space-y-4">
                          <h5 className="flex items-center gap-2 text-base font-medium text-foreground">
                            <Clock className="w-4 h-4 text-red-600" />
                            End Time <span className="text-red-500">*</span>
                          </h5>
                          <div className="grid grid-cols-2 gap-3">
                            <div className="space-y-2">
                              <label className="block text-sm font-medium text-foreground">
                                Date
                              </label>
                              <input
                                type="date"
                                value={tripForm.endDate}
                                onChange={e => handleEndDateChange(e.target.value)}
                                min={tripForm.startDate || new Date().toISOString().split('T')[0]}
                                className="w-full border border-input rounded-lg px-4 py-3 bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary transition-all duration-200 hover:border-primary/50"
                                required
                              />
                            </div>
                            <div className="space-y-2">
                              <label className="block text-sm font-medium text-foreground">
                                Time
                              </label>
                              <input
                                type="time"
                                value={tripForm.endTime}
                                onChange={e => handleEndTimeChange(e.target.value)}
                                className="w-full border border-input rounded-lg px-4 py-3 bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary transition-all duration-200 hover:border-primary/50"
                                required
                              />
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Step 2: Vehicle & Driver Selection */}
              {currentStep === 2 && (
                <div className="space-y-8">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {/* Vehicle Selection */}
                    <div className="space-y-3">
                      <label className="block text-sm font-medium text-foreground">
                        Select Vehicle <span className="text-red-500">*</span>
                      </label>
                      {loadingVehicles && (
                        <div className="text-sm text-muted-foreground mb-2 flex items-center gap-2">
                          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary"></div>
                          Loading available vehicles...
                        </div>
                      )}
                      {!loadingVehicles && vehicleOptions.length === 0 && tripForm.startDate && tripForm.startTime && tripForm.endDate && tripForm.endTime && (
                        <div className="text-sm text-amber-600 mb-2">
                          No vehicles available for the selected time period. Please adjust your schedule.
                        </div>
                      )}
                      <SearchableDropdown
                        options={vehicleOptions}
                        value={tripForm.vehicleId}
                        onChange={(value) => onFormChange('vehicleId', value)}
                        placeholder={loadingVehicles ? "Loading vehicles..." : "Choose a vehicle..."}
                        searchPlaceholder="Search vehicles..."
                        icon={Car}
                        required
                        disabled={loadingVehicles}
                      />
                      {!loadingVehicles && vehicleOptions.length > 0 && (
                        <div className="text-sm text-green-600">
                          {vehicleOptions.length} vehicle{vehicleOptions.length > 1 ? 's' : ''} available for your selected time period
                        </div>
                      )}
                    </div>

                    {/* Driver Selection */}
                    <div className="space-y-3">
                      <label className="block text-sm font-medium text-foreground">
                        Select Driver <span className="text-red-500">*</span>
                      </label>
                      {loadingDrivers && (
                        <div className="text-sm text-muted-foreground mb-2 flex items-center gap-2">
                          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary"></div>
                          Loading available drivers...
                        </div>
                      )}
                      {!loadingDrivers && driverOptions.length === 0 && tripForm.startDate && tripForm.startTime && tripForm.endDate && tripForm.endTime && (
                        <div className="text-sm text-amber-600 mb-2">
                          No drivers available for the selected time period. Please adjust your schedule.
                        </div>
                      )}
                      <SearchableDropdown
                        options={driverOptions}
                        value={tripForm.driverId}
                        onChange={(value) => onFormChange('driverId', value)}
                        placeholder={loadingDrivers ? "Loading drivers..." : "Choose a driver..."}
                        searchPlaceholder="Search drivers..."
                        icon={User}
                        required
                        disabled={loadingDrivers}
                      />
                      {!loadingDrivers && driverOptions.length > 0 && (
                        <div className="text-sm text-green-600">
                          {driverOptions.length} driver{driverOptions.length > 1 ? 's' : ''} available for your selected time period
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Trip Schedule Summary */}
                  {tripForm.startDate && tripForm.startTime && tripForm.endDate && tripForm.endTime && (
                    <div className="bg-muted/30 rounded-lg p-4">
                      <h4 className="flex items-center gap-2 text-base font-medium text-foreground mb-3">
                        <Calendar className="w-4 h-4 text-primary" />
                        Scheduled Time
                      </h4>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                        <div className="flex items-center gap-2">
                          <Clock className="w-4 h-4 text-green-600" />
                          <span className="font-medium">Start:</span>
                          <span>{tripForm.startDate} at {tripForm.startTime}</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <Clock className="w-4 h-4 text-red-600" />
                          <span className="font-medium">End:</span>
                          <span>{tripForm.endDate} at {tripForm.endTime}</span>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Step 3: Route Planning */}
              {currentStep === 3 && (
                <div className="space-y-6">
                  {/* Location Inputs */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="space-y-3">
                      <label className="block text-sm font-medium text-foreground">
                        Start Location <span className="text-red-500">*</span>
                      </label>
                      <div className="relative">
                        <MapPin className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-green-600" />
                        <LocationAutocomplete
                          value={tripForm.startLocation}
                          onChange={handleStartLocationChange}
                          placeholder="Enter start location..."
                          className="pl-10"
                        />
                      </div>
                    </div>

                    <div className="space-y-3">
                      <label className="block text-sm font-medium text-foreground">
                        End Location <span className="text-red-500">*</span>
                      </label>
                      <div className="relative">
                        <Flag className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-red-600" />
                        <LocationAutocomplete
                          value={tripForm.endLocation}
                          onChange={handleEndLocationChange}
                          placeholder="Enter end location..."
                          className="pl-10"
                        />
                      </div>
                    </div>
                  </div>

                  {/* Map Section */}
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <h4 className="flex items-center gap-2 text-lg font-medium text-foreground">
                        <Route className="w-5 h-5 text-primary" />
                        Route Map
                      </h4>
                      {routeInfo && (
                        <div className="flex items-center gap-4 text-sm text-muted-foreground">
                          <span>Distance: {routeInfo.distance}</span>
                          <span>Duration: {routeInfo.duration}</span>
                        </div>
                      )}
                    </div>

                    <div className="border border-border rounded-lg overflow-hidden">
                      <div className="h-96 bg-muted/30 relative">
                        <TripPlanningMap
                          startLocation={mapLocations.start}
                          endLocation={mapLocations.end}
                          waypoints={mapLocations.waypoints}
                          onStartLocationChange={handleMapStartLocationChange}
                          onEndLocationChange={handleMapEndLocationChange}
                          onWaypointAdd={handleWaypointAdd}
                          onWaypointRemove={handleWaypointRemove}
                          onRouteCalculated={handleRouteCalculated}
                        />
                      </div>
                    </div>

                    {mapLocations.start && mapLocations.end && (
                      <div className="bg-muted/30 rounded-lg p-4">
                        <div className="flex items-center gap-2 text-sm text-muted-foreground">
                          <CheckCircle className="w-4 h-4 text-green-600" />
                          Route calculated successfully
                          {routeInfo && (
                            <span className="ml-2">
                              • {routeInfo.distance} • {routeInfo.duration}
                            </span>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Navigation Buttons */}
              <div className="flex items-center justify-between pt-6 border-t border-border">
                <button
                  type="button"
                  onClick={prevStep}
                  disabled={currentStep === 1}
                  className="px-6 py-3 text-sm font-medium text-muted-foreground hover:text-foreground disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 flex items-center gap-2"
                >
                  <ChevronLeft className="w-4 h-4" />
                  Previous
                </button>

                <div className="flex items-center gap-3">
                  {currentStep < totalSteps ? (
                    <button
                      type="button"
                      onClick={nextStep}
                      disabled={!isStepValid(currentStep)}
                      className="px-6 py-3 bg-primary text-primary-foreground rounded-lg font-medium hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 flex items-center gap-2"
                    >
                      Next
                      <ChevronRight className="w-4 h-4" />
                    </button>
                  ) : (
                    <button
                      type="submit"
                      disabled={isSubmitting || !isStepValid(currentStep)}
                      className="px-6 py-3 bg-primary text-primary-foreground rounded-lg font-medium hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 flex items-center gap-2"
                    >
                      {isSubmitting ? (
                        <>
                          <div className="w-4 h-4 border-2 border-primary-foreground/30 border-t-primary-foreground rounded-full animate-spin" />
                          Creating Trip...
                        </>
                      ) : (
                        <>
                          <CheckCircle className="w-4 h-4" />
                          Create Trip
                        </>
                      )}
                    </button>
                  )}
                </div>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TripSchedulingModal;
