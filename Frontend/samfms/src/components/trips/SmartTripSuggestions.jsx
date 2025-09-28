import React, {useState, useEffect, useCallback} from 'react';
import {
  Clock,
  MapPin,
  User,
  Truck,
  CheckCircle,
  XCircle,
  RefreshCw,
  Calendar,
  Route,
  Zap,
  TrendingUp,
  AlertCircle,
  Brain,
  ArrowRight
} from 'lucide-react';

// Expected backend API functions (to be implemented):
import {getSmartTripSuggestions, acceptSmartTripSuggestion, declineSmartTripSuggestion} from '../../backend/api/trips';

const SmartTripSuggestions = ({onAccept, onDecline, onRefresh}) => {
  const [suggestions, setSuggestions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [processingIds, setProcessingIds] = useState(new Set());
  const [error, setError] = useState(null);

  // Fetch smart trip suggestions from backend
  const fetchSmartSuggestions = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      // TODO: Replace with actual API endpoint
      const response = await getSmartTripSuggestions();
      console.log("Received smart trips in smarttripsuggestions.jsx: ", response)

      setSuggestions(response.data.data.data || []);

    } catch (error) {
      console.error('Error fetching smart trip suggestions:', error);
      setError('Failed to load smart trip suggestions');
      setSuggestions([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchSmartSuggestions();
  }, [fetchSmartSuggestions]);

  // Handle accepting a suggestion
  const handleAccept = async (suggestionId) => {
    setProcessingIds(prev => new Set([...prev, suggestionId]));

    try {
      const respone = await acceptSmartTripSuggestion(suggestionId);
      console.log("Response for accepting smart trip: ", respone)

      console.log('Accepting suggestion:', suggestionId);

      // Remove accepted suggestion from list
      setSuggestions(prev => prev.filter(s => s.id !== suggestionId));

      if (onAccept) {
        onAccept(suggestionId);
      }
    } catch (error) {
      console.error('Error accepting suggestion:', error);
      setError('Failed to accept trip suggestion');
    } finally {
      setProcessingIds(prev => {
        const newSet = new Set(prev);
        newSet.delete(suggestionId);
        return newSet;
      });
    }
  };

  // Handle declining a suggestion
  const handleDecline = async (suggestionId) => {
    setProcessingIds(prev => new Set([...prev, suggestionId]));

    try {
      const response = await declineSmartTripSuggestion(suggestionId);
      console.log("Response for declining suggestion: ", response)

      console.log('Declining suggestion:', suggestionId);

      // Remove declined suggestion from list
      setSuggestions(prev => prev.filter(s => s.id !== suggestionId));

      if (onDecline) {
        onDecline(suggestionId);
      }
    } catch (error) {
      console.error('Error declining suggestion:', error);
      setError('Failed to decline trip suggestion');
    } finally {
      setProcessingIds(prev => {
        const newSet = new Set(prev);
        newSet.delete(suggestionId);
        return newSet;
      });
    }
  };

  // Handle refresh
  const handleRefresh = () => {
    fetchSmartSuggestions();
    if (onRefresh) {
      onRefresh();
    }
  };

  // Format date/time for display
  const formatDateTime = (dateString) => {
    try {
      return new Date(dateString).toLocaleString('en-ZA', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch {
      return 'Invalid Date';
    }
  };

  // Calculate time difference in readable format
  const getTimeDifference = (originalTime, optimizedTime) => {
    try {
      const original = new Date(originalTime);
      const optimized = new Date(optimizedTime);
      const diffMs = original.getTime() - optimized.getTime();
      const diffHours = Math.abs(diffMs) / (1000 * 60 * 60);

      if (diffHours < 1) {
        const diffMinutes = Math.abs(diffMs) / (1000 * 60);
        return `${Math.round(diffMinutes)}m ${diffMs > 0 ? 'earlier' : 'later'}`;
      }

      return `${diffHours.toFixed(1)}h ${diffMs > 0 ? 'earlier' : 'later'}`;
    } catch {
      return 'Time calculation error';
    }
  };

  // Loading state
  if (loading) {
    return (
      <div className="bg-white dark:bg-gray-900 rounded-lg shadow-md p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
            <Brain className="h-5 w-5 text-blue-500 dark:text-blue-400" />
            Smart Trip Suggestions
          </h3>
          <RefreshCw className="h-5 w-5 text-gray-400 animate-spin" />
        </div>
        <div className="flex items-center justify-center py-8">
          <div className="text-center">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 dark:border-blue-400"></div>
            <p className="mt-2 text-sm text-gray-600 dark:text-gray-300">Loading smart suggestions...</p>
          </div>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="bg-white dark:bg-gray-900 rounded-lg shadow-md p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
            <Brain className="h-5 w-5 text-blue-500 dark:text-blue-400" />
            Smart Trip Suggestions
          </h3>
          <button
            onClick={handleRefresh}
            className="p-2 text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 transition-colors"
            title="Refresh suggestions"
          >
            <RefreshCw className="h-5 w-5" />
          </button>
        </div>
        <div className="flex items-center justify-center py-8">
          <div className="text-center">
            <AlertCircle className="h-12 w-12 text-red-500 dark:text-red-400 mx-auto mb-4" />
            <p className="text-sm text-gray-600 dark:text-gray-300">{error}</p>
            <button
              onClick={handleRefresh}
              className="mt-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-500 transition-colors text-sm"
            >
              Try Again
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Main component render
  return (
    <div className="bg-white dark:bg-gray-900 rounded-lg shadow-md p-6">
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
          <Brain className="h-5 w-5 text-blue-500 dark:text-blue-400" />
          Smart Trip Suggestions
        </h1>
        <button
          onClick={handleRefresh}
          className="p-2 text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 transition-colors"
          title="Refresh suggestions"
        >
          <RefreshCw className="h-5 w-5" />
        </button>
      </div>

      {suggestions.length === 0 ? (
        // Empty state
        <div className="text-center py-8">
          <Zap className="h-12 w-12 text-gray-400 dark:text-gray-500 mx-auto mb-4" />
          <p className="text-gray-600 dark:text-gray-300 text-sm">
            No smart trip suggestions available at the moment.
          </p>
          <p className="text-gray-500 dark:text-gray-400 text-xs mt-1">
            AI will analyze scheduled trips and suggest optimizations automatically.
          </p>
        </div>
      ) : (
        // Suggestions list
        <div className="space-y-4">
          {suggestions.map((suggestion) => (
            <SuggestionCard
              key={suggestion.id}
              suggestion={suggestion}
              isProcessing={processingIds.has(suggestion.id)}
              onAccept={() => handleAccept(suggestion.id)}
              onDecline={() => handleDecline(suggestion.id)}
              formatDateTime={formatDateTime}
              getTimeDifference={getTimeDifference}
            />
          ))}
        </div>
      )}
    </div>
  );
};

// Separate component for each suggestion card
const SuggestionCard = ({
  suggestion,
  isProcessing,
  onAccept,
  onDecline,
  formatDateTime,
  getTimeDifference
}) => {
  return (
    <div className="border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 rounded-lg p-4 hover:shadow-lg transition-all duration-200">
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-3">
          <h2 className="font-medium text-gray-900 dark:text-white">{suggestion.trip_name || 'Unnamed Trip'}</h2>
          {/* <div className="flex items-center gap-1 px-2 py-1 bg-blue-100 dark:bg-blue-600/20 text-blue-700 dark:text-blue-300 rounded-full text-xs font-medium border border-blue-200 dark:border-blue-500/30">
            <TrendingUp className="h-3 w-3" />
            {suggestion.confidence}% confidence
          </div> */}
        </div>
      </div>

      {/* Route Information */}
      <div className="mb-4">
        <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-300 mb-2">
          <h3 className="font-medium flex items-center gap-3"><Route className="h-4 w-4" />Route Details</h3>
        </div>
        <div className="ml-6">
          <div className="grid grid-cols-2 gap-4 text-sm">
            {/* First Column - Origin and Destination */}
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <MapPin className="h-4 w-4 text-green-500 dark:text-green-400 flex-shrink-0" />
                <span className="text-gray-700 dark:text-gray-200">{suggestion.route.origin?.name || 'Origin'}</span>
              </div>
              <div className="flex items-center gap-2">
                <MapPin className="h-4 w-4 text-red-500 dark:text-red-400 flex-shrink-0" />
                <span className="text-gray-700 dark:text-gray-200">{suggestion.route.destination?.name || 'Destination'}</span>
              </div>
            </div>

            {/* Second Column - Distance and Duration */}
            <div className="space-y-2">
              <div className="text-gray-600 dark:text-gray-300">
                <span className="font-medium">Distance:</span> {suggestion.route.estimated_distance ? `${suggestion.route.estimated_distance.toFixed(1)} km` : 'N/A'}
              </div>
              <div className="text-gray-600 dark:text-gray-300">
                <span className="font-medium">Duration:</span> {suggestion.route.estimated_duration ? `${Math.round(suggestion.route.estimated_duration)} min` : 'N/A'}
              </div>
            </div>
          </div>

          {suggestion.route.waypoints && suggestion.route.waypoints.length > 0 && (
            <div className="mt-3 pl-4">
              <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">Waypoints:</p>
              <div className="flex flex-wrap gap-1">
                {suggestion.route.waypoints.map((waypoint, idx) => (
                  <span key={idx} className="text-xs bg-gray-100 dark:bg-gray-700/50 text-gray-600 dark:text-gray-300 px-2 py-1 rounded border border-gray-200 dark:border-gray-600">
                    {waypoint?.name || `Waypoint ${idx + 1}`}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Schedule Comparison */}
      <div className="grid md:grid-cols-2 gap-4 mb-4">
        {/* Original Schedule */}
        <div className="bg-gray-50 dark:bg-gray-800/50 border-l-4 border-l-gray-400 dark:border-l-gray-500 p-3 rounded border border-gray-200 dark:border-gray-600">
          <h5 className="text-sm font-medium text-gray-700 dark:text-gray-200 mb-2">Current Schedule</h5>
          <div className="space-y-1 text-sm text-gray-600 dark:text-gray-300">
            <div className="flex items-center gap-2">
              <Calendar className="h-3 w-3" />
              <span>Start: {formatDateTime(suggestion.original_schedule.start_time)}</span>
            </div>
            <div className="flex items-center gap-2">
              <Clock className="h-3 w-3" />
              <span>End: {formatDateTime(suggestion.original_schedule.end_time)}</span>
            </div>
            <div className="flex items-center gap-2">
              <Truck className="h-3 w-3" />
              <span>{'No vehicle assigned'}</span>
            </div>
            <div className="flex items-center gap-2">
              <User className="h-3 w-3" />
              <span>{'No driver assigned'}</span>
            </div>
          </div>
        </div>

        {/* Optimized Schedule */}
        <div className="bg-blue-50 dark:bg-blue-900/30 border-l-4 border-l-blue-500 dark:border-l-blue-400 p-3 rounded border border-blue-200 dark:border-blue-500/30">
          <h5 className="text-sm font-medium text-blue-700 dark:text-blue-300 mb-2 flex items-center gap-1">
            <Brain className="h-3 w-3" />
            Smart Trip Schedule
          </h5>
          <div className="space-y-1 text-sm text-gray-600 dark:text-gray-300">
            <div className="flex items-center gap-2">
              <Calendar className="h-3 w-3" />
              <span>Start: {formatDateTime(suggestion.optimized_schedule.start_time)}</span>
              <span className="text-xs text-blue-700 dark:text-blue-300 font-medium bg-blue-100 dark:bg-blue-600/20 px-1 py-0.5 rounded border border-blue-200 dark:border-blue-500/30">
                {getTimeDifference(suggestion.original_schedule.start_time, suggestion.optimized_schedule.start_time)}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <Clock className="h-3 w-3" />
              <span>End: {formatDateTime(suggestion.optimized_schedule.end_time)}</span>
              <span className="text-xs text-blue-700 dark:text-blue-300 font-medium bg-blue-100 dark:bg-blue-600/20 px-1 py-0.5 rounded border border-blue-200 dark:border-blue-500/30">
                {getTimeDifference(suggestion.original_schedule.end_time, suggestion.optimized_schedule.end_time)}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <Truck className="h-3 w-3" />
              <span className="font-medium text-blue-700 dark:text-blue-200">{suggestion.optimized_schedule.vehicle_name || 'Vehicle TBD'}</span>
            </div>
            <div className="flex items-center gap-2">
              <User className="h-3 w-3" />
              <span className="font-medium text-blue-700 dark:text-blue-200">{suggestion.optimized_schedule.driver_name || 'Driver TBD'}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Benefits */}
      {/* {suggestion.benefits && (
        <div className="mb-4">
          <h5 className="text-sm font-medium text-gray-700 dark:text-gray-200 mb-2">Expected Benefits</h5>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
            {suggestion.benefits.time_saved && (
              <div className="bg-green-100 dark:bg-green-600/20 text-green-700 dark:text-green-300 px-2 py-1 rounded text-xs font-medium border border-green-200 dark:border-green-500/30">
                ⏰ {suggestion.benefits.time_saved}
              </div>
            )}
            {suggestion.benefits.fuel_efficiency && (
              <div className="bg-blue-100 dark:bg-blue-600/20 text-blue-700 dark:text-blue-300 px-2 py-1 rounded text-xs font-medium border border-blue-200 dark:border-blue-500/30">
                ⛽ {suggestion.benefits.fuel_efficiency}
              </div>
            )}
            {suggestion.benefits.route_optimization && (
              <div className="bg-purple-100 dark:bg-purple-600/20 text-purple-700 dark:text-purple-300 px-2 py-1 rounded text-xs font-medium border border-purple-200 dark:border-purple-500/30">
                🗺️ {suggestion.benefits.route_optimization}
              </div>
            )}
            {suggestion.benefits.driver_utilization && (
              <div className="bg-orange-100 dark:bg-orange-600/20 text-orange-700 dark:text-orange-300 px-2 py-1 rounded text-xs font-medium border border-orange-200 dark:border-orange-500/30">
                👤 {suggestion.benefits.driver_utilization}
              </div>
            )}
          </div>
        </div>
      )} */}

      {/* AI Reasoning */}
      {suggestion.reasoning && suggestion.reasoning.length > 0 && (
        <div className="mb-4">
          <h5 className="text-sm font-medium text-gray-700 dark:text-gray-200 mb-2">Why This Suggestion?</h5>
          <div className="bg-gray-50 dark:bg-gray-800/50 rounded p-3 border border-gray-200 dark:border-gray-600/50">
            <ul className="text-xs text-gray-600 dark:text-gray-300 space-y-1">
              {suggestion.reasoning.map((reason, idx) => (
                <li key={idx} className="flex items-start gap-2">
                  <div className="w-1.5 h-1.5 bg-blue-500 dark:bg-blue-400 rounded-full mt-1.5 flex-shrink-0"></div>
                  <span>{reason}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex gap-2 pt-3 border-t border-gray-200 dark:border-gray-600">
        <button
          onClick={onAccept}
          disabled={isProcessing}
          className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-sm font-medium"
        >
          {isProcessing ? (
            <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
          ) : (
            <CheckCircle className="h-4 w-4" />
          )}
          Accept Optimization
        </button>
        <button
          onClick={onDecline}
          disabled={isProcessing}
          className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-gray-500 dark:bg-gray-700 text-white rounded-md hover:bg-gray-400 dark:hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-sm font-medium"
        >
          {isProcessing ? (
            <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
          ) : (
            <XCircle className="h-4 w-4" />
          )}
          Decline
        </button>
      </div>
    </div>
  );
};

export default SmartTripSuggestions;