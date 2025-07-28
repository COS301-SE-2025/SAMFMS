import React, { useState, useEffect } from 'react';
import { Search, Plus, Edit2, Trash2 } from 'lucide-react';
import { addGeofence, deleteGeofence, updateGeofence } from '../../backend/api/geofences';

const GeofenceManager = ({ onGeofenceChange, currentGeofences }) => {
  // State for the component
  const [geofences, setGeofences] = useState(currentGeofences || []);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState('');
  const [showAddModal, setShowAddModal] = useState(false);
  const [editingGeofence, setEditingGeofence] = useState(null);
  const [newGeofence, setNewGeofence] = useState({
    name: '',
    description: '',
    type: 'depot', 
    geometryType: 'circle', 
    radius: 500,
    coordinates: { lat: 37.7749, lng: -122.4194 },
    status: 'active'
  });

  // Filter geofences based on search and type filter
  const filteredGeofences = geofences.filter(geofence => {
    const matchesSearch = geofence.name.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesType = filterType === '' || geofence.type === filterType;

    return matchesSearch && matchesType;
  });

  // Effect to notify parent component when geofences change
  useEffect(() => {
    if (onGeofenceChange) {
      onGeofenceChange(geofences);
    }
  }, [geofences, onGeofenceChange]);

  // Handle adding a new geofence
  const handleAddGeofence = async () => {
    try {
      if (!newGeofence.name) {
        alert("Please fill in the name.");
        return;
      }

      const lat = parseFloat(newGeofence.coordinates.lat);
      const lng = parseFloat(newGeofence.coordinates.lng);

      let geometry;

      if (newGeofence.geometryType === 'circle') {
        // Correct: use center + radius
        geometry = {
          type: "circle",
          center: { latitude: lat, longitude: lng },
          radius: parseInt(newGeofence.radius)
        };
      }
      else if (newGeofence.geometryType === 'rectangle') {
        // Generate a small rectangle for demo
        const offset = 0.001;
        geometry = {
          type: "rectangle",
          points: [
            { latitude: lat + offset, longitude: lng - offset },
            { latitude: lat + offset, longitude: lng + offset },
            { latitude: lat - offset, longitude: lng + offset },
            { latitude: lat - offset, longitude: lng - offset }
          ]
        };
      }
      else if (newGeofence.geometryType === 'polygon') {
        // Example: simple triangle around the point
        const offset = 0.001;
        geometry = {
          type: "polygon",
          points: [
            { latitude: lat + offset, longitude: lng },
            { latitude: lat - offset, longitude: lng + offset },
            { latitude: lat - offset, longitude: lng - offset }
          ]
        };
      }

      const payload = {
        name: newGeofence.name,
        description: newGeofence.description || "",
        type: newGeofence.type,       // depot, service, delivery, etc.
        status: newGeofence.status || "active",
        geometry: geometry
      };

      console.log("Sending geofence data:", payload);
      const response = await addGeofence(payload);
      console.log("Geofence created successfully:", response);

      // Adapt response for UI
      const newGeofenceForUI = {
        ...response,
        coordinates: {
          lat: response.geometry?.center?.latitude || response.geometry?.points?.[0]?.latitude || 0,
          lng: response.geometry?.center?.longitude || response.geometry?.points?.[0]?.longitude || 0
        },
        radius: response.geometry?.radius || 500,
        geometryType: response.geometry?.type || 'circle'
      };

      setGeofences(prev => [...prev, newGeofenceForUI]);
      setShowAddModal(false);
      resetForm();
    } catch (error) {
      console.error("Error creating geofence:", error);
      alert(`Failed to create geofence: ${error.message || error}`);
    }
  };


  // Helper function to get colors based on geofence type
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

  // Handle editing a geofence
  const handleEditGeofence = async () => {
    if (!editingGeofence) return;

    try {
      const lat = parseFloat(newGeofence.coordinates.lat);
      const lng = parseFloat(newGeofence.coordinates.lng);

      let geometry;
      if (newGeofence.geometryType === 'circle') {
        geometry = {
          type: "circle",
          center: { latitude: lat, longitude: lng },
          radius: parseInt(newGeofence.radius)
        };
      } else if (newGeofence.geometryType === 'rectangle') {
        const offset = 0.001;
        geometry = {
          type: "rectangle",
          points: [
            { latitude: lat + offset, longitude: lng - offset },
            { latitude: lat + offset, longitude: lng + offset },
            { latitude: lat - offset, longitude: lng + offset },
            { latitude: lat - offset, longitude: lng - offset }
          ]
        };
      } else if (newGeofence.geometryType === 'polygon') {
        const offset = 0.001;
        geometry = {
          type: "polygon",
          points: [
            { latitude: lat + offset, longitude: lng },
            { latitude: lat - offset, longitude: lng + offset },
            { latitude: lat - offset, longitude: lng - offset }
          ]
        };
      }

      const payload = {
        name: newGeofence.name,
        description: newGeofence.description || "",
        type: newGeofence.type,
        status: newGeofence.status,
        geometry: geometry
      };

      const response = await updateGeofence(editingGeofence.id, payload);
      console.log("Geofence updated successfully:", response);

      const updatedGeofences = geofences.map(g =>
        g.id === editingGeofence.id ? { ...g, ...payload, coordinates: { lat, lng }, radius: geometry.radius } : g
      );
      setGeofences(updatedGeofences);

      resetForm();
      setEditingGeofence(null);
      setShowAddModal(false);
    } catch (error) {
      console.error("Error updating geofence:", error);
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
        console.error("Error deleting geofence:", error);
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
      status: geofence.status
    });
    setShowAddModal(true);
  };

  // Reset the form
  const resetForm = () => {
    setNewGeofence({
      name: "",
      description: "",
      type: "depot",
      geometryType: "circle",
      status: "active",
      coordinates: { lat: 0, lng: 0 },
      radius: 500
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
              <option value="depot">Depot</option>
              <option value="service">Service</option>
              <option value="delivery">Delivery</option>
              <option value="restricted">Restricted</option>
              <option value="emergency">Emergency</option>
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
                    <td className="py-3 px-4">{geofence.name}</td>
                    <td className="py-3 px-4">
                      {geofence.type.charAt(0).toUpperCase() + geofence.type.slice(1)}
                    </td>
                    <td className="py-3 px-4">
                      {(geofence.geometryType || geofence.geometry?.type || 'circle').charAt(0).toUpperCase() +
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
      </div>

      {/* Add/Edit Geofence Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black bg-opacity-30 z-50 flex items-center justify-center">
          <div className="bg-card p-6 rounded-lg shadow-lg max-w-md w-full max-h-[90vh] overflow-y-auto">
            <h3 className="text-xl font-semibold mb-4">
              {editingGeofence ? 'Edit Geofence' : 'Add New Geofence'}
            </h3>
            <div className="space-y-4">
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
                  onChange={e => setNewGeofence({ ...newGeofence, geometryType: e.target.value })}
                  className="w-full px-3 py-2 rounded-md border border-input bg-background text-sm"
                >
                  <option value="circle">Circle</option>
                  <option value="polygon">Polygon</option>
                  <option value="rectangle">Rectangle</option>
                </select>
              </div>

              {/* Radius (only for circle) */}
              {newGeofence.geometryType === 'circle' && (
                <div>
                  <label className="block text-sm font-medium mb-1">Radius (meters)</label>
                  <input
                    type="number"
                    value={newGeofence.radius}
                    onChange={e => setNewGeofence({ ...newGeofence, radius: parseInt(e.target.value) })}
                    className="w-full px-3 py-2 rounded-md border border-input bg-background text-sm"
                    min="10"
                    max="10000"
                  />
                </div>
              )}

              {/* Coordinates (center for now) */}
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

              {/* Buttons */}
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
                  disabled={!newGeofence.name || (newGeofence.geometryType === 'circle' && isNaN(newGeofence.radius))}
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