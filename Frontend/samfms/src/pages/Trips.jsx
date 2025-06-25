import React, {useState, useEffect, useRef} from 'react';
import VehicleStatistics from '../components/trips/VehicleStatistics';
import MapDisplay from '../components/trips/MapDisplay';
import VehicleList from '../components/trips/VehicleList';

// Custom hook for location autocomplete using Nominatim (OpenStreetMap)
const useLocationAutocomplete = () => {
  const [suggestions, setSuggestions] = useState([]);
  const [isLoading, setIsLoading] = useState(false);

  const searchLocation = async (query) => {
    if (!query || query.length < 2) { // Reduced from 3 to 2
      setSuggestions([]);
      return;
    }

    setIsLoading(true);
    try {
      // Enhanced Nominatim query with more parameters
      const params = new URLSearchParams({
        format: 'json',
        q: query,
        limit: '10', // Increased from 5 to 10
        addressdetails: '1',
        'accept-language': 'en', // Prefer English results
        countrycodes: 'za', // Limit to South Africa (adjust as needed)
        dedupe: '1', // Remove duplicate results
        extratags: '1', // Include additional tags
        namedetails: '1' // Include name variations
      });

      const response = await fetch(
        `https://nominatim.openstreetmap.org/search?${params.toString()}`,
        {
          headers: {
            'User-Agent': 'YourAppName/1.0' // Always include a User-Agent
          }
        }
      );

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();

      // Enhanced filtering and sorting
      const filteredResults = data
        .filter(item => {
          // Filter out results that are too generic or low quality
          const importance = parseFloat(item.importance) || 0;
          return importance > 0.1; // Adjust threshold as needed
        })
        .sort((a, b) => {
          // Sort by importance (relevance)
          const importanceA = parseFloat(a.importance) || 0;
          const importanceB = parseFloat(b.importance) || 0;
          return importanceB - importanceA;
        });

      setSuggestions(filteredResults);
    } catch (error) {
      console.error('Error fetching location suggestions:', error);
      setSuggestions([]);

      // Fallback: Try a simpler query if the first one fails
      try {
        const simpleResponse = await fetch(
          `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(query)}&limit=5`,
          {
            headers: {
              'User-Agent': 'YourAppName/1.0'
            }
          }
        );

        if (simpleResponse.ok) {
          const fallbackData = await simpleResponse.json();
          setSuggestions(fallbackData);
        }
      } catch (fallbackError) {
        console.error('Fallback search also failed:', fallbackError);
      }
    } finally {
      setIsLoading(false);
    }
  };

  return {suggestions, isLoading, searchLocation};
};

