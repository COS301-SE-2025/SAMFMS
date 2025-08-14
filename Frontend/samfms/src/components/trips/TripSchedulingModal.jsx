import React, { useState, useEffect } from 'react';
import { X } from 'lucide-react';
import TripPlanningMap from './TripPlanningMap';
import LocationAutocomplete from './LocationAutocomplete';

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
  const [mapLocations, setMapLocations] = useState({
    start: null,
    end: null,
    waypoints: [],
  });
  const [routeInfo, setRouteInfo] = useState(null);
  const [routeCalculating, setRouteCalculating] = useState(false);
  const [showDescription, setShowDescription] = useState(false);
  const [showDriverNotes, setShowDriverNotes] = useState(false);
  const [activeTab, setActiveTab] = useState('basic'); // 'basic' or 'map'

  // Utility functions for time
  const getCurrentDate = () => {
    const now = new Date();
    return now.toISOString().split('T')[0]; // Format: YYYY-MM-DD
  };

  // Handle location changes from autocomplete
  const handleStartLocationChange = (location, coordinates) => {
    console.log('Start location changed:', { location, coordinates });
    onFormChange('startLocation', location);
    if (coordinates) {
      const newMapLocations = {
        ...mapLocations,
        start: { lat: coordinates.lat, lng: coordinates.lng },
      };
      console.log('Updated map locations (start):', newMapLocations);
      setMapLocations(newMapLocations);

      // Switch to map tab to show the route when both locations are set
      if (newMapLocations.end) {
        console.log('Both locations set, switching to map tab');
        setActiveTab('map');
      }
    }
  };

  const handleEndLocationChange = (location, coordinates) => {
    console.log('End location changed:', { location, coordinates });
    onFormChange('endLocation', location);
    if (coordinates) {
      const newMapLocations = {
        ...mapLocations,
        end: { lat: coordinates.lat, lng: coordinates.lng },
      };
      console.log('Updated map locations (end):', newMapLocations);
      setMapLocations(newMapLocations);

      // Switch to map tab to show the route when both locations are set
      if (newMapLocations.start) {
        console.log('Both locations set, switching to map tab');
        setActiveTab('map');
      }
    }
  };

  // Handle map location selection
  const handleMapStartLocationChange = coords => {
    const newMapLocations = { ...mapLocations, start: coords };
    setMapLocations(newMapLocations);
    // Update form with coordinates (could be enhanced with reverse geocoding)
    onFormChange('startLocation', `${coords.lat.toFixed(6)}, ${coords.lng.toFixed(6)}`);
  };

  const handleMapEndLocationChange = coords => {
    const newMapLocations = { ...mapLocations, end: coords };
    setMapLocations(newMapLocations);
    // Update form with coordinates (could be enhanced with reverse geocoding)
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

  // Enhanced form submission with route data
  const handleSubmit = e => {
    e.preventDefault();
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
  };

  // Reset locations when modal closes
  useEffect(() => {
    if (!showModal) {
      setMapLocations({ start: null, end: null, waypoints: [] });
      setRouteInfo(null);
      setActiveTab('basic');
    }
  }, [showModal]);

  if (!showModal) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-[9999] p-4">
      <div className="bg-card dark:bg-card rounded-lg shadow-xl max-w-6xl w-full max-h-[95vh] overflow-y-auto border border-border">
        <div className="p-6">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-2xl font-bold text-foreground">Schedule New Trip</h2>
            <button
              onClick={onClose}
              className="text-muted-foreground hover:text-foreground text-2xl transition-colors"
              disabled={isSubmitting}
            >
              <X size={24} />
            </button>
          </div>

          {/* Tab Navigation */}
          <div className="flex border-b border-border mb-6">
            <button
              onClick={() => setActiveTab('basic')}
              className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
                activeTab === 'basic'
                  ? 'border-primary text-primary'
                  : 'border-transparent text-muted-foreground hover:text-foreground'
              }`}
            >
              Trip Details
            </button>
            <button
              onClick={() => setActiveTab('map')}
              className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
                activeTab === 'map'
                  ? 'border-primary text-primary'
                  : 'border-transparent text-muted-foreground hover:text-foreground'
              }`}
            >
              Route Planning
            </button>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Basic Trip Details Tab */}
            {activeTab === 'basic' && (
              <div className="space-y-6">
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
                        onChange={e => onFormChange('name', e.target.value.slice(0, 25))}
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
                        onClick={() => onFormChange('priority', 'low')}
                        className={`px-3 py-2 rounded-md border ${
                          tripForm.priority === 'low'
                            ? 'bg-green-100 border-green-300 ring-2 ring-green-300'
                            : 'bg-background border-input hover:bg-accent'
                        } transition-colors`}
                      >
                        <div className="flex items-center justify-center gap-2">
                          <span className="h-3 w-3 rounded-full bg-green-500"></span>
                          <span className="font-medium text-green-700">Low</span>
                        </div>
                      </button>
                      <button
                        type="button"
                        onClick={() => onFormChange('priority', 'normal')}
                        className={`px-3 py-2 rounded-md border ${
                          tripForm.priority === 'normal'
                            ? 'bg-blue-100 border-blue-300 ring-2 ring-blue-300'
                            : 'bg-background border-input hover:bg-accent'
                        } transition-colors`}
                      >
                        <div className="flex items-center justify-center gap-2">
                          <span className="h-3 w-3 rounded-full bg-blue-500"></span>
                          <span className="font-medium text-blue-700">Normal</span>
                        </div>
                      </button>
                      <button
                        type="button"
                        onClick={() => onFormChange('priority', 'high')}
                        className={`px-3 py-2 rounded-md border ${
                          tripForm.priority === 'high'
                            ? 'bg-amber-100 border-amber-300 ring-2 ring-amber-300'
                            : 'bg-background border-input hover:bg-accent'
                        } transition-colors`}
                      >
                        <div className="flex items-center justify-center gap-2">
                          <span className="h-3 w-3 rounded-full bg-amber-500"></span>
                          <span className="font-medium text-amber-700">High</span>
                        </div>
                      </button>
                      <button
                        type="button"
                        onClick={() => onFormChange('priority', 'urgent')}
                        className={`px-3 py-2 rounded-md border ${
                          tripForm.priority === 'urgent'
                            ? 'bg-red-100 border-red-300 ring-2 ring-red-300'
                            : 'bg-background border-input hover:bg-accent'
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

                {/* Vehicle and Driver Selection */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium mb-2 text-foreground">
                      Select Vehicle <span className="text-red-500">*</span>
                    </label>
                    <select
                      value={tripForm.vehicleId}
                      onChange={e => onFormChange('vehicleId', e.target.value)}
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
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-2 text-foreground">
                      Select Driver <span className="text-red-500">*</span>
                    </label>
                    <select
                      value={tripForm.driverId}
                      onChange={e => onFormChange('driverId', e.target.value)}
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

                {/* Location Section with Autocomplete */}
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
                      placeholder="Enter end location or address"
                      className="w-full border border-input rounded-md px-3 py-2 bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                      required
                    />
                  </div>
                </div>

                {/* Date and Time Section */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-4">
                    <h3 className="text-lg font-medium text-foreground">Start Schedule</h3>
                    <div>
                      <label className="block text-sm font-medium mb-2 text-foreground">
                        Start Date <span className="text-red-500">*</span>
                      </label>
                      <input
                        type="date"
                        value={tripForm.scheduledStartDate}
                        onChange={e => onFormChange('scheduledStartDate', e.target.value)}
                        min={getCurrentDate()}
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
                        onChange={e => onFormChange('scheduledStartTime', e.target.value)}
                        className="w-full border border-input rounded-md px-3 py-2 bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                        required
                      />
                    </div>
                  </div>
                  <div className="space-y-4">
                    <h3 className="text-lg font-medium text-foreground">End Schedule</h3>
                    <div>
                      <label className="block text-sm font-medium mb-2 text-foreground">
                        End Date <span className="text-red-500">*</span>
                      </label>
                      <input
                        type="date"
                        value={tripForm.scheduledEndDate}
                        onChange={e => onFormChange('scheduledEndDate', e.target.value)}
                        min={tripForm.scheduledStartDate || getCurrentDate()}
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
                        onChange={e => onFormChange('scheduledEndTime', e.target.value)}
                        className="w-full border border-input rounded-md px-3 py-2 bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                        required
                      />
                    </div>
                  </div>
                </div>

                {/* Optional Fields */}
                <div className="space-y-4">
                  {/* Description Toggle */}
                  <div className="border border-border rounded-lg overflow-hidden">
                    <button
                      type="button"
                      onClick={() => setShowDescription(!showDescription)}
                      className="flex items-center justify-between w-full p-3 text-sm font-medium text-foreground hover:bg-accent/50 transition-colors"
                    >
                      <span>
                        {showDescription ? 'Hide Trip Description' : 'Add Trip Description'}
                      </span>
                      <span
                        className={`transform transition-transform ${
                          showDescription ? 'rotate-180' : ''
                        }`}
                      >
                        ▼
                      </span>
                    </button>
                    {showDescription && (
                      <div className="p-3 border-t border-border">
                        <textarea
                          value={tripForm.description}
                          onChange={e => onFormChange('description', e.target.value.slice(0, 120))}
                          placeholder="Brief description of the trip purpose"
                          rows="2"
                          maxLength={120}
                          className="w-full border border-input rounded-md px-3 py-2 bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                        />
                        <div className="text-xs text-muted-foreground mt-1">
                          {tripForm.description.length}/120
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Driver Notes Toggle */}
                  <div className="border border-border rounded-lg overflow-hidden">
                    <button
                      type="button"
                      onClick={() => setShowDriverNotes(!showDriverNotes)}
                      className="flex items-center justify-between w-full p-3 text-sm font-medium text-foreground hover:bg-accent/50 transition-colors"
                    >
                      <span>{showDriverNotes ? 'Hide Driver Notes' : 'Add Driver Notes'}</span>
                      <span
                        className={`transform transition-transform ${
                          showDriverNotes ? 'rotate-180' : ''
                        }`}
                      >
                        ▼
                      </span>
                    </button>
                    {showDriverNotes && (
                      <div className="p-3 border-t border-border">
                        <textarea
                          value={tripForm.driverNote}
                          onChange={e => onFormChange('driverNote', e.target.value.slice(0, 150))}
                          placeholder="Special instructions for the driver"
                          rows="3"
                          maxLength={150}
                          className="w-full border border-input rounded-md px-3 py-2 bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                        />
                        <div className="text-xs text-muted-foreground mt-1">
                          {tripForm.driverNote.length}/150
                        </div>
                      </div>
                    )}
                  </div>
                </div>

                {/* Route Preview Section - Shows when both locations are selected */}
                {mapLocations.start && mapLocations.end && (
                  <div className="border border-border rounded-lg p-4 bg-muted/10">
                    <div className="flex items-center justify-between mb-3">
                      <h4 className="font-medium text-foreground">Route Preview</h4>
                      <button
                        type="button"
                        onClick={() => setActiveTab('map')}
                        className="text-sm text-primary hover:text-primary/80 underline"
                      >
                        View Full Map
                      </button>
                    </div>

                    {routeInfo ? (
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                        <div className="flex items-center gap-2">
                          <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                          <span className="text-muted-foreground">Distance:</span>
                          <span className="font-medium">
                            {(routeInfo.distance / 1000).toFixed(1)} km
                          </span>
                        </div>
                        <div className="flex items-center gap-2">
                          <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                          <span className="text-muted-foreground">Duration:</span>
                          <span className="font-medium">
                            {Math.round(routeInfo.duration / 60)} min
                          </span>
                        </div>
                        <div className="flex items-center gap-2">
                          <div className="w-2 h-2 bg-orange-500 rounded-full"></div>
                          <span className="text-muted-foreground">Waypoints:</span>
                          <span className="font-medium">{mapLocations.waypoints.length}</span>
                        </div>
                      </div>
                    ) : routeCalculating ? (
                      <div className="flex items-center gap-2 text-sm text-muted-foreground">
                        <div className="animate-spin w-4 h-4 border-2 border-primary border-t-transparent rounded-full"></div>
                        Calculating route...
                      </div>
                    ) : (
                      <div className="text-sm text-muted-foreground">
                        Route will be calculated automatically when both locations are set.
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}

            {/* Map Tab */}
            {activeTab === 'map' && (
              <div className="space-y-4">
                <div className="text-sm text-muted-foreground mb-4">
                  Use the map below to select your start and end locations, and add waypoints as
                  needed. The route will be automatically calculated using OSRM routing service.
                </div>

                <TripPlanningMap
                  startLocation={mapLocations.start}
                  endLocation={mapLocations.end}
                  waypoints={mapLocations.waypoints}
                  onStartLocationChange={handleMapStartLocationChange}
                  onEndLocationChange={handleMapEndLocationChange}
                  onWaypointAdd={handleWaypointAdd}
                  onWaypointRemove={handleWaypointRemove}
                  onRouteCalculated={handleRouteCalculated}
                  routeCalculating={routeCalculating}
                  setRouteCalculating={setRouteCalculating}
                  className="h-96"
                />

                {/* Route Information */}
                {routeInfo && (
                  <div className="bg-muted/20 rounded-lg p-4">
                    <h4 className="font-medium text-foreground mb-2">Route Information</h4>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                      <div>
                        <span className="text-muted-foreground">Distance:</span>
                        <div className="font-medium">
                          {(routeInfo.distance / 1000).toFixed(2)} km
                        </div>
                      </div>
                      <div>
                        <span className="text-muted-foreground">Estimated Duration:</span>
                        <div className="font-medium">
                          {Math.round(routeInfo.duration / 60)} minutes
                        </div>
                      </div>
                      <div>
                        <span className="text-muted-foreground">Waypoints:</span>
                        <div className="font-medium">{mapLocations.waypoints.length} stops</div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Form Actions */}
            <div className="flex justify-end space-x-3 pt-4 border-t border-border">
              <button
                type="button"
                onClick={onClose}
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
  );
};

export default TripSchedulingModal;
