import React, { useState, useEffect, useRef } from 'react';
import {
  MapContainer,
  TileLayer,
  Marker,
  useMapEvents,
  useMap,
  Polygon,
  Circle as LeafletCircle
} from 'react-leaflet';
import L from 'leaflet';
import '@geoman-io/leaflet-geoman-free';
import '@geoman-io/leaflet-geoman-free/dist/leaflet-geoman.css';
import { Search } from 'lucide-react';
import { createGeofence, deleteGeofence, updateGeofence } from '../../backend/api/geofences';

// Fix for default markers in react-leaflet
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

const GeomanControls = ({ onShapeCreated }) => {
  const map = useMap();

  useEffect(() => {
    // Add Leaflet-Geoman controls
    map.pm.addControls({
      position: 'topleft',
      drawMarker: false,
      drawPolyline: false,
      drawCircle: true,
      drawCircleMarker: false,
      drawPolygon: true,
      drawRectangle: true,
      cutPolygon: false,
      editMode: true,
      dragMode: false,
      removalMode: true,
    });

    // Capture shape coordinates when user finishes drawing
    map.on('pm:create', e => {
      const shape = e.shape;
      let coords, radius;
      if (shape === 'Circle') {
        const center = e.layer.getLatLng();
        radius = e.layer.getRadius();
        coords = { latitude: center.lat, longitude: center.lng };
        onShapeCreated(coords, shape, radius);
      } else {
        // For Polygon or Rectangle
        const latlngs = e.layer.getLatLngs()[0];
        coords = latlngs.map(p => ({ latitude: p.lat, longitude: p.lng }));
        onShapeCreated(coords, shape);
      }
    });

    return () => {
      map.pm.removeControls();
      map.off('pm:create');
    };
  }, [map, onShapeCreated]);

  return null;
};

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

