import React, { useState, useEffect, useCallback } from 'react';
import { 
  Clock, 
  MapPin, 
  Truck, 
  CheckCircle, 
  XCircle, 
  RefreshCw, 
  Route,
  AlertTriangle,
  TrendingUp,
  AlertCircle,
  ArrowRight,
  Navigation,
  Timer
} from 'lucide-react';

// Expected backend API functions for traffic monitoring
import { 
  getRouteRecommendations, 
  acceptRouteRecommendation, 
  rejectRouteRecommendation 
} from '../../backend/api/traffic';

const RouteRecommendations = ({ activeTrips, onAccept, onReject, onRefresh }) => {
  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(false);
  const [processingIds, setProcessingIds] = useState(new Set());
  const [error, setError] = useState(null);

  // Fetch route recommendations from backend
  const fetchRouteRecommendations = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      // Get all pending route recommendations
      const response = await getRouteRecommendations();
      console.log("Received route recommendations:", response);

      // Filter recommendations for active trips only
      const activeRouteRecommendations = response.data?.filter(rec => 
        activeTrips.some(trip => trip.id === rec.trip_id)
      ) || [];

      setRecommendations(activeRouteRecommendations);
      
    } catch (error) {
      console.error('Error fetching route recommendations:', error);
      setError('Failed to load route recommendations');
      setRecommendations([]);
    } finally {
      setLoading(false);
    }
  }, [activeTrips]);

  useEffect(() => {
    if (activeTrips.length > 0) {
      fetchRouteRecommendations();
    }
  }, [fetchRouteRecommendations, activeTrips]);

  // Handle accepting a recommendation
  const handleAccept = async (tripId, recommendationId) => {
    setProcessingIds(prev => new Set([...prev, recommendationId]));
    
    try {
      const response = await acceptRouteRecommendation(tripId, recommendationId);
      console.log("Response for accepting route recommendation:", response);
      
      // Remove accepted recommendation from list
      setRecommendations(prev => prev.filter(r => r.id !== recommendationId));
      
      if (onAccept) {
        onAccept(tripId, recommendationId);
      }
    } catch (error) {
      console.error('Error accepting route recommendation:', error);
      setError('Failed to accept route recommendation');
    } finally {
      setProcessingIds(prev => {
        const newSet = new Set(prev);
        newSet.delete(recommendationId);
        return newSet;
      });
    }
  };

  // Handle rejecting a recommendation
  const handleReject = async (tripId, recommendationId) => {
    setProcessingIds(prev => new Set([...prev, recommendationId]));
    
    try {
      const response = await rejectRouteRecommendation(tripId, recommendationId);
      console.log("Response for rejecting route recommendation:", response);
      
      // Remove rejected recommendation from list
      setRecommendations(prev => prev.filter(r => r.id !== recommendationId));
      
      if (onReject) {
        onReject(tripId, recommendationId);
      }
    } catch (error) {
      console.error('Error rejecting route recommendation:', error);
      setError('Failed to reject route recommendation');
    } finally {
      setProcessingIds(prev => {
        const newSet = new Set(prev);
        newSet.delete(recommendationId);
        return newSet;
      });
    }
  };

  // Handle refresh
  const handleRefresh = () => {
    fetchRouteRecommendations();
    if (onRefresh) {
      onRefresh();
    }
  };

  // Format time savings for display
  const formatTimeSavings = (seconds) => {
    const minutes = Math.round(seconds / 60);
    if (minutes < 60) {
      return `${minutes} min`;
    }
    const hours = Math.floor(minutes / 60);
    const remainingMinutes = minutes % 60;
    return `${hours}h ${remainingMinutes}m`;
  };

  // Get traffic severity color and icon
  const getTrafficSeverityDisplay = (severity) => {
    const severityMap = {
      light: { color: 'text-green-600', bgColor: 'bg-green-100', icon: '🟢' },
      moderate: { color: 'text-yellow-600', bgColor: 'bg-yellow-100', icon: '🟡' },
      heavy: { color: 'text-orange-600', bgColor: 'bg-orange-100', icon: '🟠' },
      severe: { color: 'text-red-600', bgColor: 'bg-red-100', icon: '🔴' }
    };
    return severityMap[severity] || severityMap.moderate;
  };

  // Find active trip details for a recommendation
  const getActiveTrip = (tripId) => {
    return activeTrips.find(trip => trip.id === tripId);
  };

  // Loading state
  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
            <Navigation className="h-5 w-5 text-orange-600" />
            Route Optimization Suggestions
          </h3>
          <RefreshCw className="h-5 w-5 text-gray-400 animate-spin" />
        </div>
        <div className="flex items-center justify-center py-8">
          <div className="text-center">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-orange-600"></div>
            <p className="mt-2 text-sm text-gray-600">Analyzing traffic conditions...</p>
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
            <Navigation className="h-5 w-5 text-orange-600" />
            Route Optimization Suggestions
          </h3>
          <button
            onClick={handleRefresh}
            className="p-2 text-gray-400 hover:text-gray-600 transition-colors"
            title="Refresh recommendations"
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
              className="mt-2 px-4 py-2 bg-orange-600 text-white rounded-md hover:bg-orange-700 transition-colors text-sm"
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
          <Navigation className="h-5 w-5 text-orange-600" />
          Route Optimization Suggestions
          {recommendations.length > 0 && (
            <span className="ml-2 bg-orange-100 text-orange-800 text-xs font-medium px-2.5 py-0.5 rounded-full">
              {recommendations.length}
            </span>
          )}
        </h3>
        <button
          onClick={handleRefresh}
          className="p-2 text-gray-400 hover:text-gray-600 transition-colors"
          title="Refresh recommendations"
        >
          <RefreshCw className="h-5 w-5" />
        </button>
      </div>

      {recommendations.length === 0 ? (
        // Empty state
        <div className="text-center py-8">
          <Route className="h-12 w-12 text-gray-300 mx-auto mb-4" />
          <p className="text-gray-500 text-sm">
            No route optimizations available at the moment.
          </p>
          <p className="text-gray-400 text-xs mt-1">
            AI monitors active trips and suggests faster routes when traffic conditions change.
          </p>
        </div>
      ) : (
        // Recommendations list
        <div className="space-y-4">
          {recommendations.map((recommendation) => (
            <RouteRecommendationCard
              key={recommendation.id}
              recommendation={recommendation}
              activeTrip={getActiveTrip(recommendation.trip_id)}
              isProcessing={processingIds.has(recommendation.id)}
              onAccept={() => handleAccept(recommendation.trip_id, recommendation.id)}
              onReject={() => handleReject(recommendation.trip_id, recommendation.id)}
              formatTimeSavings={formatTimeSavings}
              getTrafficSeverityDisplay={getTrafficSeverityDisplay}
            />
          ))}
        </div>
      )}
    </div>
  );
};

