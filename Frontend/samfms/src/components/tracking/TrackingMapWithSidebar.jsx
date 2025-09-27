import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  MapContainer,
  TileLayer,
  Marker,
  Popup,
  Circle,
  LayerGroup,
  FeatureGroup,
  useMap,
  Polygon
} from 'react-leaflet';
import '@geoman-io/leaflet-geoman-free';
import '@geoman-io/leaflet-geoman-free/dist/leaflet-geoman.css';

import {
  Search,
  Navigation,
  Car,
  Shield,
  Menu,
  Plus,
  Edit2,
  Trash2,
  Locate,
  LocateFixed,
  Crosshair,
  Layers,
  Save,
  X
} from 'lucide-react';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import { getVehicles } from '../../backend/api/vehicles';
import { listGeofences, deleteGeofence, addGeofence, updateGeofence } from '../../backend/api/geofences';
import { listLocations, getVehicleLocation } from '../../backend/api/locations';
import { getGeofence } from '../../backend/api/geofences';


// Fix for marker icons in React-Leaflet
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-shadow.png',
});

// Custom geofence icon
const createGeofenceIcon = type => {
  const color = type === 'depot' ? '#3b82f6' : type === 'restricted' ? '#ef4444' : '#8b5cf6';
  return L.divIcon({
    html: `<div style="background-color: ${color}; width: 20px; height: 20px; border-radius: 50%; border: 2px solid white; display: flex; align-items: center; justify-content: center;">
             <svg width="12" height="12" viewBox="0 0 24 24" fill="white">
               <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7z"/>
             </svg>
           </div>`,
    className: 'custom-geofence-marker',
    iconSize: [20, 20],
    iconAnchor: [10, 10],
  });
};

// Geofence path options based on type
const getGeofenceOptions = type => {
  switch (type) {
    case 'depot':
      return {
        color: '#3b82f6',
        fillColor: '#3b82f6',
        fillOpacity: 0.2,
        weight: 2,
      };
    case 'restricted':
      return {
        color: '#ef4444',
        fillColor: '#ef4444',
        fillOpacity: 0.3,
        weight: 2,
      };
    case 'boundary':
      return {
        color: '#22c55e',
        fillColor: '#22c55e',
        fillOpacity: 0.2,
        weight: 2,
      };
    default:
      return {
        color: '#8b5cf6',
        fillColor: '#8b5cf6',
        fillOpacity: 0.2,
        weight: 2,
      };
  }
};

// Map updater component to center on selected items
const MapUpdater = ({ center, zoom = 13 }) => {
  const map = useMap();

  useEffect(() => {
    if (center && center[0] && center[1]) {
      map.setView(center, zoom);
    }
  }, [center, zoom, map]);

  return null;
};

// Map controller for centering and follow mode
const MapController = ({ followMode, focusLocation }) => {
  const map = useMap();
  useEffect(() => {
    if (followMode && focusLocation) {
      map.setView([focusLocation.latitude, focusLocation.longitude], 15);
    }
  }, [followMode, focusLocation, map]);
  return null;
};

// Geoman Events Handler Component
// WORKING VERSION - Listen to individual layer events
const GeomanEventHandler = ({
  onGeofenceCreated,
  onGeofenceUpdated,
  onGeofenceDeleted,
  geofences,
  isEditingMode,
  setIsEditingMode
}) => {
  const map = useMap();
  const drawnLayersRef = useRef(new Map());
  const layerEventHandlers = useRef(new Map()); // Track layer event handlers for cleanup

  useEffect(() => {
    if (!map) return;

    // Handle creation (this works on map level)
    const handleCreate = (e) => {
      const layer = e.layer;
      const shape = e.shape;

      let coordinates, radius;

      if (shape === 'Circle') {
        const center = layer.getLatLng();
        radius = layer.getRadius();
        coordinates = { lat: center.lat, lng: center.lng };
      } else if (shape === 'Polygon' || shape === 'Rectangle') {
        const latlngs = layer.getLatLngs()[0];
        coordinates = latlngs.map(latlng => ({ lat: latlng.lat, lng: latlng.lng }));
      }

      onGeofenceCreated({
        shape: shape.toLowerCase(),
        coordinates,
        radius,
        layer
      });
    };

    // Only listen for create on map level
    map.on('pm:create', handleCreate);

    return () => {
      map.off('pm:create', handleCreate);
    };
  }, [map, onGeofenceCreated]);

  // Conditionally add/remove toolbar controls
  useEffect(() => {
    if (!map) return;

    if (isEditingMode) {
      map.pm.addControls({
        position: 'topright',
        drawCircle: true,
        drawMarker: false,
        drawPolygon: true,
        drawRectangle: true,
        editMode: true,
        dragMode: true,
        cutPolygon: false,
        drawPolyline: false,
      });
    } else {
      map.pm.removeControls();
    }

    return () => {
      map.pm.removeControls();
    };
  }, [map, isEditingMode]);

  // Handle existing geofences
  useEffect(() => {
    if (!map || !isEditingMode) {
      // Clean up layers and their event handlers
      layerEventHandlers.current.forEach((handlers, layerId) => {
        const layer = drawnLayersRef.current.get(layerId);
        if (layer) {
          // Remove layer event listeners
          layer.off('pm:markerdragend', handlers.markerdragend);
          layer.off('pm:dragend', handlers.dragend);
          layer.off('pm:vertexadded', handlers.vertexadded);
          layer.off('pm:vertexremoved', handlers.vertexremoved);
          layer.off('pm:remove', handlers.remove);
          
          // Disable PM and remove from map
          if (layer.pm) {
            layer.pm.disable();
          }
          if (map.hasLayer(layer)) {
            map.removeLayer(layer);
          }
        }
      });
      
      drawnLayersRef.current.clear();
      layerEventHandlers.current.clear();
      return;
    }

    // Clear existing layers first
    layerEventHandlers.current.forEach((handlers, layerId) => {
      const layer = drawnLayersRef.current.get(layerId);
      if (layer) {
        layer.off('pm:markerdragend', handlers.markerdragend);
        layer.off('pm:dragend', handlers.dragend);
        layer.off('pm:vertexadded', handlers.vertexadded);
        layer.off('pm:vertexremoved', handlers.vertexremoved);
        layer.off('pm:remove', handlers.remove);
        
        if (layer.pm) {
          layer.pm.disable();
        }
        if (map.hasLayer(layer)) {
          map.removeLayer(layer);
        }
      }
    });
    
    drawnLayersRef.current.clear();
    layerEventHandlers.current.clear();

    // Add geofences as editable layers
    geofences.forEach((geofence) => {
      let layer;

      if (geofence.shape === 'circle') {
        layer = L.circle(
          [geofence.coordinates.lat, geofence.coordinates.lng],
          { radius: geofence.radius }
        );
      } else if (geofence.shape === 'polygon') {
        layer = L.polygon(geofence.latlngs);
      }

      if (layer) {
        // Store geofence ID on layer
        layer.geofenceId = geofence.id;

        // Apply styling
        layer.setStyle(getGeofenceOptions(geofence.type));

        // Add to map
        layer.addTo(map);

        // Enable PM editing
        if (layer.pm) {
          layer.pm.enable({
            allowSelfIntersection: false,
            preventVertexEdit: false,
            preventMarkerRemoval: false,
          });

          // CRITICAL: Create event handlers for THIS specific layer
          const handleLayerEdit = (e) => {
            console.log("Layer edit detected for geofence:", geofence.id);
            
            let coordinates, radius;

            if (layer instanceof L.Circle) {
              console.log("Is circle");
              const center = layer.getLatLng();
              radius = layer.getRadius();
              coordinates = { lat: center.lat, lng: center.lng };
            } else if (layer instanceof L.Polygon) {
              console.log("Is polygon")
              const latlngs = layer.getLatLngs()[0];
              coordinates = latlngs.map(latlng => ({ lat: latlng.lat, lng: latlng.lng }));
            }

            onGeofenceUpdated(geofence.id, {
              coordinates,
              radius
            });
          };

          const handleLayerRemove = (e) => {
            console.log("Layer remove detected for geofence:", geofence.id);
            onGeofenceDeleted(geofence.id);
          };

          // Add event listeners to the individual layer
          layer.on('pm:markerdragend', handleLayerEdit);
          layer.on('pm:dragend', handleLayerEdit);
          layer.on('pm:vertexadded', handleLayerEdit);
          layer.on('pm:vertexremoved', handleLayerEdit);
          layer.on('pm:remove', handleLayerRemove);

          // Store handlers for cleanup
          layerEventHandlers.current.set(geofence.id, {
            markerdragend: handleLayerEdit,
            dragend: handleLayerEdit,
            vertexadded: handleLayerEdit,
            vertexremoved: handleLayerEdit,
            remove: handleLayerRemove
          });

          console.log(`Enabled PM editing and events for geofence ${geofence.id}`);
        }

        // Store layer reference
        drawnLayersRef.current.set(geofence.id, layer);
      }
    });

    console.log(`Added ${drawnLayersRef.current.size} editable geofences with individual event handlers`);

  }, [map, geofences, isEditingMode, onGeofenceUpdated, onGeofenceDeleted]);

  return null;
};