const GeofenceManager = ({
  onGeofenceChange,
  currentGeofences,
  initialShowForm = false,
  showFormOnly = false,
  onCancel,
  onSuccess,
  editingGeofence: editingGeofenceProp,
}) => {
  // State for the component - ensure currentGeofences is properly structured
  const safeCurrentGeofences = (currentGeofences || []).filter(
    geofence => geofence && typeof geofence === 'object'
  );
  const [geofences, setGeofences] = useState(safeCurrentGeofences);
  const [showAddForm, setShowAddForm] = useState(initialShowForm);
  const [editingGeofence, setEditingGeofence] = useState(editingGeofenceProp || null);
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
    polygon: [],
    status: 'active',
  });

  const mapRef = useRef(null);

  // Handle editing geofence prop changes
  useEffect(() => {
    if (editingGeofenceProp) {
      const isCircle = editingGeofenceProp.shape === 'circle';
      setNewGeofence({
        name: editingGeofenceProp.name || '',
        description: editingGeofenceProp.description || '',
        type: editingGeofenceProp.type || 'depot',
        geometryType: isCircle ? 'circle' : 'polygon',
        radius: isCircle ? editingGeofenceProp.radius || 500 : 500,
        coordinates: isCircle ? editingGeofenceProp.coordinates || { lat: 37.7749, lng: -122.4194 } : { lat: 0, lng: 0 },
        polygon: !isCircle ? editingGeofenceProp.latlngs.map(([lat, lng]) => ({ latitude: lat, longitude: lng })) : [],
        status: editingGeofenceProp.status || 'active',
      });
      setEditingGeofence(editingGeofenceProp);
      setShowAddForm(true);
    }
  }, [editingGeofenceProp]);

  // Load existing shape for editing
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !editingGeofence) return;

    let layer;
    if (editingGeofence.shape === 'circle') {
      layer = L.circle(
        [editingGeofence.coordinates.lat, editingGeofence.coordinates.lng],
        { radius: editingGeofence.radius }
      );
    } else {
      layer = L.polygon(editingGeofence.latlngs);
    }

    if (layer) {
      layer.addTo(map);
      layer.pm.enable({ allowSelfIntersection: false });

      // Listen for edits
      map.on('pm:edit', e => {
        const editedLayer = e.layer;
        if (editedLayer instanceof L.Circle) {
          const center = editedLayer.getLatLng();
          const radius = editedLayer.getRadius();
          setNewGeofence(prev => ({
            ...prev,
            coordinates: { lat: center.lat, lng: center.lng },
            radius,
          }));
        } else if (editedLayer instanceof L.Polygon) {
          const latlngs = editedLayer.getLatLngs()[0];
          const points = latlngs.map(ll => ({ latitude: ll.lat, longitude: ll.lng }));
          setNewGeofence(prev => ({
            ...prev,
            polygon: points,
          }));
        }
      });

      // Center on layer
      map.fitBounds(layer.getBounds());
    }

    return () => {
      if (layer) map.removeLayer(layer);
      map.off('pm:edit');
    };
  }, [editingGeofence, mapRef]);

  // Update local geofences when prop changes
  useEffect(() => {
    const safeCurrentGeofences = (currentGeofences || []).filter(
      geofence => geofence && typeof geofence === 'object'
    );
    setGeofences(safeCurrentGeofences);
  }, [currentGeofences]);

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
      } else {
        // For polygon or rectangle
        geometry = {
          type: 'polygon',  // Treat rectangle as polygon
          points: newGeofence.polygon,
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
      const response = await createGeofence(payload);
      console.log('Geofence created successfully:', response);

      // Immediately call onSuccess to trigger parent refresh
      if (onSuccess) {
        await onSuccess();
      }

      // If this is used in a modal with showFormOnly=true, call onCancel to close the modal
      if (showFormOnly && onCancel) {
        onCancel();
      } else {
        setShowAddForm(false);
      }

      resetForm();
    } catch (error) {
      console.error('Error creating geofence:', error);
      alert(`Failed to create geofence: ${error.message || error}`);
    }
  };

  const handleShapeCreated = (coords, shape, radius = null) => {
    if (shape === 'Circle') {
      setNewGeofence(prev => ({
        ...prev,
        geometryType: 'circle',
        coordinates: { lat: coords.latitude, lng: coords.longitude },
        radius: radius || prev.radius,
        polygon: [],
      }));
    } else {
      // Rectangle or Polygon
      setNewGeofence(prev => ({
        ...prev,
        geometryType: shape.toLowerCase() === 'rectangle' ? 'rectangle' : 'polygon',
        polygon: coords,
        coordinates: { lat: 0, lng: 0 },
      }));
    }
  };

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
      } else {
        geometry = {
          type: 'polygon',
          points: newGeofence.polygon,
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

      resetForm();
      setEditingGeofence(null);

      // Call onSuccess if provided
      if (onSuccess) {
        await onSuccess();
      }

      // If this is used in a modal with showFormOnly=true, call onCancel to close the modal
      if (showFormOnly && onCancel) {
        onCancel();
      } else {
        setShowAddForm(false);
      }
    } catch (error) {
      console.error('Error updating geofence:', error);
      alert(`Failed to update geofence: ${error.message || error}`);
    }
  };

  // Reset the form
  const resetForm = () => {
    setNewGeofence({
      name: '',
      description: '',
      type: 'depot',
      geometryType: 'circle',
      radius: 500,
      coordinates: { lat: 37.7749, lng: -122.4194 },
      polygon: [],
      status: 'active',
    });
    setEditingGeofence(null);
  };

  return (
    <>
      {/* Show form when adding */}
      {showAddForm && (
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
                  ref={mapRef}
                >
                  <TileLayer
                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                    url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                  />
                  <GeomanControls onShapeCreated={handleShapeCreated} />

                  {/* Show polygon if drawn */}
                  {newGeofence.polygon.length > 0 && (
                    <Polygon
                      positions={newGeofence.polygon.map(p => [p.latitude, p.longitude])}
                      pathOptions={{ color: 'blue', weight: 2 }}
                    />
                  )}

                  {/* Show circle if circle type */}
                  {newGeofence.geometryType === 'circle' && newGeofence.coordinates.lat !== 0 && newGeofence.coordinates.lng !== 0 && (
                    <LeafletCircle
                      center={[newGeofence.coordinates.lat, newGeofence.coordinates.lng]}
                      radius={newGeofence.radius}
                      pathOptions={{ color: 'blue', weight: 2 }}
                    />
                  )}

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
                  {newGeofence.geometryType === 'circle' && newGeofence.coordinates.lat !== 0 && newGeofence.coordinates.lng !== 0 && (
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
                    <option value="restricted">Restricted</option>
                    <option value="boundary">Boundary</option>
                  </select>
                </div>

                {/* Geometry Type */}
                <div>
                  <label className="block text-sm font-medium mb-1">Shape</label>
                  <select
                    value={newGeofence.geometryType}
                    onChange={e => setNewGeofence({ ...newGeofence, geometryType: e.target.value })}
                    className="w-full px-3 py-2 rounded-md border border-input bg-background text-sm"
                  >
                    <option value="circle">Circle</option>
                    <option value="rectangle">Rectangle</option>
                    <option value="polygon">Polygon</option>
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

              {/* Conditional Fields */}
              {newGeofence.geometryType === 'circle' && (
                <>
                  {/* Radius Slider */}
                  <div>
                    <label className="block text-sm font-medium mb-1">
                      Radius: {newGeofence.radius} meters
                    </label>
                    <input
                      type="range"
                      min="50"
                      max="10000"
                      step="50"
                      value={newGeofence.radius}
                      onChange={e =>
                        setNewGeofence({ ...newGeofence, radius: parseInt(e.target.value) })
                      }
                      className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer slider"
                    />
                    <div className="flex justify-between text-xs text-muted-foreground mt-1">
                      <span>50m</span>
                      <span>10,000m</span>
                    </div>
                  </div>

                  {/* Coordinates */}
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
                </>
              )}
              {newGeofence.geometryType !== 'circle' && (
                <div className="text-sm text-muted-foreground">
                  Edit the {newGeofence.geometryType} shape directly on the map.
                </div>
              )}

              {/* Buttons */}
              <div className="flex gap-2 mt-6">
                <button
                  onClick={() => {
                    // Call onCancel if provided (for modal mode)
                    if (typeof onCancel === 'function') {
                      onCancel();
                    } else {
                      // Fallback for standalone mode
                      setShowAddForm(false);
                      setEditingGeofence(null);
                      resetForm();
                    }
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
      )}
    </>
  );
};

export default GeofenceManager;