// Separate component for each recommendation card
const RouteRecommendationCard = ({ 
  recommendation, 
  activeTrip,
  isProcessing, 
  onAccept, 
  onReject, 
  formatTimeSavings,
  getTrafficSeverityDisplay
}) => {
  const trafficDisplay = getTrafficSeverityDisplay(recommendation.traffic_avoided);
  
  return (
    <div className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-all duration-200">
      {/* Header with Trip Info */}
      <div className="flex items-start justify-between mb-3">
        <div>
          <h4 className="font-medium text-gray-900 flex items-center gap-2">
            <Truck className="h-4 w-4" />
            {activeTrip?.vehicleName || 'Vehicle'} - {activeTrip?.driver || 'Driver'}
          </h4>
          <p className="text-sm text-gray-500">Trip ID: {recommendation.trip_id}</p>
          <p className="text-sm text-gray-600 mt-1">{activeTrip?.destination || 'Destination'}</p>
        </div>
        <div className="flex items-center gap-2">
          <div className={`flex items-center gap-1 px-2 py-1 ${trafficDisplay.bgColor} ${trafficDisplay.color} rounded-full text-xs font-medium`}>
            <AlertTriangle className="h-3 w-3" />
            {recommendation.traffic_avoided.toUpperCase()} TRAFFIC
          </div>
          <div className="flex items-center gap-1 px-2 py-1 bg-blue-100 text-blue-800 rounded-full text-xs font-medium">
            <TrendingUp className="h-3 w-3" />
            {Math.round(recommendation.confidence * 100)}%
          </div>
        </div>
      </div>

      {/* Traffic Alert Banner */}
      <div className={`${trafficDisplay.bgColor} border-l-4 border-${recommendation.traffic_avoided === 'severe' ? 'red' : recommendation.traffic_avoided === 'heavy' ? 'orange' : 'yellow'}-500 p-3 rounded mb-4`}>
        <div className="flex items-center gap-2">
          <AlertTriangle className={`h-4 w-4 ${trafficDisplay.color}`} />
          <span className="text-sm font-medium text-gray-900">Traffic Detected</span>
        </div>
        <p className="text-sm text-gray-700 mt-1">{recommendation.reason}</p>
      </div>

      {/* Route Comparison */}
      <div className="grid md:grid-cols-2 gap-4 mb-4">
        {/* Current Route Status */}
        <div className="bg-red-50 border-l-4 border-red-400 p-3 rounded">
          <h5 className="text-sm font-medium text-red-700 mb-2 flex items-center gap-1">
            <Route className="h-3 w-3" />
            Current Route
          </h5>
          <div className="space-y-1 text-sm text-gray-600">
            <div className="flex items-center justify-between">
              <span>Status:</span>
              <span className={`font-medium ${trafficDisplay.color}`}>
                {trafficDisplay.icon} {recommendation.traffic_avoided.toUpperCase()} Traffic
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span>Progress:</span>
              <span>{activeTrip?.progress || 0}% Complete</span>
            </div>
          </div>
        </div>

        {/* Optimized Route */}
        <div className="bg-green-50 border-l-4 border-green-500 p-3 rounded">
          <h5 className="text-sm font-medium text-green-700 mb-2 flex items-center gap-1">
            <Navigation className="h-3 w-3" />
            Optimized Route
          </h5>
          <div className="space-y-1 text-sm text-gray-600">
            <div className="flex items-center justify-between">
              <span>Time Saved:</span>
              <span className="font-medium text-green-600">
                {formatTimeSavings(recommendation.time_savings)}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span>Distance:</span>
              <span>{(recommendation.recommended_route?.distance / 1000).toFixed(1)} km</span>
            </div>
          </div>
        </div>
      </div>

      {/* Route Details */}
      <div className="mb-4">
        <div className="flex items-center gap-2 text-sm text-gray-600 mb-2">
          <MapPin className="h-4 w-4" />
          <span className="font-medium">Route Information</span>
        </div>
        <div className="ml-6 bg-gray-50 rounded p-3">
          <div className="grid grid-cols-3 gap-4 text-sm">
            <div>
              <span className="text-gray-500">New Distance:</span>
              <p className="font-medium">{(recommendation.recommended_route?.distance / 1000).toFixed(1)} km</p>
            </div>
            <div>
              <span className="text-gray-500">Est. Duration:</span>
              <p className="font-medium">{Math.round(recommendation.recommended_route?.duration / 60)} min</p>
            </div>
            <div>
              <span className="text-gray-500">Time Savings:</span>
              <p className="font-medium text-green-600">{formatTimeSavings(recommendation.time_savings)}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Benefits Summary */}
      <div className="mb-4">
        <h5 className="text-sm font-medium text-gray-700 mb-2">Expected Benefits</h5>
        <div className="flex flex-wrap gap-2">
          <div className="bg-green-100 text-green-700 px-2 py-1 rounded text-xs font-medium">
            <Timer className="h-3 w-3 inline mr-1" />
            Save {formatTimeSavings(recommendation.time_savings)}
          </div>
          <div className="bg-blue-100 text-blue-700 px-2 py-1 rounded text-xs font-medium">
            <Route className="h-3 w-3 inline mr-1" />
            Avoid {recommendation.traffic_avoided} traffic
          </div>
          <div className="bg-purple-100 text-purple-700 px-2 py-1 rounded text-xs font-medium">
            <TrendingUp className="h-3 w-3 inline mr-1" />
            {Math.round(recommendation.confidence * 100)}% confidence
          </div>
        </div>
      </div>

      {/* Timestamp */}
      <div className="text-xs text-gray-500 mb-4">
        <Clock className="h-3 w-3 inline mr-1" />
        Recommendation generated: {new Date(recommendation.created_at).toLocaleString()}
      </div>

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
          Accept New Route
        </button>
        <button
          onClick={onReject}
          disabled={isProcessing}
          className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-sm font-medium"
        >
          {isProcessing ? (
            <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
          ) : (
            <XCircle className="h-4 w-4" />
          )}
          Keep Current Route
        </button>
      </div>
    </div>
  );
};

export default RouteRecommendations;