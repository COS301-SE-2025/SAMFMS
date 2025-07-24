import React, { useState, useEffect } from 'react';
import { Search, Plus, Edit2, Trash2 } from 'lucide-react';
import { addGeofence } from '../../backend/api/geofences';

const GeofenceManager = ({ onGeofenceChange, currentGeofences }) => {
  // State for the component
  const [geofences, setGeofences] = useState(currentGeofences || []);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState('');
  const [showAddModal, setShowAddModal] = useState(false);
  const [editingGeofence, setEditingGeofence] = useState(null);
  const [newGeofence, setNewGeofence] = useState({
    name: '',
    type: 'depot',
    radius: 500,
    coordinates: { lat: 37.7749, lng: -122.4194 },
    status: 'active',
  });

  // Filter geofences based on search and type filter
  const filteredGeofences = geofences.filter(geofence => {
    const matchesSearch = geofence.name.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesType = filterType === '' || geofence.type === filterType;

    return matchesSearch && matchesType;
  });

  function parseGeofenceArea(areaStr) {
    const match = areaStr.match(/^CIRCLE\((-?\d+(\.\d+)?) (-?\d+(\.\d+)?),(\d+)\)$/);
    if (!match) return null;

    const lng = parseFloat(match[1]);
    const lat = parseFloat(match[3]);
    const radius = parseFloat(match[5]);

    return {
      coordinates: { lat, lng },
      radius,
    };
  }

  // Effect to notify parent component when geofences change
  useEffect(() => {
    if (onGeofenceChange) {
      onGeofenceChange(geofences);
    }
  }, [geofences, onGeofenceChange]);

  // Handle adding a new geofence
  // Handle adding a new geofence
  const handleAddGeofence = async () => {
    try {
      console.log('Creating geofence with data:', newGeofence);

      const geofenceData = {
        name: newGeofence.name,
        description: newGeofence.description,
        type: newGeofence.type,
        radius: parseInt(newGeofence.radius),
        latitude: parseFloat(newGeofence.coordinates.lat),
        longitude: parseFloat(newGeofence.coordinates.lng),
        status: newGeofence.status
      };

      console.log('Sending geofence data:', geofenceData);
      const result = await addGeofence(geofenceData);
      console.log("Geofence creation response:", result);

      // FIXED: Check the correct response structure
      if (!result || result.status !== 'success' || !result.data) {
        console.error("Invalid response structure:", result);
        throw new Error("Invalid response from GPS service");
      }

      const responseData = result.data;
      console.log("Response data:", responseData);

      // FIXED: Handle the actual response structure from GPS service
      let geofenceId, geofenceArea, geofenceName;

      // The GPS service returns data directly in the 'data' field
      if (responseData.id) {
        geofenceId = responseData.id;
        geofenceArea = responseData.area || responseData.geometry;
        geofenceName = responseData.name;
      } else {
        console.error("No geofence ID in response data:", responseData);
        throw new Error("No geofence ID returned from service");
      }

      console.log("Extracted geofence data:", { geofenceId, geofenceArea, geofenceName });

      // Parse the area/geometry - handle both CIRCLE format and coordinates
      let parsed = null;
      if (geofenceArea) {
        parsed = parseGeofenceArea(geofenceArea);
      }

      // If parsing fails, use the original coordinates from the response or request
      if (!parsed) {
        console.warn("Could not parse geofence area, using original coordinates");
        parsed = {
          coordinates: {
            lat: responseData.latitude || newGeofence.coordinates.lat,
            lng: responseData.longitude || newGeofence.coordinates.lng
          },
          radius: responseData.radius || newGeofence.radius
        };
      }

      const newFormattedGeofence = {
        id: geofenceId,
        name: geofenceName || newGeofence.name,
        type: newGeofence.type,
        status: newGeofence.status,
        coordinates: parsed.coordinates,
        radius: parsed.radius,
        geometry: geofenceArea || `CIRCLE(${newGeofence.coordinates.lng} ${newGeofence.coordinates.lat},${newGeofence.radius})`
      };

      console.log("Adding geofence to state:", newFormattedGeofence);
      setGeofences(prev => [...prev, newFormattedGeofence]);

      resetForm();
      setShowAddModal(false);

      // Optional: Show success message
      alert("Geofence created successfully!");

    } catch (error) {
      console.error("Error creating geofence:", error);

      let errorMessage = "Failed to create geofence";
      if (error.response && error.response.data) {
        errorMessage += ": " + (error.response.data.detail || error.response.data.message || error.message);
      } else {
        errorMessage += ": " + error.message;
      }

      alert(errorMessage);
    }
  };


  // Handle editing a geofence
  const handleEditGeofence = () => {
    if (!editingGeofence) return;

    const updatedGeofences = geofences.map(g =>
      g.id === editingGeofence.id ? { ...newGeofence, id: g.id } : g
    );

    setGeofences(updatedGeofences);
    resetForm();
    setEditingGeofence(null);
    setShowAddModal(false);
  };

  // Handle deleting a geofence
  const handleDeleteGeofence = id => {
    if (window.confirm('Are you sure you want to delete this geofence?')) {
      setGeofences(geofences.filter(g => g.id !== id));
    }
  };

  // Edit geofence
  const startEditGeofence = geofence => {
    setEditingGeofence(geofence);
    setNewGeofence({ ...geofence });
    setShowAddModal(true);
  };

  // Reset the form
  const resetForm = () => {
    setNewGeofence({
      name: '',
      type: 'depot',
      radius: 500,
      coordinates: { lat: 37.7749, lng: -122.4194 },
      status: 'active',
    });
  };

  return (
    <>
      <div className="bg-card rounded-lg shadow-md p-6 border border-border">
        <div className="flex justify-between items-center mb-4">
          <div className="flex gap-2">
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
              <option value="restricted">Restricted Areas</option>
              <option value="depot">Depot Areas</option>
              <option value="customer">Customer Sites</option>
              <option value="service">Service Areas</option>
            </select>
          </div>
          <button
            className="bg-primary text-primary-foreground px-4 py-2 rounded-md hover:bg-primary/90 transition flex items-center gap-2"
            onClick={() => setShowAddModal(true)}
          >
            <Plus size={16} /> Add Geofence
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full border-collapse">
            <thead>
              <tr className="border-b border-border">
                <th className="text-left py-3 px-4">Name</th>
                <th className="text-left py-3 px-4">Type</th>
                <th className="text-left py-3 px-4">Radius</th>
                <th className="text-left py-3 px-4">Coordinates</th>
                <th className="text-left py-3 px-4">Status</th>
                <th className="text-left py-3 px-4">Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredGeofences.length > 0 ? (
                filteredGeofences.map(geofence => (
                  <tr key={geofence.id} className="border-b border-border hover:bg-accent/10">
                    <td className="py-3 px-4">{geofence.name}</td>
                    <td className="py-3 px-4">
                      {geofence.type.charAt(0).toUpperCase() + geofence.type.slice(1)}
                    </td>
                    <td className="py-3 px-4">{geofence.radius}m</td>
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
                          Restricted
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
                  <td colSpan="6" className="py-8 text-center text-muted-foreground">
                    No geofences found
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Add/Edit Geofence Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black bg-opacity-30 z-50 flex items-center justify-center">
          <div className="bg-card p-6 rounded-lg shadow-lg max-w-md w-full">
            <h3 className="text-xl font-semibold mb-4">
              {editingGeofence ? 'Edit Geofence' : 'Add New Geofence'}
            </h3>
            <div className="space-y-4">
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
              <div>
                <label className="block text-sm font-medium mb-1">Type</label>
                <select
                  value={newGeofence.type}
                  onChange={e => setNewGeofence({ ...newGeofence, type: e.target.value })}
                  className="w-full px-3 py-2 rounded-md border border-input bg-background text-sm"
                >
                  <option value="depot">Depot</option>
                  <option value="restricted">Restricted Area</option>
                  <option value="customer">Customer Site</option>
                  <option value="service">Service Area</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Radius (meters)</label>
                <input
                  type="number"
                  value={newGeofence.radius}
                  onChange={e =>
                    setNewGeofence({ ...newGeofence, radius: parseInt(e.target.value) })
                  }
                  className="w-full px-3 py-2 rounded-md border border-input bg-background text-sm"
                  min="10"
                  max="10000"
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
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
                          lat: parseFloat(e.target.value),
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
                          lng: parseFloat(e.target.value),
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
              <div>
                <label className="block text-sm font-medium mb-1">Status</label>
                <select
                  value={newGeofence.status}
                  onChange={e => setNewGeofence({ ...newGeofence, status: e.target.value })}
                  className="w-full px-3 py-2 rounded-md border border-input bg-background text-sm"
                >
                  <option value="active">Active</option>
                  <option value="restricted">Restricted</option>
                </select>
              </div>
              <div className="flex justify-end gap-2 mt-6">
                <button
                  onClick={() => {
                    setShowAddModal(false);
                    setEditingGeofence(null);
                    resetForm();
                  }}
                  className="px-4 py-2 border border-input rounded-md"
                >
                  Cancel
                </button>
                <button
                  onClick={editingGeofence ? handleEditGeofence : handleAddGeofence}
                  className="bg-primary text-primary-foreground px-4 py-2 rounded-md hover:bg-primary/90 transition"
                  disabled={!newGeofence.name || isNaN(newGeofence.radius)}
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