// Geofence Creation Modal
const GeofenceCreationModal = ({ isOpen, onClose, onSave, shapeData }) => {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [type, setType] = useState('boundary');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!name.trim()) return;

    onSave({
      name: name.trim(),
      description: description.trim(),
      type,
      ...shapeData
    });

    // Reset form
    setName('');
    setDescription('');
    setType('boundary');
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[1000]">
      <div className="bg-white dark:bg-gray-800 rounded-lg p-6 w-96 max-w-[90vw]">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">Create Geofence</h3>
          <button
            onClick={onClose}
            className="p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded text-gray-600 dark:text-gray-400"
          >
            <X size={20} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1 text-gray-700 dark:text-gray-300">Name</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
              placeholder="Enter geofence name"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1 text-gray-700 dark:text-gray-300">Description</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
              placeholder="Enter description (optional)"
              rows={3}
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1 text-gray-700 dark:text-gray-300">Type</label>
            <select
              value={type}
              onChange={(e) => setType(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
            >
              <option value="boundary">Boundary</option>
              <option value="depot">Depot</option>
              <option value="restricted">Restricted</option>
            </select>
          </div>

          <div className="flex justify-end space-x-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-md"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 flex items-center space-x-2"
            >
              <Save size={16} />
              <span>Save Geofence</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

const calculateCenter = (latlngs) => {
  let latSum = 0, lngSum = 0;
  latlngs.forEach(([lat, lng]) => { latSum += lat; lngSum += lng; });
  return [latSum / latlngs.length, lngSum / latlngs.length];
};

const TrackingMapWithSidebar = () => {
  const [activeTab, setActiveTab] = useState('vehicles');
  const [vehicles, setVehicles] = useState([]);
  const [locations, setLocations] = useState([]);
  const [followMode, setFollowMode] = useState(false);
  const [mapType, setMapType] = useState('streets');
  const [focusLocation, setFocusLocation] = useState(null);
  const [geofences, setGeofences] = useState([]);
  const [showGeofences, setShowGeofences] = useState(true);
  const [showVehicles, setShowVehicles] = useState(true);
  const [showLocations, setShowLocations] = useState(true);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [mapCenter, setMapCenter] = useState([37.7749, -122.4194]);
  const [selectedItem, setSelectedItem] = useState(null);
  const [userLocation, setUserLocation] = useState(null);
  const [showUserLocation, setShowUserLocation] = useState(false);

  // New states for Geoman functionality
  const [isEditingMode, setIsEditingMode] = useState(false);
  const [pendingGeofence, setPendingGeofence] = useState(null);
  const [showGeofenceModal, setShowGeofenceModal] = useState(false);
  const [showAddGeofenceModal, setShowAddGeofenceModal] = useState(false);
  const [editingGeofence, setEditingGeofence] = useState(null);

  // Address search state
  const [addressSearch, setAddressSearch] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [searchSuggestions, setSearchSuggestions] = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(false);

  const searchContainerRef = useRef(null);
  const mapRef = useRef(null);

  // Toggle follow mode
  const toggleFollowMode = useCallback(() => {
    setFollowMode(prev => !prev);
  }, []);

  // Get map layer based on type
  const getMapLayer = () => {
    switch (mapType) {
      case 'satellite':
        return {
          url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
          attribution:
            'Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community',
        };
      case 'terrain':
        return {
          url: 'https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png',
          attribution:
            'Map data: &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors, <a href="http://viewfinderpanoramas.org">SRTM</a> | Map style: &copy; <a href="https://opentopomap.org">OpenTopoMap</a>',
        };
      case 'streets':
      default:
        return {
          url: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
          attribution:
            '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        };
    }
  };


  // Cleanup timeout on unmount
  useEffect(() => {
    // Handle click outside search bar to hide suggestions
    const handleClickOutside = event => {
      if (searchContainerRef.current && !searchContainerRef.current.contains(event.target)) {
        setShowSuggestions(false);
      }
    };

    // Close sidebar with Escape key
    const handleKeyDown = event => {
      if (event.key === 'Escape' && !sidebarCollapsed) {
        setSidebarCollapsed(true);
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    document.addEventListener('mousedown', handleClickOutside);

    return () => {
      if (window.addressSearchTimeout) {
        clearTimeout(window.addressSearchTimeout);
      }
      document.removeEventListener('keydown', handleKeyDown);
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [sidebarCollapsed]);

  // Get user's location on mount
  useEffect(() => {
    const getUserLocation = () => {
      if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
          position => {
            const { latitude, longitude } = position.coords;
            const locationArray = [latitude, longitude];
            setUserLocation(locationArray);
            setMapCenter(locationArray);
          },
          error => {
            console.warn('Could not get user location:', error);
            // Keep default location (San Francisco) if geolocation fails
          },
          {
            enableHighAccuracy: true,
            timeout: 10000,
            maximumAge: 300000, // 5 minutes
          }
        );
      } else {
        console.warn('Geolocation is not supported by this browser.');
      }
    };

    getUserLocation();
  }, []);

  // Load vehicles data
  const loadVehicles = useCallback(async () => {
    try {
      setLoading(true);

      // Load vehicles
      const vehiclesResponse = await getVehicles({ limit: 100 });

      const vehiclesData =
        vehiclesResponse.data?.data?.vehicles ||
        vehiclesResponse.vehicles ||
        vehiclesResponse.data?.vehicles ||
        [];

      // Only include vehicles that have actual GPS location data
      const transformedVehicles = vehiclesData
        .map(vehicle => {
          const vehicleId = vehicle.id || vehicle.vehicle_id;
          return {
            id: vehicleId,
            name: vehicle.vehicle_name || vehicle.name || `Vehicle ${vehicleId}`,
            make: vehicle.make || 'Unknown',
            model: vehicle.model || 'Unknown',
            status: vehicle.status || 'unknown',
            license_plate: vehicle.license_plate || 'N/A',
          };
        });

      setVehicles(transformedVehicles);
    } catch (err) {
      console.error('Error loading vehicles:', err);
      setError('Failed to load vehicles');
    }
  }, []);

  // Load geofences data
  const loadGeofences = useCallback(async () => {
    try {
      setLoading(true);

      const response = await listGeofences();
      console.log("Geofences response:", response.data?.data || response.data || response);

      const geofencesData = response.data?.data || response.data || response || [];

      const transformedGeofences = geofencesData
        .map(geofence => {
          if (!geofence.geometry) return null;

          // Circle geofence
          if (geofence.geometry.type === 'Point' && geofence.geometry.coordinates) {
            return {
              id: geofence.id,
              name: geofence.name,
              description: geofence.description,
              type: geofence.type,
              shape: 'circle',
              coordinates: {
                lat: geofence.geometry.coordinates[1],
                lng: geofence.geometry.coordinates[0],
              },
              radius: geofence.geometry.radius || 1000,
              status: geofence.status,
            };
          }

          // Polygon geofence
          if (geofence.geometry.type === 'Polygon' && geofence.geometry.coordinates?.[0]?.length) {
            const latlngs = geofence.geometry.coordinates[0].map(([lng, lat]) => [lat, lng]);
            return {
              id: geofence.id,
              name: geofence.name,
              description: geofence.description,
              type: geofence.type,
              shape: 'polygon',
              latlngs,
              status: geofence.status,
            };
          }

          return null;
        })
        .filter(Boolean);

      setGeofences(transformedGeofences);
    } catch (err) {
      console.error('Error loading geofences:', err);
      setError('Failed to load geofences');
    } finally {
      setLoading(false);
    }
  }, []);

  // Handle geofence creation from map drawing
  const handleGeofenceCreated = useCallback((shapeData) => {
    setPendingGeofence(shapeData);
    setShowGeofenceModal(true);
  }, []);

  // Handle saving new geofence
  const handleSaveGeofence = useCallback(async (geofenceData) => {
    try {
      const { name, description, type, shape, coordinates, radius } = geofenceData;

      let geometry;
      if (shape === 'circle') {
        geometry = {
          type: 'Point',
          coordinates: [coordinates.lng, coordinates.lat],
          radius: radius
        };
      } else if (shape === 'polygon' || shape === 'rectangle') {
        let points = coordinates.map(coord => [coord.lng, coord.lat]);
        if (points[0][0] !== points[points.length - 1][0] || points[0][1] !== points[points.length - 1][1]) {
          points.push(points[0]);
        }
        geometry = {
          type: 'Polygon',
          coordinates: [points]
        };
      }

      const payload = {
        name,
        description,
        type,
        geometry,
        status: 'active'
      };

      const response = await addGeofence(payload);
      console.log("Creation for geofence response", response.data.data)
      await loadGeofences();

      setShowGeofenceModal(false);
      setPendingGeofence(null);

      // Remove the temporary layer if it exists
      if (pendingGeofence?.layer && mapRef.current) {
        mapRef.current.removeLayer(pendingGeofence.layer);
      }

    } catch (error) {
      console.error('Error creating geofence:', error);
      alert('Failed to create geofence. Please try again.');
    }
  }, [pendingGeofence, loadGeofences]);

  // Handle geofence update from map editing
  const handleGeofenceUpdated = useCallback(async (geofenceId, updateData) => {
    try {
      console.log("Entered editing function", geofenceId, updateData)
      const geofence = geofences.find(g => g.id === geofenceId);
      console.log("Geofence found: ", geofence)
      if (!geofence) return;

      let geometry;
      if (geofence.shape === 'circle') {
        geometry = {
          type: 'Point',
          coordinates: [updateData.coordinates.lng, updateData.coordinates.lat],
          radius: updateData.radius
        };
      } else if (geofence.shape === 'polygon') {
        let points = updateData.coordinates.map(coord => [coord.lng, coord.lat]);
        if (points[0][0] !== points[points.length - 1][0] || points[0][1] !== points[points.length - 1][1]) {
          points.push(points[0]);
        }
        geometry = {
          type: 'Polygon',
          coordinates: [points]
        };
      }

      const payload = {
        name: geofence.name,
        description: geofence.description,
        type: geofence.type,
        geometry,
        status: geofence.status
      };

      const response = await updateGeofence(geofenceId, payload);
      console.log("Response for updating geofence", response.data.data)
      await loadGeofences(); // Reload geofences
    } catch (error) {
      console.error('Error updating geofence:', error);
      alert('Failed to update geofence. Please try again.');
    }
  }, [geofences, loadGeofences]);

  // Handle geofence deletion from map
  const handleGeofenceDeleted = useCallback(async (geofenceId) => {
    try {
      await deleteGeofence(geofenceId);
      await loadGeofences(); // Reload geofences
    } catch (error) {
      console.error('Error deleting geofence:', error);
      alert('Failed to delete geofence. Please try again.');
    }
  }, [loadGeofences]);

  // Handle geofence editing
  const handleEditGeofence = (geofence, event) => {
    console.log("handleEditGeofence entered", geofence, event);
    event.stopPropagation();
    setIsEditingMode(true);
    if (geofence.shape === 'circle') {
      setMapCenter([geofence.coordinates.lat, geofence.coordinates.lng]);
    } else {
      setMapCenter(calculateCenter(geofence.latlngs));
    }
  };

  // Handle geofence deletion
  const handleDeleteGeofence = async (geofenceId, event) => {
    event.stopPropagation();

    if (window.confirm('Are you sure you want to delete this geofence?')) {
      try {
        const response = await deleteGeofence(geofenceId);
        console.log("Geofence deletion resposne", response.data.data);
        setGeofences(prev => prev.filter(g => g.id !== geofenceId));
        await loadGeofences();
      } catch (error) {
        console.error('Error deleting geofence:', error);
        alert('Failed to delete geofence. Please try again.');
        await loadGeofences();
      }
    }
  };

  // Toggle edit mode
  const toggleEditMode = () => {
    setIsEditingMode(prev => !prev);
  };

  // Load geofences on component mount
  useEffect(() => {
    loadGeofences();
  }, [loadGeofences]);

  const currentMapLayer = getMapLayer();


  // Load live locations data with auto-refresh
  useEffect(() => {
    const loadLocations = async () => {
      try {
        const response = await listLocations();
        const locationsData = response.data?.data || [];
        setLocations(locationsData);

        // Auto-focus on first location if follow mode is enabled and we have locations
        if (followMode && locationsData.length > 0 && !focusLocation) {
          setFocusLocation(locationsData[0]);
        }
      } catch (err) {
        console.error('Failed to load locations:', err);
      }
    };

    loadLocations();
    const interval = setInterval(loadLocations, 2000); // Refresh every 5 seconds
    return () => clearInterval(interval);
  }, [followMode, focusLocation]);

  // Load data on mount
  useEffect(() => {
    const loadData = async () => {
      await Promise.all([loadVehicles(), loadGeofences()]);
    };
    loadData();
  }, [loadVehicles, loadGeofences]);

  // Filter items based on search term
  const filteredItems =
    activeTab === 'vehicles'
      ? vehicles.filter(
        vehicle =>
          (vehicle.name?.toLowerCase() || '').includes(searchTerm.toLowerCase()) ||
          (vehicle.make?.toLowerCase() || '').includes(searchTerm.toLowerCase()) ||
          (vehicle.model?.toLowerCase() || '').includes(searchTerm.toLowerCase()) ||
          (vehicle.license_plate?.toLowerCase() || '').includes(searchTerm.toLowerCase())
      )
      : geofences.filter(
        geofence =>
          (geofence.name?.toLowerCase() || '').includes(searchTerm.toLowerCase()) ||
          (geofence.description?.toLowerCase() || '').includes(searchTerm.toLowerCase()) ||
          (geofence.type?.toLowerCase() || '').includes(searchTerm.toLowerCase())
      );

  // Handle geofence changes from the GeofenceManager
  const handleGeofenceChange = useCallback(async updatedGeofences => {
    // We now rely primarily on server refresh through onSuccess
    // This is kept for backward compatibility but simplified
    console.log('Geofences changed, relying on server refresh');
  }, []);

  // Enhanced function to handle successful geofence operations
  const handleGeofenceSuccess = useCallback(async () => {
    // Reload geofences to show the latest data from the server
    console.log('Refreshing geofences after successful operation');
    await loadGeofences();

    // Close modal
    //setShowAddGeofenceModal(false);
    //setEditingGeofence(null);
  }, [loadGeofences]);

  // Handle item selection and map centering
  const handleItemSelect = async (item) => {
    console.log("Item selected", item);
    console.log("Item id: ", item.id)
    setSelectedItem(item);

    try {
      const geofence = await getGeofence(item.id);
      console.log("Geofence response: ", geofence)
      if (geofence === null) {
        const vehicleData = await getVehicleLocation(item.id);
        console.log("Full response:", vehicleData);

        const { latitude, longitude } = vehicleData;
        setMapCenter([latitude, longitude]);
      } else {
        if (geofence.geometry.type === 'Point') {
          setMapCenter([geofence.geometry.coordinates[1], geofence.geometry.coordinates[0]]);
        } else if (geofence.geometry.type === 'Polygon') {
          const coords = geofence.geometry.coordinates[0].map(([lng, lat]) => [lat, lng]);
          setMapCenter(calculateCenter(coords));
        }
      }

    } catch (err) {
      console.error("Failed to fetch vehicle location:", err);
    }
  };


  // Handle live location selection
  const handleLocationSelect = location => {
    setFocusLocation(location);
    setMapCenter([location.latitude, location.longitude]);
    setFollowMode(true); // Enable follow mode when selecting a live location
  };

  // Address search functionality
  const handleAddressSearch = async query => {
    if (!query.trim()) {
      setSearchSuggestions([]);
      setShowSuggestions(false);
      return;
    }

    setIsSearching(true);
    try {
      // Using Nominatim (OpenStreetMap) geocoding service
      const response = await fetch(
        `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(
          query
        )}&limit=5&addressdetails=1`
      );

      if (response.ok) {
        const data = await response.json();
        const suggestions = data.map(item => ({
          display_name: item.display_name,
          lat: parseFloat(item.lat),
          lon: parseFloat(item.lon),
          place_id: item.place_id,
        }));

        setSearchSuggestions(suggestions);
        setShowSuggestions(suggestions.length > 0);
      }
    } catch (error) {
      console.error('Error searching address:', error);
      setSearchSuggestions([]);
    } finally {
      setIsSearching(false);
    }
  };

  // Handle address selection from suggestions
  const handleAddressSelect = suggestion => {
    setMapCenter([suggestion.lat, suggestion.lon]);
    setAddressSearch(suggestion.display_name);
    setShowSuggestions(false);
    setSearchSuggestions([]);
    // Keep the search bar expanded after selection so user can see the selected address
  };

  // Handle input change with debounced search
  const handleAddressInputChange = value => {
    setAddressSearch(value);

    // Clear previous timeout
    if (window.addressSearchTimeout) {
      clearTimeout(window.addressSearchTimeout);
    }

    // Set new timeout for search
    window.addressSearchTimeout = setTimeout(() => {
      handleAddressSearch(value);
    }, 300);
  };

  // Handle location button click
  const handleLocationButtonClick = () => {
    if (userLocation && userLocation[0] && userLocation[1]) {
      setMapCenter([userLocation[0], userLocation[1]]);
      setShowUserLocation(!showUserLocation);
    } else {
      // Try to get location again if we don't have it
      if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
          position => {
            const { latitude, longitude } = position.coords;
            const locationArray = [latitude, longitude];
            setUserLocation(locationArray);
            setMapCenter(locationArray);
            setShowUserLocation(true);
          },
          error => {
            console.warn('Could not get user location:', error);
            alert('Unable to get your location. Please check your browser permissions.');
          },
          {
            enableHighAccuracy: true,
            timeout: 10000,
            maximumAge: 300000,
          }
        );
      }
    }
  };

  if (loading && vehicles.length === 0 && geofences.length === 0) {
    return (
      <div
        className="w-full flex items-center justify-center"
        style={{ height: 'calc(100vh - 70px)' }}
      >
        <div className="flex items-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mr-3"></div>
          <span>Loading map data...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div
        className="w-full flex items-center justify-center p-6"
        style={{ height: 'calc(100vh - 70px)' }}
      >
        <div className="bg-destructive/10 border border-destructive text-destructive px-4 py-3 rounded max-w-md w-full text-center">
          <p>{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full" style={{ height: 'calc(100vh - 70px)' }}>
      <div className="relative h-full">
        {/* Map - Full Width */}
        <div className="w-full h-full border border-border overflow-hidden relative">
          {/* Floating Address Search Bar and Toggle Buttons */}
          <div className="absolute top-4 left-4 right-4 z-[1000]">
            <div className="flex items-start gap-3">
              {/* Location Button */}
              <button
                onClick={handleLocationButtonClick}
                className={`flex items-center justify-center rounded-lg shadow-lg border px-3 py-2 h-10 transition-all duration-300 ease-in-out hover:scale-105 active:scale-95 ${showUserLocation
                  ? 'bg-blue-500 hover:bg-blue-600 border-blue-600 text-white'
                  : 'bg-white hover:bg-gray-50 border-gray-300 text-gray-600 dark:bg-gray-800 dark:hover:bg-gray-700 dark:border-gray-600 dark:text-gray-300'
                  }`}
                title="Go to my location"
              >
                {showUserLocation ? (
                  <LocateFixed className="w-4 h-4 transition-transform duration-200" />
                ) : (
                  <Locate className="w-4 h-4 transition-transform duration-200" />
                )}
              </button>

              {/* Search Bar Container */}
              <div className="flex-1" ref={searchContainerRef}>
                <div className="transition-all duration-300 ease-in-out">
                  <div className="space-y-2">
                    {/* Search bar */}
                    <div className="relative flex items-center bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg shadow-lg transition-all duration-300 ease-in-out h-10">
                      <Search className="absolute left-3 text-gray-500 dark:text-gray-400 w-4 h-4 transition-colors duration-200" />
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
                        className="w-full pl-10 pr-12 py-3 rounded-lg border-0 focus:outline-none focus:ring-2 focus:ring-blue-500 bg-transparent text-gray-900 dark:text-gray-100 text-sm placeholder-gray-500 dark:placeholder-gray-400 transition-all duration-200"
                        onKeyDown={e => {
                          if (e.key === 'Escape') {
                            setAddressSearch('');
                            setShowSuggestions(false);
                            setSearchSuggestions([]);
                          }
                        }}
                      />
                      {/* Loading spinner */}
                      {isSearching && (
                        <div className="absolute right-3 transition-opacity duration-200">
                          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-500"></div>
                        </div>
                      )}
                    </div>

                    {/* Search Suggestions Dropdown */}
                    {showSuggestions && searchSuggestions.length > 0 && (
                      <div className="bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg shadow-lg max-h-60 overflow-y-auto z-[1001] animate-in fade-in slide-in-from-top-1 duration-200">
                        {searchSuggestions.map((suggestion, index) => (
                          <button
                            key={suggestion.place_id}
                            onClick={() => handleAddressSelect(suggestion)}
                            className="w-full text-left px-4 py-3 hover:bg-gray-50 dark:hover:bg-gray-700 transition-all duration-200 border-b border-gray-100 dark:border-gray-600 last:border-b-0 focus:outline-none focus:bg-gray-50 dark:focus:bg-gray-700 transform hover:translate-x-1"
                            style={{ animationDelay: `${index * 50}ms` }}
                          >
                            <div className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate transition-colors duration-200">
                              {suggestion.display_name}
                            </div>
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* Control Buttons Container - Fixed height regardless of search state */}
              <div className="flex items-center gap-2 h-10">
                {/* Live Locations Toggle */}
                <button
                  onClick={() => setShowLocations(!showLocations)}
                  className={`flex items-center gap-2 px-3 py-2 h-10 rounded-lg shadow-lg border transition-all duration-300 ease-in-out hover:scale-105 active:scale-95 ${showLocations
                    ? 'bg-orange-500 hover:bg-orange-600 border-orange-600 text-white'
                    : 'bg-white hover:bg-gray-50 border-gray-300 text-gray-600 dark:bg-gray-800 dark:hover:bg-gray-700 dark:border-gray-600 dark:text-gray-300'
                    }`}
                  title={`${showLocations ? 'Hide' : 'Show'} Live Locations`}
                >
                  <Navigation className="w-4 h-4 transition-transform duration-200" />
                  <span className="text-sm font-medium hidden sm:inline">Live</span>
                </button>

                {/* Vehicles Toggle */}
                <button
                  onClick={() => setShowVehicles(!showVehicles)}
                  className={`flex items-center gap-2 px-3 py-2 h-10 rounded-lg shadow-lg border transition-all duration-300 ease-in-out hover:scale-105 active:scale-95 ${showVehicles
                    ? 'bg-green-500 hover:bg-green-600 border-green-600 text-white'
                    : 'bg-white hover:bg-gray-50 border-gray-300 text-gray-600 dark:bg-gray-800 dark:hover:bg-gray-700 dark:border-gray-600 dark:text-gray-300'
                    }`}
                  title={`${showVehicles ? 'Hide' : 'Show'} Vehicles`}
                >
                  <Car className="w-4 h-4 transition-transform duration-200" />
                  <span className="text-sm font-medium hidden sm:inline">Vehicles</span>
                </button>

                {/* Geofences Toggle */}
                <button
                  onClick={() => setShowGeofences(!showGeofences)}
                  className={`flex items-center gap-2 px-3 py-2 h-10 rounded-lg shadow-lg border transition-all duration-300 ease-in-out hover:scale-105 active:scale-95 ${showGeofences
                    ? 'bg-blue-500 hover:bg-blue-600 border-blue-600 text-white'
                    : 'bg-white hover:bg-gray-50 border-gray-300 text-gray-600 dark:bg-gray-800 dark:hover:bg-gray-700 dark:border-gray-600 dark:text-gray-300'
                    }`}
                  title={`${showGeofences ? 'Hide' : 'Show'} Geofences`}
                >
                  <Shield className="w-4 h-4 transition-transform duration-200" />
                  <span className="text-sm font-medium hidden sm:inline">Geofences</span>
                </button>

                {/* Follow Mode Toggle */}
                <button
                  onClick={toggleFollowMode}
                  className={`flex items-center gap-2 px-3 py-2 h-10 rounded-lg shadow-lg border transition-all duration-300 ease-in-out hover:scale-105 active:scale-95 ${followMode
                    ? 'bg-purple-500 hover:bg-purple-600 border-purple-600 text-white'
                    : 'bg-white hover:bg-gray-50 border-gray-300 text-gray-600 dark:bg-gray-800 dark:hover:bg-gray-700 dark:border-gray-600 dark:text-gray-300'
                    }`}
                  title={`${followMode ? 'Disable' : 'Enable'} Follow Mode`}
                >
                  <Crosshair className="w-4 h-4 transition-transform duration-200" />
                  <span className="text-sm font-medium hidden sm:inline">Follow</span>
                </button>

                {/* Sidebar Toggle Button */}
                <button
                  onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
                  className="flex items-center justify-center bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 shadow-lg px-3 py-2 h-10 hover:bg-gray-50 dark:hover:bg-gray-700 transition-all duration-300 ease-in-out hover:scale-105 active:scale-95 rounded-lg"
                  title={sidebarCollapsed ? 'Show Sidebar' : 'Hide Sidebar'}
                >
                  <Menu
                    className={`w-4 h-4 text-gray-600 dark:text-gray-300 transition-transform duration-300 ${sidebarCollapsed ? 'rotate-0' : 'rotate-180'
                      }`}
                  />
                </button>
              </div>
            </div>
          </div>

          <MapContainer
            center={mapCenter}
            zoom={13}
            style={{ height: '100%', width: '100%' }}
            zoomControl={false}
            ref={mapRef}
          >
            <TileLayer
              attribution={currentMapLayer.attribution}
              url={currentMapLayer.url}
            />
            <MapController followMode={followMode} focusLocation={focusLocation} />
            <MapUpdater center={mapCenter} />

            <GeomanEventHandler
              onGeofenceCreated={handleGeofenceCreated}
              onGeofenceUpdated={handleGeofenceUpdated}
              onGeofenceDeleted={handleGeofenceDeleted}
              geofences={geofences}
              isEditingMode={isEditingMode}
              setIsEditingMode={setIsEditingMode}
            />

            {/* Live vehicle locations - Main feature like TrackingMap */}
            {showLocations && locations.map(loc => (
              <Marker
                key={loc.id}
                position={[loc.latitude, loc.longitude]}
                icon={L.divIcon({
                  className: 'custom-location-icon',
                  html: `<div style="background:#ff9800;width:16px;height:16px;border-radius:50%;border:3px solid white;box-shadow:0 2px 8px rgba(0,0,0,0.3);"></div>`,
                  iconSize: [22, 22],
                  iconAnchor: [11, 11],
                })}
                eventHandlers={{
                  click: () => handleLocationSelect(loc),
                }}
              >
                <Popup>
                  <div className="text-sm">
                    <h4 className="font-medium">Vehicle {loc.vehicle_id}</h4>
                    <p><strong>Speed:</strong> {loc.speed} km/h</p>
                    <p><strong>Heading:</strong> {loc.heading}°</p>
                    <p><strong>Updated:</strong> {new Date(loc.updated_at).toLocaleString()}</p>
                    <p className="text-xs text-muted-foreground mt-2">
                      Lat: {loc.latitude.toFixed(6)}, Lng: {loc.longitude.toFixed(6)}
                    </p>
                  </div>
                </Popup>
              </Marker>
            ))}

            {/* User Location Marker */}
            {showUserLocation && userLocation && userLocation[0] && userLocation[1] && (
              <Marker
                position={[userLocation[0], userLocation[1]]}
                icon={L.divIcon({
                  className: 'user-location-marker',
                  html: `<div style="
                    width: 16px; 
                    height: 16px; 
                    background: #3b82f6; 
                    border: 2px solid white; 
                    border-radius: 50%; 
                    box-shadow: 0 2px 8px rgba(0,0,0,0.3);
                    position: relative;
                    top: -8px;
                    left: -8px;
                  "></div>`,
                  iconSize: [16, 16],
                  iconAnchor: [8, 8],
                })}
              >
                <Popup>
                  <div className="text-sm">
                    <h4 className="font-medium">Your Location</h4>
                    <p className="text-muted-foreground">Current position</p>
                  </div>
                </Popup>
              </Marker>
            )}

            {/* Geofence Circles and Polygons - Always show when enabled */}
            {showGeofences && !isEditingMode && geofences.length > 0 && (
              <LayerGroup>
                {geofences.map(geofence => (
                  <FeatureGroup
                    key={`geofence-group-${geofence.id}`}
                    pathOptions={getGeofenceOptions(geofence.type)}
                  >
                    <Popup>
                      <div className="text-sm">
                        <h4 className="font-medium">{geofence.name}</h4>
                        <p className="text-muted-foreground">{geofence.description}</p>
                        <div className="flex items-center mt-1">
                          <div
                            className={`w-2 h-2 rounded-full mr-2 ${geofence.type === 'depot'
                              ? 'bg-blue-500'
                              : geofence.type === 'restricted'
                                ? 'bg-red-500'
                                : geofence.type === 'boundary'
                                  ? 'bg-green-500'
                                  : 'bg-purple-500'
                              }`}
                          ></div>
                          <span className="text-xs capitalize">{geofence.type}</span>
                        </div>
                        {geofence.radius && (
                          <p className="text-xs text-muted-foreground mt-1">
                            Radius: {geofence.radius}m
                          </p>
                        )}
                      </div>
                    </Popup>

                    {/* Render circle geofences as before */}
                    {geofence.shape === 'circle' && (
                      <>
                        <Circle
                          center={[geofence.coordinates.lat, geofence.coordinates.lng]}
                          radius={geofence.radius || 1000}
                        />
                        {activeTab === 'geofences' && (
                          <Marker
                            position={[geofence.coordinates.lat, geofence.coordinates.lng]}
                            icon={createGeofenceIcon(geofence.type)}
                          />
                        )}
                      </>
                    )}

                    {/* Render polygon geofences */}
                    {geofence.shape === 'polygon' && (
                      <Polygon
                        positions={geofence.latlngs} // array of [lat, lng]
                        pathOptions={getGeofenceOptions(geofence.type)}
                      />
                    )}
                  </FeatureGroup>
                ))}
              </LayerGroup>
            )}

          </MapContainer>

          {/* Map Controls - Bottom Right */}
          <div className="absolute bottom-4 right-4 flex flex-col gap-2 z-[1000]">
            <div className="bg-white dark:bg-gray-800 p-2 rounded-lg shadow-lg border border-gray-300 dark:border-gray-600">
              <button
                className={`p-2 rounded-md w-8 h-8 flex items-center justify-center transition-all duration-200 ${mapType === 'streets'
                  ? 'bg-primary text-primary-foreground'
                  : 'hover:bg-gray-100 dark:hover:bg-gray-700'
                  }`}
                onClick={() => setMapType('streets')}
                title="Street map"
              >
                <Navigation size={16} />
              </button>
              <button
                className={`p-2 rounded-md w-8 h-8 flex items-center justify-center mt-1 transition-all duration-200 ${mapType === 'satellite'
                  ? 'bg-primary text-primary-foreground'
                  : 'hover:bg-gray-100 dark:hover:bg-gray-700'
                  }`}
                onClick={() => setMapType('satellite')}
                title="Satellite map"
              >
                <Layers size={16} />
              </button>
              <button
                className={`p-2 rounded-md w-8 h-8 flex items-center justify-center mt-1 transition-all duration-200 ${mapType === 'terrain'
                  ? 'bg-primary text-primary-foreground'
                  : 'hover:bg-gray-100 dark:hover:bg-gray-700'
                  }`}
                onClick={() => setMapType('terrain')}
                title="Terrain map"
              >
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
                  <path d="m2 22 10-10 10 10M12 12V3" />
                  <path d="m9 6 3-3 3 3" />
                </svg>
              </button>
            </div>
          </div>
        </div>

        {/* Sidebar Backdrop - More prominent on mobile */}
        {!sidebarCollapsed && (
          <div
            className="absolute inset-0 bg-black bg-opacity-10 sm:bg-opacity-10 z-[998] transition-opacity duration-300"
            onClick={() => setSidebarCollapsed(true)}
          />
        )}

        {/* Sidebar - Overlay on top of map */}
        <div
          className={`absolute top-20 right-4 w-full sm:w-80 h-[calc(100vh-174px)] bg-card border border-border shadow-xl rounded-2xl z-[999] transition-all duration-500 ease-in-out transform ${sidebarCollapsed ? 'translate-x-full opacity-0' : 'translate-x-0 opacity-100'
            }`}
        >
          <div className="flex flex-col h-full p-4 animate-in slide-in-from-right-4 duration-300">
            {/* Tabs */}
            <div className="flex border-b border-border mb-4">
              <button
                className={`flex-1 px-4 py-2 text-sm font-medium border-b-2 transition-all duration-300 ease-in-out ${activeTab === 'vehicles'
                  ? 'border-primary text-primary bg-primary/5 transform scale-105'
                  : 'border-transparent text-muted-foreground hover:text-foreground hover:border-border hover:bg-accent/50'
                  }`}
                onClick={() => {
                  setActiveTab('vehicles');
                  setSearchTerm('');
                  setSelectedItem(null);
                }}
              >
                <Car
                  className={`w-4 h-4 inline mr-2 transition-transform duration-200 ${activeTab === 'vehicles' ? 'scale-110' : ''
                    }`}
                />
                Vehicles ({vehicles.length})
              </button>
              <button
                className={`flex-1 px-4 py-2 text-sm font-medium border-b-2 transition-all duration-300 ease-in-out ${activeTab === 'geofences'
                  ? 'border-primary text-primary bg-primary/5 transform scale-105'
                  : 'border-transparent text-muted-foreground hover:text-foreground hover:border-border hover:bg-accent/50'
                  }`}
                onClick={() => {
                  setActiveTab('geofences');
                  setSearchTerm('');
                  setSelectedItem(null);
                }}
              >
                <Shield
                  className={`w-4 h-4 inline mr-2 transition-transform duration-200 ${activeTab === 'geofences' ? 'scale-110' : ''
                    }`}
                />
                Geofences ({geofences.length})
              </button>
            </div>

            {/* Search */}
            <div className="relative mb-4">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground w-4 h-4 transition-colors duration-200" />
              <input
                type="text"
                placeholder={`Search ${activeTab}...`}
                value={searchTerm}
                onChange={e => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary transition-all duration-200 rounded-md"
              />
            </div>

            {/* Edit Mode Button - Only show when geofences tab is active */}
            {activeTab === 'geofences' && (
              <div className="mb-4 animate-in fade-in slide-in-from-top-2 duration-300">
                <button
                  onClick={toggleEditMode}
                  className={`w-full flex items-center justify-center gap-2 px-4 py-2 text-sm font-medium rounded-md hover:scale-105 active:scale-95 transition-all duration-300 ease-in-out ${isEditingMode
                    ? 'bg-red-600 text-white hover:bg-red-700'
                    : 'bg-blue-600 text-white hover:bg-blue-700'
                    }`}
                >
                  <Edit2 className="w-4 h-4 transition-transform duration-200" />
                  {isEditingMode ? 'Exit Edit Mode' : 'Edit Geofences on Map'}
                </button>
              </div>
            )}

            {/* Live Locations Summary - Show when locations are available */}
            {locations.length > 0 && (
              <div className="mb-4 p-3 bg-orange-50 dark:bg-orange-900/20 border border-orange-200 dark:border-orange-800 rounded-lg animate-in fade-in duration-300">
                <div className="flex items-center gap-2 mb-2">
                  <div className="w-2 h-2 bg-orange-500 rounded-full animate-pulse"></div>
                  <span className="text-sm font-medium text-orange-800 dark:text-orange-200">
                    Live Tracking Active
                  </span>
                </div>
                <p className="text-xs text-orange-700 dark:text-orange-300">
                  {locations.length} vehicle{locations.length > 1 ? 's' : ''} being tracked
                </p>
                {followMode && focusLocation && (
                  <p className="text-xs text-orange-600 dark:text-orange-400 mt-1">
                    Following Vehicle {focusLocation.vehicle_id}
                  </p>
                )}
              </div>
            )}

            {/* Items List */}
            <div className="flex-1 overflow-y-auto space-y-2">
              {filteredItems.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground animate-in fade-in duration-300">
                  <p>No {activeTab} found</p>
                  {searchTerm && <p className="text-xs mt-1">Try adjusting your search</p>}
                </div>
              ) : (
                filteredItems.map((item, index) => (
                  <div
                    key={item.id}
                    className={`w-full p-3 border border-border cursor-pointer transition-all duration-300 ease-in-out hover:bg-accent hover:scale-[1.02] hover:shadow-md transform animate-in fade-in slide-in-from-left-2 rounded-xl ${selectedItem?.id === item.id
                      ? 'bg-primary/10 border-primary scale-[1.02] shadow-md'
                      : ''
                      }`}
                    style={{ animationDelay: `${index * 50}ms` }}
                    onClick={() => handleItemSelect(item)}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <h4 className="font-medium text-sm truncate transition-colors duration-200">
                          {item.name}
                        </h4>
                        {activeTab === 'vehicles' ? (
                          <div className="mt-1 space-y-1">
                            <p className="text-xs text-muted-foreground transition-colors duration-200">
                              {item.make} {item.model}
                            </p>
                            <p className="text-xs text-muted-foreground transition-colors duration-200">
                              Plate: {item.license_plate}
                            </p>
                            <div className="flex items-center mt-1">
                              <div
                                className={`w-2 h-2 rounded-full mr-2 transition-all duration-300 ${item.status === 'active'
                                  ? 'bg-green-500 animate-pulse'
                                  : item.status === 'inactive'
                                    ? 'bg-red-500'
                                    : 'bg-yellow-500 animate-pulse'
                                  }`}
                              ></div>
                              <span className="text-xs capitalize text-muted-foreground transition-colors duration-200">
                                {item.status}
                              </span>
                            </div>
                          </div>
                        ) : (
                          <div className="mt-1 space-y-1">
                            <p className="text-xs text-muted-foreground truncate transition-colors duration-200">
                              {item.description || 'No description'}
                            </p>
                            <div className="flex items-center mt-1">
                              <div
                                className={`w-2 h-2 rounded-full mr-2 transition-all duration-300 ${item.type === 'depot'
                                  ? 'bg-blue-500'
                                  : item.type === 'restricted'
                                    ? 'bg-red-500'
                                    : 'bg-purple-500'
                                  }`}
                              ></div>
                              <span className="text-xs capitalize text-muted-foreground transition-colors duration-200">
                                {item.type}
                              </span>
                            </div>
                            <div className="flex items-center gap-2 mt-2">
                              <button
                                onClick={(e) => handleEditGeofence(item, e)}
                                className="p-1 text-blue-600 dark:text-blue-400 hover:bg-blue-100 dark:hover:bg-blue-900/30 rounded transition-all duration-200"
                                title="Edit Geofence"
                              >
                                <Edit2 className="w-4 h-4" />
                              </button>
                              <button
                                onClick={(e) => handleDeleteGeofence(item.id, e)}
                                className="p-1 text-red-600 dark:text-red-400 hover:bg-red-100 dark:hover:bg-red-900/30 rounded transition-all duration-200"
                                title="Delete Geofence"
                              >
                                <Trash2 className="w-4 h-4" />
                              </button>
                            </div>
                          </div>
                        )}
                      </div>
                      <div className="flex items-center gap-1 ml-2 flex-shrink-0">
                        {activeTab === 'geofences' ? (
                          <Shield className="w-4 h-4 text-muted-foreground transition-transform duration-200 group-hover:scale-110" />
                        ) : (
                          <Car className="w-4 h-4 text-muted-foreground transition-transform duration-200 group-hover:scale-110" />
                        )}
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Geofence Creation Modal for drawing */}
      <GeofenceCreationModal
        isOpen={showGeofenceModal}
        onClose={() => {
          setShowGeofenceModal(false);
          setPendingGeofence(null);
          // Remove temporary layer if it exists
          if (pendingGeofence?.layer && mapRef.current) {
            mapRef.current.removeLayer(pendingGeofence.layer);
          }
        }}
        onSave={handleSaveGeofence}
        shapeData={pendingGeofence}
      />
    </div>
  );
};

export default TrackingMapWithSidebar;