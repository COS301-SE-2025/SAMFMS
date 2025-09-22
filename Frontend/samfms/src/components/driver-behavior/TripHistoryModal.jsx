import React, { useState, useEffect, useCallback } from 'react';
import { X, Map, Calendar, MapPin, Clock, AlertTriangle } from 'lucide-react';
import { getDriverTripHistory } from '../../backend/api/driverBehavior';
import TripMapModal from './TripMapModal';

const TripHistoryModal = ({ isOpen, onClose, driverId, driverName }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [trips, setTrips] = useState([]);
  const [pagination, setPagination] = useState({});
  const [mapModalOpen, setMapModalOpen] = useState(false);
  const [selectedTrip, setSelectedTrip] = useState(null);

  // Load trip history when modal opens
  const loadTripHistory = useCallback(async () => {
    if (!driverId) return;

    try {
      setLoading(true);
      setError(null);

      const response = await getDriverTripHistory(driverId, {
        skip: 0,
        limit: 100
      });

      setTrips(response.trips || []);
      setPagination(response.pagination || {});

    } catch (err) {
      console.error('Error loading trip history:', err);
      setError('Failed to load trip history. Please try again.');
    } finally {
      setLoading(false);
    }
  }, [driverId]);

  useEffect(() => {
    if (isOpen && driverId) {
      loadTripHistory();
    }
  }, [isOpen, driverId, loadTripHistory]);

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  const formatTime = (dateString) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const formatLocation = (location) => {
    if (!location) return 'Unknown Location';
    return location.address || location.name || `${location.lat?.toFixed(4)}, ${location.lng?.toFixed(4)}` || 'Unknown Location';
  };

  const getStatusColor = (status) => {
    switch (status?.toLowerCase()) {
      case 'completed':
        return 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400';
      case 'in_progress':
        return 'bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-400';
      case 'cancelled':
        return 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400';
      case 'scheduled':
        return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-400';
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-900/20 dark:text-gray-400';
    }
  };

  const handleMapClick = (trip) => {
    setSelectedTrip(trip);
    setMapModalOpen(true);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen px-4 pt-4 pb-20 text-center sm:block sm:p-0">
        {/* Background overlay */}
        <div 
          className="fixed inset-0 transition-opacity bg-gradient-to-br from-gray-900/50 to-blue-900/50 backdrop-blur-sm"
          onClick={onClose}
        />

        {/* Modal panel */}
        <div className="inline-block w-full max-w-6xl p-0 my-8 overflow-hidden text-left align-middle transition-all transform bg-gradient-to-br from-white to-gray-50 dark:from-gray-800 dark:to-gray-900 shadow-2xl rounded-2xl border border-gray-200 dark:border-gray-700">
          {/* Header */}
          <div className="bg-gradient-to-r from-blue-500 to-indigo-600 px-6 py-4 text-white">
            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <span className="text-2xl mr-3">🚗</span>
                <div>
                  <h3 className="text-xl font-bold">
                    Trip History for {driverName}
                  </h3>
                  <p className="text-blue-100 text-sm">
                    Driver ID: {driverId}
                  </p>
                </div>
              </div>
              <button
                onClick={onClose}
                className="p-2 text-white/80 hover:text-white hover:bg-white/20 rounded-lg transition-all duration-200"
              >
                <X className="w-6 h-6" />
              </button>
            </div>
          </div>

          {/* Content */}
          <div className="p-6">
            <div className="max-h-96 overflow-y-auto">
            {loading && (
              <div className="flex items-center justify-center h-32 bg-gradient-to-br from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 rounded-xl">
                <div className="text-center">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-3"></div>
                  <span className="text-blue-600 dark:text-blue-400 font-medium">Loading trip history...</span>
                </div>
              </div>
            )}

            {error && (
              <div className="flex items-center justify-center h-32 bg-gradient-to-br from-red-50 to-orange-50 dark:from-red-900/20 dark:to-orange-900/20 rounded-xl">
                <div className="text-center">
                  <AlertTriangle className="w-12 h-12 text-red-500 mx-auto mb-3" />
                  <p className="text-red-600 dark:text-red-400 font-medium mb-3">{error}</p>
                  <button
                    onClick={loadTripHistory}
                    className="bg-gradient-to-r from-red-500 to-orange-500 hover:from-red-600 hover:to-orange-600 
                               text-white px-4 py-2 rounded-lg font-medium shadow-md hover:shadow-lg 
                               transform hover:scale-105 transition-all duration-200"
                  >
                    🔄 Retry
                  </button>
                </div>
              </div>
            )}

            {!loading && !error && trips.length === 0 && (
              <div className="text-center py-12 bg-gradient-to-br from-gray-50 to-blue-50 dark:from-gray-800 dark:to-blue-900/20 rounded-xl">
                <div className="text-6xl mb-4">🚗</div>
                <Calendar className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <p className="text-lg font-medium text-gray-600 dark:text-gray-400 mb-2">No trips found for this driver</p>
                <p className="text-sm text-gray-500 dark:text-gray-500">This driver hasn't completed any trips yet</p>
              </div>
            )}

            {!loading && !error && trips.length > 0 && (
              <div className="bg-gradient-to-br from-white to-gray-50 dark:from-gray-800 dark:to-gray-900 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
                <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                  <thead className="bg-gradient-to-r from-gray-100 to-gray-200 dark:from-gray-700 dark:to-gray-800">
                    <tr>
                      <th className="px-6 py-4 text-left text-xs font-semibold text-gray-700 dark:text-gray-200 uppercase tracking-wider">
                        <span className="flex items-center">
                          🚗 Trip Name
                        </span>
                      </th>
                      <th className="px-6 py-4 text-left text-xs font-semibold text-gray-700 dark:text-gray-200 uppercase tracking-wider">
                        <span className="flex items-center">
                          📅 Schedule
                        </span>
                      </th>
                      <th className="px-6 py-4 text-left text-xs font-semibold text-gray-700 dark:text-gray-200 uppercase tracking-wider">
                        <span className="flex items-center">
                          📍 Locations
                        </span>
                      </th>
                      <th className="px-6 py-4 text-left text-xs font-semibold text-gray-700 dark:text-gray-200 uppercase tracking-wider">
                        <span className="flex items-center">
                          ✅ Status
                        </span>
                      </th>
                      <th className="px-6 py-4 text-left text-xs font-semibold text-gray-700 dark:text-gray-200 uppercase tracking-wider">
                        <span className="flex items-center">
                          ⚠️ Violations
                        </span>
                      </th>
                      <th className="px-6 py-4 text-left text-xs font-semibold text-gray-700 dark:text-gray-200 uppercase tracking-wider">
                        <span className="flex items-center">
                          🗺️ Actions
                        </span>
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-gradient-to-b from-white to-gray-50 dark:from-gray-800 dark:to-gray-900 divide-y divide-gray-200 dark:divide-gray-700">
                    {trips.map((trip, index) => (
                      <tr key={trip.trip_id || index} className="hover:bg-gradient-to-r hover:from-blue-50 hover:to-indigo-50 dark:hover:from-blue-900/10 dark:hover:to-indigo-900/10 transition-all duration-200">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm font-semibold text-gray-900 dark:text-white">
                            {trip.trip_name}
                          </div>
                          <div className="text-xs text-gray-500 dark:text-gray-400 flex items-center">
                            🆔 ID: {trip.trip_id}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm text-gray-900 dark:text-white">
                            <div className="flex items-center mb-1 text-sm font-medium">
                              <Calendar className="w-4 h-4 mr-2 text-blue-500" />
                              {formatDate(trip.scheduled_start_time)}
                            </div>
                            <div className="flex items-center text-xs text-gray-500 dark:text-gray-400">
                              <Clock className="w-3 h-3 mr-2 text-green-500" />
                              {formatTime(trip.scheduled_start_time)} - {formatTime(trip.scheduled_end_time)}
                            </div>
                          </div>
                        </td>
                        <td className="px-6 py-4">
                          <div className="text-sm text-gray-900 dark:text-white">
                            <div className="flex items-center mb-1">
                              <MapPin className="w-4 h-4 mr-2 text-green-500" />
                              <span className="truncate max-w-32 font-medium">{formatLocation(trip.origin)}</span>
                            </div>
                            <div className="flex items-center text-xs text-gray-500 dark:text-gray-400">
                              <MapPin className="w-4 h-4 mr-2 text-red-500" />
                              <span className="truncate max-w-32">{formatLocation(trip.destination)}</span>
                            </div>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`inline-flex px-3 py-1 text-xs font-bold rounded-full shadow-sm ${getStatusColor(trip.status)}`}>
                            {trip.status}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-center">
                          <div className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-bold ${
                            (trip.total_violations || trip.violation_count || 0) > 0 
                              ? 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400' 
                              : 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400'
                          }`}>
                            {(trip.total_violations || trip.violation_count || 0) > 0 ? '⚠️' : '✅'} {trip.total_violations || trip.violation_count || 0}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <button
                            onClick={() => handleMapClick(trip)}
                            className="bg-gradient-to-r from-green-500 to-emerald-500 hover:from-green-600 hover:to-emerald-600 
                                       text-white p-2 rounded-lg shadow-md hover:shadow-lg 
                                       transform hover:scale-105 transition-all duration-200 
                                       flex items-center justify-center"
                            title="View Trip on Map"
                          >
                            <Map className="w-4 h-4" />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* Footer with pagination info */}
          {pagination.total_count > 0 && (
            <div className="mx-6 mb-6 pt-4 border-t border-gray-200 dark:border-gray-700 bg-gradient-to-r from-gray-50 to-blue-50 dark:from-gray-800 dark:to-blue-900/20 rounded-lg p-4">
              <div className="flex items-center">
                <span className="text-lg mr-2">📊</span>
                <p className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  Showing <span className="font-bold text-blue-600 dark:text-blue-400">{pagination.skip + 1}</span> to <span className="font-bold text-blue-600 dark:text-blue-400">{Math.min(pagination.skip + pagination.limit, pagination.total_count)}</span> of <span className="font-bold">{pagination.total_count}</span> trips
                </p>
              </div>
            </div>
          )}
          </div>
        </div>
      </div>
      
      {/* Trip Map Modal */}
      {selectedTrip && (
        <TripMapModal
          isOpen={mapModalOpen}
          onClose={() => setMapModalOpen(false)}
          trip={selectedTrip}
          violations={selectedTrip.violations || {}}
        />
      )}
    </div>
  );
};

export default TripHistoryModal;