import React, { useState, useEffect, useCallback } from 'react';
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
import { getSmartTripSuggestions, acceptSmartTripSuggestion, declineSmartTripSuggestion } from '../../backend/api/trips';

const SmartTripSuggestions = ({ onAccept, onDecline, onRefresh }) => {
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
      // TODO: Replace with actual API call
      // await acceptSmartTripSuggestion(suggestionId);
      
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
      // TODO: Replace with actual API call
      // await declineSmartTripSuggestion(suggestionId);
      
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
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
            <Brain className="h-5 w-5 text-blue-600" />
            Smart Trip Suggestions
          </h3>
          <RefreshCw className="h-5 w-5 text-gray-400 animate-spin" />
        </div>
        <div className="flex items-center justify-center py-8">
          <div className="text-center">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <p className="mt-2 text-sm text-gray-600">Loading smart suggestions...</p>
          </div>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
            <Brain className="h-5 w-5 text-blue-600" />
            Smart Trip Suggestions
          </h3>
          <button
            onClick={handleRefresh}
            className="p-2 text-gray-400 hover:text-gray-600 transition-colors"
            title="Refresh suggestions"
          >
            <RefreshCw className="h-5 w-5" />
          </button>
        </div>
        <div className="flex items-center justify-center py-8">
          <div className="text-center">
            <AlertCircle className="h-12 w-12 text-red-400 mx-auto mb-4" />
            <p className="text-sm text-gray-600">{error}</p>
            <button
              onClick={handleRefresh}
              className="mt-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors text-sm"
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
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
          <Brain className="h-5 w-5 text-blue-600" />
          Smart Trip Suggestions
        </h3>
        <button
          onClick={handleRefresh}
          className="p-2 text-gray-400 hover:text-gray-600 transition-colors"
          title="Refresh suggestions"
        >
          <RefreshCw className="h-5 w-5" />
        </button>
      </div>

      {suggestions.length === 0 ? (
        // Empty state
        <div className="text-center py-8">
          <Zap className="h-12 w-12 text-gray-300 mx-auto mb-4" />
          <p className="text-gray-500 text-sm">
            No smart trip suggestions available at the moment.
          </p>
          <p className="text-gray-400 text-xs mt-1">
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
    <div className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-all duration-200">
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div>
          <h4 className="font-medium text-gray-900">{suggestion.tripName}</h4>
          <p className="text-sm text-gray-500">Trip ID: {suggestion.tripId}</p>
        </div>
        <div className="flex items-center gap-1 px-2 py-1 bg-blue-100 text-blue-800 rounded-full text-xs font-medium">
          <TrendingUp className="h-3 w-3" />
          {suggestion.confidence}% confidence
        </div>
      </div>

      {/* Route Information */}
      <div className="mb-4">
        <div className="flex items-center gap-2 text-sm text-gray-600 mb-2">
          <Route className="h-4 w-4" />
          <span className="font-medium">Route Details</span>
        </div>
        <div className="ml-6">
          <div className="flex items-center justify-between text-sm">
            <div className="flex items-center gap-2">
              <MapPin className="h-3 w-3 text-green-500" />
              <span className="text-gray-700">{suggestion.route.origin}</span>
            </div>
            <ArrowRight className="h-4 w-4 text-gray-400" />
            <div className="flex items-center gap-2">
              <MapPin className="h-3 w-3 text-red-500" />
              <span className="text-gray-700">{suggestion.route.destination}</span>
            </div>
          </div>
          
          {suggestion.route.waypoints && suggestion.route.waypoints.length > 0 && (
            <div className="mt-2 pl-4">
              <p className="text-xs text-gray-500 mb-1">Waypoints:</p>
              <div className="flex flex-wrap gap-1">
                {suggestion.route.waypoints.map((waypoint, idx) => (
                  <span key={idx} className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded">
                    {waypoint}
                  </span>
                ))}
              </div>
            </div>
          )}
          
          <div className="flex gap-4 mt-2 text-xs text-gray-500">
            <span>Distance: {suggestion.route.estimatedDistance}</span>
            <span>Duration: {suggestion.route.estimatedDuration}</span>
          </div>
        </div>
      </div>

      {/* Schedule Comparison */}
      <div className="grid md:grid-cols-2 gap-4 mb-4">
        {/* Original Schedule */}
        <div className="bg-gray-50 border-l-4 border-gray-400 p-3 rounded">
          <h5 className="text-sm font-medium text-gray-700 mb-2">Current Schedule</h5>
          <div className="space-y-1 text-sm text-gray-600">
            <div className="flex items-center gap-2">
              <Calendar className="h-3 w-3" />
              <span>Start: {formatDateTime(suggestion.originalSchedule.startTime)}</span>
            </div>
            <div className="flex items-center gap-2">
              <Clock className="h-3 w-3" />
              <span>End: {formatDateTime(suggestion.originalSchedule.endTime)}</span>
            </div>
            <div className="flex items-center gap-2">
              <Truck className="h-3 w-3" />
              <span>{suggestion.originalSchedule.vehicle || 'No vehicle assigned'}</span>
            </div>
            <div className="flex items-center gap-2">
              <User className="h-3 w-3" />
              <span>{suggestion.originalSchedule.driver || 'No driver assigned'}</span>
            </div>
          </div>
        </div>

        {/* Optimized Schedule */}
        <div className="bg-blue-50 border-l-4 border-blue-500 p-3 rounded">
          <h5 className="text-sm font-medium text-blue-700 mb-2 flex items-center gap-1">
            <Brain className="h-3 w-3" />
            AI Optimized
          </h5>
          <div className="space-y-1 text-sm text-gray-600">
            <div className="flex items-center gap-2">
              <Calendar className="h-3 w-3" />
              <span>Start: {formatDateTime(suggestion.optimizedSchedule.startTime)}</span>
              <span className="text-xs text-blue-600 font-medium bg-blue-100 px-1 py-0.5 rounded">
                {getTimeDifference(suggestion.originalSchedule.startTime, suggestion.optimizedSchedule.startTime)}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <Clock className="h-3 w-3" />
              <span>End: {formatDateTime(suggestion.optimizedSchedule.endTime)}</span>
              <span className="text-xs text-blue-600 font-medium bg-blue-100 px-1 py-0.5 rounded">
                {getTimeDifference(suggestion.originalSchedule.endTime, suggestion.optimizedSchedule.endTime)}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <Truck className="h-3 w-3" />
              <span className="font-medium text-blue-700">{suggestion.optimizedSchedule.vehicleName}</span>
            </div>
            <div className="flex items-center gap-2">
              <User className="h-3 w-3" />
              <span className="font-medium text-blue-700">{suggestion.optimizedSchedule.driverName}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Benefits */}
      {suggestion.benefits && (
        <div className="mb-4">
          <h5 className="text-sm font-medium text-gray-700 mb-2">Expected Benefits</h5>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
            {suggestion.benefits.timeSaved && (
              <div className="bg-green-100 text-green-700 px-2 py-1 rounded text-xs font-medium">
                ⏰ {suggestion.benefits.timeSaved}
              </div>
            )}
            {suggestion.benefits.fuelEfficiency && (
              <div className="bg-blue-100 text-blue-700 px-2 py-1 rounded text-xs font-medium">
                ⛽ {suggestion.benefits.fuelEfficiency}
              </div>
            )}
            {suggestion.benefits.routeOptimization && (
              <div className="bg-purple-100 text-purple-700 px-2 py-1 rounded text-xs font-medium">
                🗺️ {suggestion.benefits.routeOptimization}
              </div>
            )}
            {suggestion.benefits.driverUtilization && (
              <div className="bg-orange-100 text-orange-700 px-2 py-1 rounded text-xs font-medium">
                👤 {suggestion.benefits.driverUtilization}
              </div>
            )}
          </div>
        </div>
      )}

      {/* AI Reasoning */}
      {suggestion.reasoning && suggestion.reasoning.length > 0 && (
        <div className="mb-4">
          <h5 className="text-sm font-medium text-gray-700 mb-2">Why This Suggestion?</h5>
          <div className="bg-gray-50 rounded p-3">
            <ul className="text-xs text-gray-600 space-y-1">
              {suggestion.reasoning.map((reason, idx) => (
                <li key={idx} className="flex items-start gap-2">
                  <div className="w-1.5 h-1.5 bg-blue-500 rounded-full mt-1.5 flex-shrink-0"></div>
                  <span>{reason}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex gap-2 pt-3 border-t border-gray-100">
        <button
          onClick={onAccept}
          disabled={isProcessing}
          className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-sm font-medium"
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
          className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-sm font-medium"
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