// Location Autocomplete Component
const LocationAutocomplete = ({value, onChange, placeholder, className, required}) => {
  const [inputValue, setInputValue] = useState(value || '');
  const [showSuggestions, setShowSuggestions] = useState(false);
  const {suggestions, isLoading, searchLocation} = useLocationAutocomplete();
  const debounceRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    setInputValue(value || '');
  }, [value]);

  const handleInputChange = (e) => {
    const newValue = e.target.value;
    setInputValue(newValue);

    // Clear previous debounce
    if (debounceRef.current) {
      clearTimeout(debounceRef.current);
    }

    // Debounce the search
    debounceRef.current = setTimeout(() => {
      searchLocation(newValue);
      setShowSuggestions(true);
    }, 300);
  };

  const handleSuggestionClick = (suggestion) => {
    const address = suggestion.display_name;
    setInputValue(address);
    setShowSuggestions(false);
    onChange(address, {
      lat: parseFloat(suggestion.lat),
      lng: parseFloat(suggestion.lon),
      formatted_address: address,
      place_id: suggestion.place_id
    });
  };

  const handleBlur = () => {
    // Delay hiding suggestions to allow for clicks
    setTimeout(() => setShowSuggestions(false), 200);
  };

  const handleFocus = () => {
    if (suggestions.length > 0) {
      setShowSuggestions(true);
    }
  };

  return (
    <div className="relative">
      <input
        ref={inputRef}
        type="text"
        value={inputValue}
        onChange={handleInputChange}
        onBlur={handleBlur}
        onFocus={handleFocus}
        placeholder={placeholder}
        className={className}
        required={required}
      />

      {showSuggestions && (suggestions.length > 0 || isLoading) && (
        <div className="absolute z-10 w-full bg-white border border-gray-300 rounded-md shadow-lg mt-1 max-h-60 overflow-y-auto">
          {isLoading ? (
            <div className="p-3 text-center text-gray-500">
              <div className="inline-block animate-spin rounded-full h-4 w-4 border-b-2 border-gray-900"></div>
              <span className="ml-2">Searching...</span>
            </div>
          ) : (
            suggestions.map((suggestion, index) => (
              <div
                key={suggestion.place_id || index}
                className="p-3 hover:bg-gray-100 cursor-pointer border-b border-gray-100 last:border-b-0"
                onClick={() => handleSuggestionClick(suggestion)}
              >
                <div className="font-medium text-sm">{suggestion.display_name}</div>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
};

const Trips = () => {
  // Sample mock data for vehicles with location
  const [vehicles, setVehicles] = useState([]);
  const [selectedVehicle, setSelectedVehicle] = useState(null);
  const [showScheduleModal, setShowScheduleModal] = useState(false);

  // Trip form state
  const [tripForm, setTripForm] = useState({
    vehicleId: '',
    startLocation: '',
    endLocation: '',
    scheduledDate: '',
    scheduledTime: '',
    notes: ''
  });

  // Store coordinates for selected locations
  const [locationCoords, setLocationCoords] = useState({
    start: null,
    end: null
  });

  useEffect(() => {
    // Connect to your Core backend WebSocket endpoint
    const ws = new WebSocket('ws://localhost:8000/ws/vehicles');

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.vehicles) {
        setVehicles(data.vehicles);
      } else {
        setVehicles([]);
        console.warn("No vehicles data received:", data);
      }
    };

    ws.onerror = (err) => {
      console.error('WebSocket error:', err);
    };

    ws.onclose = (event) => {
      console.warn('WebSocket closed:', event);
    };

    return () => ws.close();
  }, []);

  // Calculate statistics
  const stats = {
    activeVehicles: vehicles.filter(v => v.status === 'online').length,
    idleVehicles: vehicles.filter(v => v.status === 'offline').length,
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
      vehicleId: '',
      startLocation: '',
      endLocation: '',
      scheduledDate: '',
      scheduledTime: '',
      notes: ''
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

  const handleSubmitTrip = async (e) => {
    e.preventDefault();

    // Validate form
    if (!tripForm.vehicleId || !tripForm.startLocation ||
      !tripForm.endLocation || !tripForm.scheduledDate || !tripForm.scheduledTime) {
      alert('Please fill in all required fields');
      return;
    }

    try {
      // Here you would make an API call to your backend to create the trip
      const tripData = {
        ...tripForm,
        scheduledDateTime: `${tripForm.scheduledDate}T${tripForm.scheduledTime}`,
        status: 'scheduled',
        coordinates: locationCoords // Include coordinates for mapping
      };

      console.log('Creating trip:', tripData);

      // Replace with actual API call
      // const response = await fetch('/api/trips', {
      //   method: 'POST',
      //   headers: { 'Content-Type': 'application/json' },
      //   body: JSON.stringify(tripData)
      // });

      alert('Trip scheduled successfully!');
      handleCloseModal();
    } catch (error) {
      console.error('Error scheduling trip:', error);
      alert('Failed to schedule trip. Please try again.');
    }
  };

  // Get available vehicles (online and not assigned to active trips)
  const availableVehicles = vehicles.filter(v => v.status === 'online');

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

        {/* Map and Vehicle List Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Map display takes 2/3 of the width on large screens */}
          <div className="lg:col-span-2">
            <MapDisplay vehicles={vehicles} selectedVehicle={selectedVehicle} />
          </div>
          {/* Vehicle list takes 1/3 of the width on large screens */}
          <div className="lg:col-span-1">
            <VehicleList vehicles={vehicles} onSelectVehicle={handleSelectVehicle} />
          </div>

          {/* Schedule Trip Button */}
          <div className="mt-6 flex justify-end">
            <button
              className="bg-primary text-primary-foreground px-4 py-2 rounded-md hover:bg-primary/90 transition"
              onClick={handleScheduleTrip}
            >
              Schedule New Trip
            </button>
          </div>

          {/* Schedule Trip Modal */}
          {showScheduleModal && (
            <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[9999] p-4">
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
                <div className="p-6">
                  <div className="flex justify-between items-center mb-6">
                    <h2 className="text-2xl font-bold">Schedule New Trip</h2>
                    <button
                      onClick={handleCloseModal}
                      className="text-gray-400 hover:text-gray-600 text-2xl"
                    >
                      ×
                    </button>
                  </div>

                  <form onSubmit={handleSubmitTrip} className="space-y-4">
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
                            {vehicle.name || `Vehicle ${vehicle.id}`} - {vehicle.id}
                          </option>
                        ))}
                      </select>
                      {availableVehicles.length === 0 && (
                        <p className="text-sm text-red-500 mt-1">No available vehicles</p>
                      )}
                    </div>

                    {/* Start Location */}
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

                    {/* End Location */}
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

                    {/* Date and Time */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium mb-2">
                          Scheduled Date <span className="text-red-500">*</span>
                        </label>
                        <input
                          type="date"
                          value={tripForm.scheduledDate}
                          onChange={(e) => handleFormChange('scheduledDate', e.target.value)}
                          min={new Date().toISOString().split('T')[0]}
                          className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary"
                          required
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium mb-2">
                          Scheduled Time <span className="text-red-500">*</span>
                        </label>
                        <input
                          type="time"
                          value={tripForm.scheduledTime}
                          onChange={(e) => handleFormChange('scheduledTime', e.target.value)}
                          className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary"
                          required
                        />
                      </div>
                    </div>

                    {/* Notes */}
                    <div>
                      <label className="block text-sm font-medium mb-2">
                        Notes (Optional)
                      </label>
                      <textarea
                        value={tripForm.notes}
                        onChange={(e) => handleFormChange('notes', e.target.value)}
                        placeholder="Add any additional notes or instructions..."
                        rows="3"
                        className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary"
                      />
                    </div>

                    {/* Form Actions */}
                    <div className="flex justify-end space-x-3 pt-4">
                      <button
                        type="button"
                        onClick={handleCloseModal}
                        className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 transition"
                      >
                        Cancel
                      </button>
                      <button
                        type="submit"
                        className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition"
                        disabled={availableVehicles.length === 0}
                      >
                        Schedule Trip
                      </button>
                    </div>
                  </form>
                </div>
              </div>
            </div>
          )}

          {/* Trip History Section */}
          <div className="mt-8">
            <h2 className="text-xl font-semibold mb-4">Trip History</h2>
            <div className="bg-card rounded-lg shadow-md p-6 border border-border">
              <div className="overflow-x-auto">
                <table className="w-full border-collapse">
                  <thead>
                    <tr className="border-b border-border">
                      <th className="text-left py-3 px-4">Vehicle ID</th>
                      <th className="text-left py-3 px-4">Name</th>
                      <th className="text-left py-3 px-4">Status</th>
                      <th className="text-left py-3 px-4">Last Update</th>
                      <th className="text-left py-3 px-4">Speed</th>
                      <th className="text-left py-3 px-4">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {vehicles.length > 0 ? (
                      vehicles.map(vehicle => (
                        <tr key={vehicle.id} className="border-b border-border hover:bg-accent/10">
                          <td className="py-3 px-4">{vehicle.id}</td>
                          <td className="py-3 px-4">{vehicle.name || 'Unknown'}</td>
                          <td className="py-3 px-4">
                            <span className={
                              vehicle.status === 'online'
                                ? "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200 py-1 px-2 rounded-full text-xs"
                                : "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200 py-1 px-2 rounded-full text-xs"
                            }>
                              {vehicle.status === 'online' ? 'Active' : 'Idle'}
                            </span>
                          </td>
                          <td className="py-3 px-4">{vehicle.lastUpdate ? new Date(vehicle.lastUpdate).toLocaleString() : 'Unknown'}</td>
                          <td className="py-3 px-4">{vehicle.speed != null ? `${vehicle.speed} km/h` : 'N/A'}</td>
                          <td className="py-3 px-4">
                            <button className="text-primary hover:text-primary/80" onClick={() => handleSelectVehicle(vehicle)}>
                              Details
                            </button>
                          </td>
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td colSpan={6} className="py-3 px-4 text-center text-muted-foreground">
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
    </div>
  );
};

export default Trips;