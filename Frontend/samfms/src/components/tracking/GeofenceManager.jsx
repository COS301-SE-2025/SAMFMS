import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, useMapEvents, useMap } from 'react-leaflet';
import L from 'leaflet';
import { Search, Plus, Edit2, Trash2 } from 'lucide-react';
import { addGeofence, deleteGeofence, updateGeofence } from '../../backend/api/geofences';

// Fix for default markers in react-leaflet
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

// Component to handle map clicks
const MapClickHandler = ({ onLocationSelect }) => {
  useMapEvents({
    click: e => {
      const { lat, lng } = e.latlng;
      onLocationSelect({
        lat: parseFloat(lat.toFixed(6)),
        lng: parseFloat(lng.toFixed(6)),
      });
    },
  });
  return null;
};

// Component to handle map centering when coordinates change
const MapUpdater = ({ center }) => {
  const map = useMap();

  useEffect(() => {
    if (center && center[0] !== 0 && center[1] !== 0) {
      map.setView(center, 15);
    }
  }, [map, center]);

  return null;
};

const GeofenceManager = ({ onGeofenceChange, currentGeofences }) => {
  // State for the component - ensure currentGeofences is properly structured
  const safeCurrentGeofences = (currentGeofences || []).filter(
    geofence => geofence && typeof geofence === 'object'
  );
  const [geofences, setGeofences] = useState(safeCurrentGeofences);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState('');
  const [showAddForm, setShowAddForm] = useState(false);
  const [editingGeofence, setEditingGeofence] = useState(null);
  const [addressSearch, setAddressSearch] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [searchSuggestions, setSearchSuggestions] = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [searchTimeout, setSearchTimeout] = useState(null);
  const [newGeofence, setNewGeofence] = useState({
    name: '',
    description: '',
    type: 'depot',
    geometryType: 'circle',
    radius: 500,
    coordinates: { lat: 37.7749, lng: -122.4194 },
    status: 'active',
  });

  // Filter geofences based on search and type filter
  const filteredGeofences = geofences.filter(geofence => {
    if (!geofence || typeof geofence !== 'object') return false;

    const geofenceName = geofence.name || '';
    const geofenceType = geofence.type || '';
    const searchTermSafe = (searchTerm || '').toLowerCase();

    const matchesSearch =
      searchTermSafe === '' || geofenceName.toLowerCase().includes(searchTermSafe);
    const matchesType = filterType === '' || geofenceType === filterType;

    return matchesSearch && matchesType;
  });

  // Effect to notify parent component when geofences change
  useEffect(() => {
    if (onGeofenceChange) {
      onGeofenceChange(geofences);
    }
  }, [geofences, onGeofenceChange]);

  // Handle search suggestions as user types
  const handleAddressInputChange = value => {
    setAddressSearch(value);

    // Clear existing timeout
    if (searchTimeout) {
      clearTimeout(searchTimeout);
    }

    if (value.trim().length < 3) {
      setSearchSuggestions([]);
      setShowSuggestions(false);
      return;
    }

    // Set new timeout for debounced search
    const timeout = setTimeout(async () => {
      try {
        const response = await fetch(
          `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(
            value
          )}&limit=5`
        );
        const data = await response.json();

        if (data && data.length > 0) {
          setSearchSuggestions(data);
          setShowSuggestions(true);
        } else {
          setSearchSuggestions([]);
          setShowSuggestions(false);
        }
      } catch (error) {
        console.error('Suggestion search error:', error);
        setSearchSuggestions([]);
        setShowSuggestions(false);
      }
    }, 500); // 500ms debounce

    setSearchTimeout(timeout);
  };

  // Handle selecting a suggestion
  const handleSuggestionSelect = suggestion => {
    const lat = parseFloat(suggestion.lat);
    const lng = parseFloat(suggestion.lon);

    setAddressSearch(suggestion.display_name);
    setNewGeofence({
      ...newGeofence,
      coordinates: {
        lat: parseFloat(lat.toFixed(6)),
        lng: parseFloat(lng.toFixed(6)),
      },
    });

    setShowSuggestions(false);
    setSearchSuggestions([]);
  };

  // Handle address search using Nominatim geocoding service
  const handleAddressSearch = async () => {
    if (!addressSearch.trim()) return;

    setIsSearching(true);
    try {
      const response = await fetch(
        `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(
          addressSearch
        )}&limit=1`
      );
      const data = await response.json();

      if (data && data.length > 0) {
        const result = data[0];
        const lat = parseFloat(result.lat);
        const lng = parseFloat(result.lon);

        setNewGeofence({
          ...newGeofence,
          coordinates: {
            lat: parseFloat(lat.toFixed(6)),
            lng: parseFloat(lng.toFixed(6)),
          },
        });
      } else {
        alert('Address not found. Please try a different search term.');
      }
    } catch (error) {
      console.error('Geocoding error:', error);
      alert('Error searching for address. Please try again.');
    } finally {
      setIsSearching(false);
    }
  };

  // Handle adding a new geofence
  const handleAddGeofence = async () => {
    try {
      if (!newGeofence.name) {
        alert('Please fill in the name.');
        return;
      }

      const lat = parseFloat(newGeofence.coordinates.lat);
      const lng = parseFloat(newGeofence.coordinates.lng);

      let geometry;

      if (newGeofence.geometryType === 'circle') {
        // Correct: use center + radius
        geometry = {
          type: 'circle',
          center: { latitude: lat, longitude: lng },
          radius: parseInt(newGeofence.radius),
        };
      } else if (newGeofence.geometryType === 'rectangle') {
        // Generate a small rectangle for demo
        const offset = 0.001;
        geometry = {
          type: 'rectangle',
          points: [
            { latitude: lat + offset, longitude: lng - offset },
            { latitude: lat + offset, longitude: lng + offset },
            { latitude: lat - offset, longitude: lng + offset },
            { latitude: lat - offset, longitude: lng - offset },
          ],
        };
      } else if (newGeofence.geometryType === 'polygon') {
        // Example: simple triangle around the point
        const offset = 0.001;
        geometry = {
          type: 'polygon',
          points: [
            { latitude: lat + offset, longitude: lng },
            { latitude: lat - offset, longitude: lng + offset },
            { latitude: lat - offset, longitude: lng - offset },
          ],
        };
      }

      const payload = {
        name: newGeofence.name,
        description: newGeofence.description || '',
        type: newGeofence.type, // depot, service, delivery, etc.
        status: newGeofence.status || 'active',
        geometry: geometry,
      };

      console.log('Sending geofence data:', payload);
      const response = await addGeofence(payload);
      console.log('Geofence created successfully:', response);

      // Adapt response for UI
      const newGeofenceForUI = {
        ...response,
        coordinates: {
          lat: response.geometry?.center?.latitude || response.geometry?.points?.[0]?.latitude || 0,
          lng:
            response.geometry?.center?.longitude || response.geometry?.points?.[0]?.longitude || 0,
        },
        radius: response.geometry?.radius || 500,
        geometryType: response.geometry?.type || 'circle',
      };

      setGeofences(prev => [...prev, newGeofenceForUI]);
      setShowAddForm(false);
      resetForm();
    } catch (error) {
      console.error('Error creating geofence:', error);
      alert(`Failed to create geofence: ${error.message || error}`);
    }
  };

  // Helper function to get colors based on geofence type
  /*
  const getColorForType = (type, opacity = 1) => {
    const colors = {
      depot: `rgba(0, 123, 255, ${opacity})`,
      service: `rgba(40, 167, 69, ${opacity})`,
      delivery: `rgba(255, 193, 7, ${opacity})`,
      restricted: `rgba(220, 53, 69, ${opacity})`,
      emergency: `rgba(255, 0, 0, ${opacity})`
    };

    return colors[type] || `rgba(108, 117, 125, ${opacity})`;
  };
  */

  // Handle editing a geofence
  const handleEditGeofence = async () => {
    if (!editingGeofence) return;

    try {
      const lat = parseFloat(newGeofence.coordinates.lat);
      const lng = parseFloat(newGeofence.coordinates.lng);

      let geometry;
      if (newGeofence.geometryType === 'circle') {
        geometry = {
          type: 'circle',
          center: { latitude: lat, longitude: lng },
          radius: parseInt(newGeofence.radius),
        };
      } else if (newGeofence.geometryType === 'rectangle') {
        const offset = 0.001;
        geometry = {
          type: 'rectangle',
          points: [
            { latitude: lat + offset, longitude: lng - offset },
            { latitude: lat + offset, longitude: lng + offset },
            { latitude: lat - offset, longitude: lng + offset },
            { latitude: lat - offset, longitude: lng - offset },
          ],
        };
      } else if (newGeofence.geometryType === 'polygon') {
        const offset = 0.001;
        geometry = {
          type: 'polygon',
          points: [
            { latitude: lat + offset, longitude: lng },
            { latitude: lat - offset, longitude: lng + offset },
            { latitude: lat - offset, longitude: lng - offset },
          ],
        };
      }

      const payload = {
        name: newGeofence.name,
        description: newGeofence.description || '',
        type: newGeofence.type,
        status: newGeofence.status,
        geometry: geometry,
      };

      const response = await updateGeofence(editingGeofence.id, payload);
      console.log('Geofence updated successfully:', response);

      const updatedGeofences = geofences.map(g =>
        g.id === editingGeofence.id
          ? { ...g, ...payload, coordinates: { lat, lng }, radius: geometry.radius }
          : g
      );
      setGeofences(updatedGeofences);

      resetForm();
      setEditingGeofence(null);
      setShowAddForm(false);
    } catch (error) {
      console.error('Error updating geofence:', error);
      alert(`Failed to update geofence: ${error.message || error}`);
    }
  };

  // Handle deleting a geofence
  const handleDeleteGeofence = async id => {
    if (window.confirm('Are you sure you want to delete this geofence?')) {
      try {
        await deleteGeofence(id);
        setGeofences(geofences.filter(g => g.id !== id));
        console.log(`Geofence ${id} deleted successfully`);
      } catch (error) {
        console.error('Error deleting geofence:', error);
        alert(`Failed to delete geofence: ${error.message || error}`);
      }
    }
  };

  // Edit geofence
  const startEditGeofence = geofence => {
    setEditingGeofence(geofence);
    setNewGeofence({
      name: geofence.name,
      description: geofence.description,
      type: geofence.type,
      geometryType: geofence.geometryType || 'circle',
      coordinates: geofence.coordinates,
      radius: geofence.radius,
      status: geofence.status,
    });
    setShowAddForm(true);
  };

  // Reset the form
  const resetForm = () => {
    setNewGeofence({
      name: '',
      description: '',
      type: 'depot',
      geometryType: 'circle',
      status: 'active',
      coordinates: { lat: 0, lng: 0 },
      radius: 500,
    });
  };

  return (
    <>
      <div className="bg-card rounded-lg shadow-md p-6 border border-border">
        <div className="flex justify-between items-center mb-4">
          <div className="flex items-center gap-4">
            <h2 className="text-xl font-semibold">Geofences</h2>
            {/* Show search and filter only when table is visible */}
            {!showAddForm && (
              <>
                <div className="relative">
                  <input
                    type="text"
                    placeholder="Search geofences..."
                    className="px-4 py-2 pl-10 rounded-md border border-input bg-background text-sm"
                    value={searchTerm}
                    onChange={e => setSearchTerm(e.target.value)}
                  />
                  <Search
                    className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground"
                    size={16}
                  />
                </div>
                <select
                  className="px-4 py-2 rounded-md border border-input bg-background text-sm"
                  value={filterType}
                  onChange={e => setFilterType(e.target.value)}
                >
                  <option value="">All types</option>
                  <option value="depot">Depot</option>
                  <option value="service">Service</option>
                  <option value="delivery">Delivery</option>
                  <option value="restricted">Restricted</option>
                  <option value="emergency">Emergency</option>
                </select>
              </>
            )}
          </div>
          {/* Show Add button only when table is visible */}
          {!showAddForm && (
            <button
              className="bg-green-600 text-white p-2 rounded-md hover:bg-green-700 transition flex items-center"
              onClick={() => setShowAddForm(true)}
            >
              <Plus size={16} />
            </button>
          )}
        </div>

        {/* Conditional rendering: show form when adding, otherwise show table */}
        {showAddForm ? (
          /* Add Geofence Form */
          <div className="space-y-4">
            <h3 className="text-xl font-semibold mb-4">
              {editingGeofence ? 'Edit Geofence' : 'Add New Geofence'}
            </h3>
            <div className="flex flex-col lg:flex-row gap-6">
              {/* Map Section - Left Side / Top on Mobile */}
              <div className="flex-1 lg:max-w-md space-y-3">
                {/* Address Search Bar */}
                <div className="relative">
                  <div className="flex flex-col sm:flex-row gap-2">
                    <input
                      type="text"
                      placeholder="Search for an address..."
                      value={addressSearch}
                      onChange={e => handleAddressInputChange(e.target.value)}
                      onFocus={() => {
                        if (searchSuggestions.length > 0) {
                          setShowSuggestions(true);
                        }
                      }}
                      onBlur={e => {
                        // Only hide if not clicking on a suggestion
                        if (!e.relatedTarget || !e.relatedTarget.closest('.suggestion-item')) {
                          setTimeout(() => setShowSuggestions(false), 150);
                        }
                      }}
                      onKeyDown={e => {
                        if (e.key === 'Enter') {
                          e.preventDefault();
                          handleAddressSearch();
                          setShowSuggestions(false);
                        }
                        if (e.key === 'Escape') {
                          setShowSuggestions(false);
                        }
                      }}
                      className="flex-1 px-3 py-2 rounded-md border border-input bg-background text-sm focus:ring-2 focus:ring-primary focus:border-transparent"
                      autoComplete="off"
                    />
                    <button
                      type="button"
                      onClick={() => {
                        handleAddressSearch();
                        setShowSuggestions(false);
                      }}
                      disabled={isSearching || !addressSearch.trim()}
                      className="w-full sm:w-auto px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {isSearching ? (
                        <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
                      ) : (
                        <Search size={16} />
                      )}
                      {isSearching ? 'Searching...' : 'Search'}
                    </button>
                  </div>

                  {/* Search Suggestions Dropdown */}
                  {showSuggestions && searchSuggestions.length > 0 && (
                    <div className="absolute z-[9999] w-full mt-1 bg-background border border-input rounded-md shadow-lg max-h-48 overflow-y-auto">
                      {searchSuggestions.map((suggestion, index) => (
                        <div
                          key={index}
                          className="suggestion-item px-3 py-2 hover:bg-accent cursor-pointer border-b border-border last:border-b-0 focus:bg-accent focus:outline-none"
                          tabIndex={0}
                          onMouseDown={e => {
                            // Prevent blur event on input when clicking suggestions
                            e.preventDefault();
                          }}
                          onClick={() => {
                            handleSuggestionSelect(suggestion);
                            setShowSuggestions(false);
                          }}
                          onKeyDown={e => {
                            if (e.key === 'Enter' || e.key === ' ') {
                              e.preventDefault();
                              handleSuggestionSelect(suggestion);
                              setShowSuggestions(false);
                            }
                          }}
                        >
                          <div className="text-sm font-medium text-foreground truncate">
                            {suggestion.display_name}
                          </div>
                          {suggestion.type && (
                            <div className="text-xs text-muted-foreground capitalize">
                              {suggestion.type}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {/* Map Container */}
                <div className="h-64 sm:h-80 lg:h-96 border border-input rounded-md overflow-hidden">
                  <MapContainer
                    center={[
                      newGeofence.coordinates.lat || 37.7749,
                      newGeofence.coordinates.lng || -122.4194,
                    ]}
                    zoom={13}
                    style={{ height: '100%', width: '100%' }}
                    className="rounded-md"
                  >
                    <TileLayer
                      attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                      url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                    />
                    <MapClickHandler
                      onLocationSelect={coords => {
                        setNewGeofence({
                          ...newGeofence,
                          coordinates: coords,
                        });
                      }}
                    />
                    <MapUpdater
                      center={[newGeofence.coordinates.lat, newGeofence.coordinates.lng]}
                    />
                    {/* Show marker if coordinates are set */}
                    {newGeofence.coordinates.lat !== 0 && newGeofence.coordinates.lng !== 0 && (
                      <Marker
                        position={[newGeofence.coordinates.lat, newGeofence.coordinates.lng]}
                      />
                    )}
                  </MapContainer>
                </div>
              </div>

              {/* Form Inputs - Right Side */}
              <div className="flex-1 space-y-4 lg:ml-4">
                {/* Name */}
                <div>
                  <label className="block text-sm font-medium mb-1">Name</label>
                  <input
                    type="text"
                    value={newGeofence.name}
                    onChange={e => setNewGeofence({ ...newGeofence, name: e.target.value })}
                    className="w-full px-3 py-2 rounded-md border border-input bg-background text-sm"
                    placeholder="Geofence name"
                  />
                </div>

                {/* Description */}
                <div>
                  <label className="block text-sm font-medium mb-1">Description</label>
                  <input
                    type="text"
                    value={newGeofence.description}
                    onChange={e => setNewGeofence({ ...newGeofence, description: e.target.value })}
                    className="w-full px-3 py-2 rounded-md border border-input bg-background text-sm"
                    placeholder="Geofence description"
                  />
                </div>

                {/* Category, Shape, and Status - Side by Side */}
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                  {/* Category */}
                  <div>
                    <label className="block text-sm font-medium mb-1">Category</label>
                    <select
                      value={newGeofence.type}
                      onChange={e => setNewGeofence({ ...newGeofence, type: e.target.value })}
                      className="w-full px-3 py-2 rounded-md border border-input bg-background text-sm"
                    >
                      <option value="depot">Depot</option>
                      <option value="service">Service</option>
                      <option value="delivery">Delivery</option>
                      <option value="restricted">Restricted</option>
                      <option value="emergency">Emergency</option>
                    </select>
                  </div>

                  {/* Geometry Type */}
                  <div>
                    <label className="block text-sm font-medium mb-1">Shape</label>
                    <select
                      value={newGeofence.geometryType}
                      onChange={e =>
                        setNewGeofence({ ...newGeofence, geometryType: e.target.value })
                      }
                      className="w-full px-3 py-2 rounded-md border border-input bg-background text-sm"
                    >
                      <option value="circle">Circle</option>
                      <option value="polygon">Polygon</option>
                      <option value="rectangle">Rectangle</option>
                    </select>
                  </div>

                  {/* Status */}
                  <div>
                    <label className="block text-sm font-medium mb-1">Status</label>
                    <select
                      value={newGeofence.status}
                      onChange={e => setNewGeofence({ ...newGeofence, status: e.target.value })}
                      className="w-full px-3 py-2 rounded-md border border-input bg-background text-sm"
                    >
                      <option value="active">Active</option>
                      <option value="inactive">Inactive</option>
                      <option value="draft">Draft</option>
                    </select>
                  </div>
                </div>

                {/* Radius Slider (only for circle) */}
                {newGeofence.geometryType === 'circle' && (
                  <div>
                    <label className="block text-sm font-medium mb-1">
                      Radius: {newGeofence.radius} meters
                    </label>
                    <input
                      type="range"
                      min="0"
                      max="100000"
                      step="100"
                      value={newGeofence.radius}
                      onChange={e =>
                        setNewGeofence({ ...newGeofence, radius: parseInt(e.target.value) })
                      }
                      className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer slider"
                    />
                    <div className="flex justify-between text-xs text-muted-foreground mt-1">
                      <span>0m</span>
                      <span>100,000m</span>
                    </div>
                  </div>
                )}

                {/* Coordinates Display */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                  <div>
                    <label className="block text-sm font-medium mb-1">Latitude</label>
                    <input
                      type="number"
                      value={newGeofence.coordinates.lat}
                      onChange={e =>
                        setNewGeofence({
                          ...newGeofence,
                          coordinates: {
                            ...newGeofence.coordinates,
                            lat: parseFloat(e.target.value) || 0,
                          },
                        })
                      }
                      className="w-full px-3 py-2 rounded-md border border-input bg-background text-sm"
                      step="0.0001"
                      min="-90"
                      max="90"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Longitude</label>
                    <input
                      type="number"
                      value={newGeofence.coordinates.lng}
                      onChange={e =>
                        setNewGeofence({
                          ...newGeofence,
                          coordinates: {
                            ...newGeofence.coordinates,
                            lng: parseFloat(e.target.value) || 0,
                          },
                        })
                      }
                      className="w-full px-3 py-2 rounded-md border border-input bg-background text-sm"
                      step="0.0001"
                      min="-180"
                      max="180"
                    />
                  </div>
                </div>

                {/* Buttons */}
                <div className="flex gap-2 mt-6">
                  <button
                    onClick={() => {
                      setShowAddForm(false);
                      setEditingGeofence(null);
                      resetForm();
                    }}
                    className="flex-1 px-4 py-2 border border-input rounded-md hover:bg-accent transition"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={editingGeofence ? handleEditGeofence : handleAddGeofence}
                    className="flex-1 bg-primary text-primary-foreground px-4 py-2 rounded-md hover:bg-primary/90 transition"
                    disabled={
                      !newGeofence.name ||
                      (newGeofence.geometryType === 'circle' && isNaN(newGeofence.radius))
                    }
                  >
                    {editingGeofence ? 'Update' : 'Add'} Geofence
                  </button>
                </div>
              </div>
            </div>
          </div>
        ) : (
          /* Geofence Table */
          <div className="overflow-x-auto">
            <table className="w-full border-collapse">
              <thead>
                <tr className="border-b border-border">
                  <th className="text-left py-3 px-4">Name</th>
                  <th className="text-left py-3 px-4">Type</th>
                  <th className="text-left py-3 px-4">Shape</th>
                  <th className="text-left py-3 px-4">Size</th>
                  <th className="text-left py-3 px-4">Coordinates</th>
                  <th className="text-left py-3 px-4">Status</th>
                  <th className="text-left py-3 px-4">Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredGeofences.length > 0 ? (
                  filteredGeofences.map(geofence => (
                    <tr key={geofence.id} className="border-b border-border hover:bg-accent/10">
                      <td className="py-3 px-4">{geofence?.name || 'N/A'}</td>
                      <td className="py-3 px-4">
                        {geofence?.type
                          ? geofence.type.charAt(0).toUpperCase() + geofence.type.slice(1)
                          : 'Unknown'}
                      </td>
                      <td className="py-3 px-4">
                        {(geofence.geometryType || geofence.geometry?.type || 'circle')
                          .charAt(0)
                          .toUpperCase() +
                          (geofence.geometryType || geofence.geometry?.type || 'circle').slice(1)}
                      </td>
                      <td className="py-3 px-4">
                        {geofence.radius ? `${geofence.radius}m` : 'Custom'}
                      </td>
                      <td className="py-3 px-4">
                        {geofence.coordinates.lat.toFixed(4)}, {geofence.coordinates.lng.toFixed(4)}
                      </td>
                      <td className="py-3 px-4">
                        {geofence.status === 'active' ? (
                          <span className="bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200 py-1 px-2 rounded-full text-xs">
                            Active
                          </span>
                        ) : (
                          <span className="bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200 py-1 px-2 rounded-full text-xs">
                            Inactive
                          </span>
                        )}
                      </td>
                      <td className="py-3 px-4 space-x-2">
                        <button
                          className="text-primary hover:text-primary/80 text-sm"
                          onClick={() => startEditGeofence(geofence)}
                        >
                          <Edit2 size={16} className="inline mr-1" />
                          Edit
                        </button>
                        <button
                          className="text-destructive hover:text-destructive/80 text-sm"
                          onClick={() => handleDeleteGeofence(geofence.id)}
                        >
                          <Trash2 size={16} className="inline mr-1" />
                          Delete
                        </button>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan="7" className="py-8 text-center text-muted-foreground">
                      No geofences found
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </>
  );
};

export default GeofenceManager;
