import React, { useState, useEffect, useRef } from 'react';
import { History } from 'lucide-react';
import { 
  getAllDriverHistories 
} from '../../backend/api/driverBehavior';
import TripHistoryModal from './TripHistoryModal';
import Pagination from '../vehicles/Pagination';

const DriverBehaviorDrivers = ({ driverData: propDriverData, onDataUpdate }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [drivers, setDrivers] = useState(propDriverData || []);
  const [sortField, setSortField] = useState('overallScore');
  const [sortDirection, setSortDirection] = useState('desc');
  const [searchTerm, setSearchTerm] = useState('');
  const [filterRisk, setFilterRisk] = useState('all');
  const [driversPerPage, setDriversPerPage] = useState(10);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const [showTripHistory, setShowTripHistory] = useState(false);
  const [selectedDriverId, setSelectedDriverId] = useState(null);
  const [selectedDriverName, setSelectedDriverName] = useState('');

  // Use ref to store the onDataUpdate callback to avoid dependency issues
  const onDataUpdateRef = useRef(onDataUpdate);
  useEffect(() => {
    onDataUpdateRef.current = onDataUpdate;
  }, [onDataUpdate]);

  // Load data on component mount and when filters change
  useEffect(() => {
    const loadDriversData = async (page = currentPage, limit = driversPerPage) => {
      try {
        setLoading(true);
        setError(null);

        const params = {
          skip: (page - 1) * limit,
          limit: limit
        };

        // Add search term if it exists and has content
        if (searchTerm && searchTerm.trim()) {
          params.search = searchTerm.trim();
        }

        // Add risk level filter if not 'all'
        if (filterRisk !== 'all') {
          params.risk_level = filterRisk;
        }

        const api = await getAllDriverHistories(params);

        // Unpack nested responses safely
        const histories =
          api?.data?.data?.histories ??
          api?.data?.histories ??
          api?.histories ??
          api?.drivers ?? // keep supporting older "drivers" shape
          [];

        // Normalize fields so the table keeps working
        const driversData = histories.map(d => ({
          ...d,
          // keep existing UI that expects `overallScore`
          overallScore: d.driver_safety_score ?? d.overallScore,
          // ensure the badge reads from backend risk
          driver_risk_level: (d.driver_risk_level ?? d.risk_level ?? d.riskLevel ?? d.risk ?? 'low'),
        }));

        // Total/Count (support both nested & flat pagination)
        const totalDrivers =
          api?.data?.data?.pagination?.total ??
          api?.data?.pagination?.total ??
          api?.pagination?.total ??
          histories.length;

        setDrivers(driversData);
        setTotalCount(totalDrivers);
        setTotalPages(Math.ceil(totalDrivers / limit));

        // If you notify parent:
        if (onDataUpdateRef.current) onDataUpdateRef.current(driversData);

      } catch (err) {
        console.error('Error loading drivers data:', err);
        setError('Failed to load driver data. Please try again.');
      } finally {
        setLoading(false);
      }
    };

    if (propDriverData && propDriverData.length > 0) {
      setDrivers(propDriverData);
      setTotalCount(propDriverData.length);
      setTotalPages(Math.ceil(propDriverData.length / driversPerPage));
      if (onDataUpdateRef.current) {
        onDataUpdateRef.current(propDriverData);
      }
    } else {
      loadDriversData(currentPage, driversPerPage);
    }
  }, [propDriverData, searchTerm, filterRisk, driversPerPage, currentPage]);

  // For server-side pagination, we don't need local filtering/sorting
  // The API handles filtering and we'll display drivers as received
  const displayDrivers = drivers;

  const handleSort = (field) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('desc');
    }
  };

  // Pagination handlers
  const goToNextPage = () => {
    if (currentPage < totalPages) {
      setCurrentPage(currentPage + 1);
    }
  };

  const goToPrevPage = () => {
    if (currentPage > 1) {
      setCurrentPage(currentPage - 1);
    }
  };

  const changeItemsPerPage = (event) => {
    const newPerPage = parseInt(event.target.value, 10);
    setDriversPerPage(newPerPage);
    setCurrentPage(1); // Reset to first page when changing page size
  };

  // Reset to first page when search or filter changes
  useEffect(() => {
    setCurrentPage(1);
  }, [searchTerm, filterRisk]);

  // Debounce search to avoid too many API calls
  useEffect(() => {
    const debounceTimer = setTimeout(() => {
      // Trigger data reload after debounce delay
      if (!propDriverData || propDriverData.length === 0) {
        // This will trigger the main useEffect to reload data
        setCurrentPage(1);
      }
    }, 300);

    return () => clearTimeout(debounceTimer);
  }, [searchTerm, propDriverData]);

  const getRiskLevel = (riskLevel) => {
    const level = (riskLevel || 'low').toLowerCase();
    if (level === 'high') return { level: 'High', color: 'text-red-600 bg-red-100 dark:bg-red-900/20 dark:text-red-400' };
    if (level === 'medium') return { level: 'Medium', color: 'text-yellow-600 bg-yellow-100 dark:bg-yellow-900/20 dark:text-yellow-400' };
    return { level: 'Low', color: 'text-green-600 bg-green-100 dark:bg-green-900/20 dark:text-green-400' };
  };

  const getSortIcon = (field) => {
    if (sortField !== field) return '↕️';
    return sortDirection === 'asc' ? '↑' : '↓';
  };

  return (
    <div className="space-y-6">
      {/* Filters and Search */}
      <div className="bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-800 dark:to-gray-900 border border-gray-200 dark:border-gray-700 rounded-xl shadow-lg p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-6 flex items-center">
          <span className="text-2xl mr-3">🔍</span>
          Search & Filter Drivers
        </h3>
        <div className="flex flex-col md:flex-row gap-4">
          <div className="flex-1">
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Search Drivers
            </label>
            <input
              type="text"
              placeholder="Search by name or employee ID..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full px-4 py-3 border-2 border-gray-200 dark:border-gray-600 rounded-lg 
                         focus:ring-2 focus:ring-blue-500 focus:border-blue-500 
                         dark:bg-gray-700 dark:text-white transition-all duration-200 
                         hover:border-blue-300 dark:hover:border-blue-400"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Risk Level
            </label>
            <select
              value={filterRisk}
              onChange={(e) => setFilterRisk(e.target.value)}
              className="px-4 py-3 border-2 border-gray-200 dark:border-gray-600 rounded-lg 
                         focus:ring-2 focus:ring-blue-500 focus:border-blue-500 
                         dark:bg-gray-700 dark:text-white transition-all duration-200 
                         hover:border-blue-300 dark:hover:border-blue-400"
            >
              <option value="all">All Risk Levels</option>
              <option value="high">High Risk</option>
              <option value="medium">Medium Risk</option>
              <option value="low">Low Risk</option>
            </select>
          </div>
        </div>
      </div>

      {/* Results Summary */}
      <div className="flex items-center justify-between bg-gradient-to-r from-gray-50 to-blue-50 dark:from-gray-800 dark:to-blue-900/20 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
        <div className="flex items-center space-x-4">
          <div className="flex items-center">
            <span className="text-lg mr-2">📊</span>
            <p className="text-sm font-medium text-gray-700 dark:text-gray-300">
              Showing <span className="font-bold text-blue-600 dark:text-blue-400">{displayDrivers.length}</span> of <span className="font-bold">{totalCount}</span> drivers
              <span className="ml-2 text-xs text-gray-500 dark:text-gray-400">
                (Page {currentPage} of {totalPages})
              </span>
            </p>
          </div>
        </div>
        <div className="flex items-center space-x-4">
          {loading && (
            <div className="flex items-center text-blue-600 dark:text-blue-400">
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600 dark:border-blue-400 mr-2"></div>
              <span className="text-sm font-medium">Loading...</span>
            </div>
          )}
          {error && (
            <div className="flex items-center text-red-600 dark:text-red-400">
              <span className="text-lg mr-2">⚠️</span>
              <span className="text-sm font-medium">{error}</span>
            </div>
          )}
        </div>
      </div>

      {/* Drivers Table */}
      <div className="bg-gradient-to-br from-white to-gray-50 dark:from-gray-800 dark:to-gray-900 border border-gray-200 dark:border-gray-700 rounded-xl shadow-lg overflow-hidden">
        <div className="px-6 py-4 bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 border-b border-gray-200 dark:border-gray-700">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center">
            <span className="text-2xl mr-3">👥</span>
            Driver Performance Overview
          </h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gradient-to-r from-gray-100 to-gray-200 dark:from-gray-700 dark:to-gray-800">
              <tr>
                <th 
                  className="px-6 py-4 text-left text-xs font-semibold text-gray-700 dark:text-gray-200 uppercase tracking-wider cursor-pointer hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors duration-200"
                  onClick={() => handleSort('name')}
                >
                  <span className="flex items-center">
                    👤 Driver {getSortIcon('name')}
                  </span>
                </th>
                <th 
                  className="px-6 py-4 text-left text-xs font-semibold text-gray-700 dark:text-gray-200 uppercase tracking-wider cursor-pointer hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors duration-200"
                  onClick={() => handleSort('employeeId')}
                >
                  <span className="flex items-center">
                    🆔 Employee ID {getSortIcon('employeeId')}
                  </span>
                </th>
                <th 
                  className="px-6 py-4 text-left text-xs font-semibold text-gray-700 dark:text-gray-200 uppercase tracking-wider cursor-pointer hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors duration-200"
                  onClick={() => handleSort('overallScore')}
                >
                  <span className="flex items-center">
                    📊 Safety Score {getSortIcon('overallScore')}
                  </span>
                </th>
                <th className="px-6 py-4 text-left text-xs font-semibold text-gray-700 dark:text-gray-200 uppercase tracking-wider">
                  <span className="flex items-center">
                    ⚠️ Risk Level
                  </span>
                </th>
                <th 
                  className="px-6 py-4 text-left text-xs font-semibold text-gray-700 dark:text-gray-200 uppercase tracking-wider cursor-pointer hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors duration-200"
                  onClick={() => handleSort('speedingEvents')}
                >
                  <span className="flex items-center">
                    🚗💨 Speeding Events {getSortIcon('speedingEvents')}
                  </span>
                </th>
                <th 
                  className="px-6 py-4 text-left text-xs font-semibold text-gray-700 dark:text-gray-200 uppercase tracking-wider cursor-pointer hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors duration-200"
                  onClick={() => handleSort('harshBraking')}
                >
                  <span className="flex items-center">
                    🛑 Harsh Braking {getSortIcon('harshBraking')}
                  </span>
                </th>
                <th 
                  className="px-6 py-4 text-left text-xs font-semibold text-gray-700 dark:text-gray-200 uppercase tracking-wider cursor-pointer hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors duration-200"
                  onClick={() => handleSort('rapidAcceleration')}
                >
                  <span className="flex items-center">
                    🚀 Rapid Acceleration {getSortIcon('rapidAcceleration')}
                  </span>
                </th>
                <th 
                  className="px-6 py-4 text-left text-xs font-semibold text-gray-700 dark:text-gray-200 uppercase tracking-wider cursor-pointer hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors duration-200"
                  onClick={() => handleSort('distraction')}
                >
                  <span className="flex items-center">
                    📱 Distraction Events {getSortIcon('distraction')}
                  </span>
                </th>
                <th className="px-6 py-4 text-left text-xs font-semibold text-gray-700 dark:text-gray-200 uppercase tracking-wider">
                  <span className="flex items-center">
                    ⚡ Actions
                  </span>
                </th>
              </tr>
            </thead>
            <tbody className="bg-gradient-to-b from-white to-gray-50 dark:from-gray-800 dark:to-gray-900 divide-y divide-gray-200 dark:divide-gray-700">
              {displayDrivers.map((driver) => {
                const riskInfo = getRiskLevel(driver.driver_risk_level);
                const driverName = driver.name || driver.driver_name || 'Unknown Driver';
                const employeeId = driver.employeeId || driver.driver_id || driver.id || 'N/A';
                
                return (
                  <tr key={driver.id || driver._id || driver.driver_id} className="hover:bg-gradient-to-r hover:from-blue-50 hover:to-indigo-50 dark:hover:from-blue-900/10 dark:hover:to-indigo-900/10 transition-all duration-200">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <div className="flex-shrink-0 h-10 w-10">
                          <div className="h-10 w-10 rounded-full bg-gradient-to-br from-blue-100 to-indigo-100 dark:from-blue-900/30 dark:to-indigo-900/30 flex items-center justify-center shadow-lg">
                            <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                              {driverName.split(' ').map(n => n[0]).join('').toUpperCase()}
                            </span>
                          </div>
                        </div>
                        <div className="ml-4">
                          <div className="text-sm font-medium text-gray-900 dark:text-white">{driverName}</div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                      {employeeId}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                      <div className="flex items-center">
                        <div className={`px-3 py-1 rounded-full text-sm font-bold ${
                          parseFloat(driver.overallScore) >= 8.5
                            ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400'
                            : parseFloat(driver.overallScore) >= 7
                            ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400'
                            : 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400'
                        }`}>
                          {(parseFloat(driver.overallScore) || 0).toFixed(1)}/10
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${riskInfo.color}`}>
                        {riskInfo.level} Risk
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                      <span className={(driver.speedingEvents || 0) > 0 ? 'text-red-600 dark:text-red-400 font-semibold' : ''}>
                        {driver.speedingEvents || 0}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                      <span className={(driver.harshBraking || 0) > 0 ? 'text-orange-600 dark:text-orange-400 font-semibold' : ''}>
                        {driver.harshBraking || 0}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                      <span className={(driver.rapidAcceleration || 0) > 0 ? 'text-yellow-600 dark:text-yellow-400 font-semibold' : ''}>
                        {driver.rapidAcceleration || 0}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                      <span className={(driver.distraction || 0) > 0 ? 'text-purple-600 dark:text-purple-400 font-semibold' : ''}>
                        {driver.distraction || 0}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                      <button 
                        className="bg-gradient-to-r from-blue-500 to-indigo-500 hover:from-blue-600 hover:to-indigo-600 
                                   text-white p-2 rounded-lg shadow-md hover:shadow-lg 
                                   transform hover:scale-105 transition-all duration-200 
                                   flex items-center justify-center"
                        title="View Trip History"
                        onClick={() => {
                          setSelectedDriverId(driver.id || driver.driver_id);
                          setSelectedDriverName(driverName);
                          setShowTripHistory(true);
                        }}
                      >
                        <History className="w-5 h-5" />
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        
        {displayDrivers.length === 0 && (
          <div className="text-center py-12 bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-800 dark:to-gray-900">
            <div className="text-6xl mb-4">🚗</div>
            <p className="text-lg font-medium text-gray-600 dark:text-gray-400 mb-2">No drivers found</p>
            <p className="text-sm text-gray-500 dark:text-gray-500">Try adjusting your search criteria or filters</p>
          </div>
        )}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="mt-6">
          <Pagination
            currentPage={currentPage}
            totalPages={totalPages}
            itemsPerPage={driversPerPage}
            goToNextPage={goToNextPage}
            goToPrevPage={goToPrevPage}
            changeItemsPerPage={changeItemsPerPage}
          />
        </div>
      )}

      {/* Trip History Modal */}
      <TripHistoryModal
        isOpen={showTripHistory}
        onClose={() => setShowTripHistory(false)}
        driverId={selectedDriverId}
        driverName={selectedDriverName}
      />
    </div>
  );
};

export default DriverBehaviorDrivers;