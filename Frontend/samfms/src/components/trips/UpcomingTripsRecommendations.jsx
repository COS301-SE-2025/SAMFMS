import React, { useState, useEffect, useCallback } from 'react';
import { 
  Route, 
  MapPin, 
  User, 
  Truck, 
  CheckCircle, 
  XCircle, 
  RefreshCw, 
  Calendar,
  Clock,
  TrendingUp,
  AlertCircle,
  Brain,
  ArrowRight,
  Plus,
  Users,
  Timer,
  Target,
  Zap
} from 'lucide-react';

// Expected backend API functions (to be implemented):
import { 
  getUpcomingTripsRecommendations, 
  acceptTripCombinationRecommendation, 
  rejectTripCombinationRecommendation 
} from '../../backend/api/trips';

const UpcomingTripsRecommendations = ({ upcomingTrips, onAccept, onReject, onRefresh }) => {
  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(false);
  const [processingIds, setProcessingIds] = useState(new Set());
  const [error, setError] = useState(null);

  // Fetch trip combination recommendations from backend
  const fetchRecommendations = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await getUpcomingTripsRecommendations();
      console.log("Received upcoming trip recommendations: ", response);

      setRecommendations(response.data.data.data || []);
      
    } catch (error) {
      console.error('Error fetching upcoming trip recommendations:', error);
      setError('Failed to load trip combination recommendations');
      setRecommendations([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (upcomingTrips && upcomingTrips.length > 0) {
      fetchRecommendations();
    }
  }, [upcomingTrips, fetchRecommendations]);

  // Handle accepting a recommendation
  const handleAccept = async (recommendationId) => {
    setProcessingIds(prev => new Set([...prev, recommendationId]));
    
    try {
      const response = await acceptTripCombinationRecommendation(recommendationId);
      console.log("Response for accepting trip combination: ", response);
      
      console.log('Accepting recommendation:', recommendationId);
      
      // Remove accepted recommendation from list
      setRecommendations(prev => prev.filter(r => r.id !== recommendationId));
      
      if (onAccept) {
        onAccept(recommendationId);
      }
    } catch (error) {
      console.error('Error accepting recommendation:', error);
      setError('Failed to accept trip combination');
    } finally {
      setProcessingIds(prev => {
        const newSet = new Set(prev);
        newSet.delete(recommendationId);
        return newSet;
      });
    }
  };

  // Handle rejecting a recommendation
  const handleReject = async (recommendationId) => {
    setProcessingIds(prev => new Set([...prev, recommendationId]));
    
    try {
      const response = await rejectTripCombinationRecommendation(recommendationId);
      console.log("Response for rejecting recommendation: ", response);
      
      console.log('Rejecting recommendation:', recommendationId);
      
      // Remove rejected recommendation from list
      setRecommendations(prev => prev.filter(r => r.id !== recommendationId));
      
      if (onReject) {
        onReject(recommendationId);
      }
    } catch (error) {
      console.error('Error rejecting recommendation:', error);
      setError('Failed to reject trip combination');
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
    fetchRecommendations();
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

  // Calculate time difference between trips
  const calculateTimeBetweenTrips = (firstTripEnd, secondTripStart) => {
    try {
      const endTime = new Date(firstTripEnd);
      const startTime = new Date(secondTripStart);
      const diffMs = startTime.getTime() - endTime.getTime();
      const diffHours = Math.abs(diffMs) / (1000 * 60 * 60);
      
      if (diffHours < 1) {
        const diffMinutes = Math.abs(diffMs) / (1000 * 60);
        return `${Math.round(diffMinutes)}m`;
      }
      
      return `${diffHours.toFixed(1)}h`;
    } catch {
      return 'N/A';
    }
  };

  // Loading state
  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
            <Route className="h-5 w-5 text-purple-600" />
            Trip Combination Recommendations
          </h3>
          <RefreshCw className="h-5 w-5 text-gray-400 animate-spin" />
        </div>
        <div className="flex items-center justify-center py-8">
          <div className="text-center">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600"></div>
            <p className="mt-2 text-sm text-gray-600">Analyzing trip combinations...</p>
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
            <Route className="h-5 w-5 text-purple-600" />
            Trip Combination Recommendations
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
              className="mt-2 px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 transition-colors text-sm"
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
          <Route className="h-5 w-5 text-purple-600" />
          Trip Combination Recommendations
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
          <Plus className="h-12 w-12 text-gray-300 mx-auto mb-4" />
          <p className="text-gray-500 text-sm">
            No trip combination opportunities available.
          </p>
          <p className="text-gray-400 text-xs mt-1">
            AI will analyze upcoming trips for efficient combining possibilities.
          </p>
        </div>
      ) : (
        // Recommendations list
        <div className="space-y-4">
          {recommendations.map((recommendation) => (
            <RecommendationCard
              key={recommendation.id}
              recommendation={recommendation}
              isProcessing={processingIds.has(recommendation.id)}
              onAccept={() => handleAccept(recommendation.id)}
              onReject={() => handleReject(recommendation.id)}
              formatDateTime={formatDateTime}
              calculateTimeBetweenTrips={calculateTimeBetweenTrips}
            />
          ))}
        </div>
      )}
    </div>
  );
};

// Separate component for each recommendation card
const RecommendationCard = ({ 
  recommendation, 
  isProcessing, 
  onAccept, 
  onReject, 
  formatDateTime
}) => {
  return (
    <div className="border border-purple-200 rounded-lg p-4 hover:shadow-md transition-all duration-200 bg-gradient-to-r from-purple-50 to-transparent">
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div>
          <h4 className="font-medium text-gray-900 flex items-center gap-2">
            <Plus className="h-4 w-4 text-purple-600" />
            Combine 2 Trips
          </h4>
          <p className="text-sm text-gray-500">
            Confidence Score: {Math.round(recommendation.confidence_score * 100)}%
          </p>
        </div>
        <div className="flex items-center gap-1 px-2 py-1 bg-purple-100 text-purple-800 rounded-full text-xs font-medium">
          <Brain className="h-3 w-3" />
          AI Recommended
        </div>
      </div>

      {/* Trip Details */}
      <div className="mb-4">
        <div className="flex items-center gap-2 text-sm text-gray-600 mb-3">
          <Route className="h-4 w-4" />
          <span className="font-medium">Trips to Combine</span>
        </div>
        
        <div className="space-y-3">
          {/* Primary Trip */}
          <div className="bg-white border rounded-lg p-3">
            <div className="flex items-center justify-between mb-2">
              <h5 className="font-medium text-gray-800">{recommendation.primary_trip_name}</h5>
              <span className="text-xs bg-blue-100 text-blue-600 px-2 py-1 rounded">
                Primary Trip
              </span>
            </div>
            
            <div className="grid grid-cols-2 gap-4 text-sm text-gray-600">
              <div>
                <div className="flex items-center gap-1 mb-1">
                  <User className="h-3 w-3" />
                  <span className="text-xs font-medium">Driver</span>
                </div>
                <div className="text-xs">{recommendation.recommended_driver}</div>
              </div>
              <div>
                <div className="flex items-center gap-1 mb-1">
                  <Truck className="h-3 w-3" />
                  <span className="text-xs font-medium">Vehicle</span>
                </div>
                <div className="text-xs">{recommendation.recommended_vehicle}</div>
              </div>
            </div>
          </div>

          {/* Connection indicator */}
          <div className="flex justify-center py-1">
            <div className="flex items-center gap-2 text-purple-600">
              <div className="w-8 h-0.5 bg-purple-300"></div>
              <ArrowRight className="h-4 w-4" />
              <div className="w-8 h-0.5 bg-purple-300"></div>
            </div>
            <div className="mx-2 text-xs text-gray-500">
              {recommendation.travel_distance_km?.toFixed(1)} km gap
            </div>
          </div>

          {/* Secondary Trip */}
          <div className="bg-white border rounded-lg p-3">
            <div className="flex items-center justify-between mb-2">
              <h5 className="font-medium text-gray-800">{recommendation.secondary_trip_name}</h5>
              <span className="text-xs bg-green-100 text-green-600 px-2 py-1 rounded">
                Secondary Trip
              </span>
            </div>
            
            <div className="text-sm text-gray-600">
              <div className="flex items-center justify-between">
                <span>Time gap: {recommendation.time_gap_hours?.toFixed(1)} hours</span>
                <span>Travel time: ~{Math.round(recommendation.travel_distance_km / 30 * 60)} min</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Combined Route Benefits */}
      <div className="mb-4">
        <h5 className="text-sm font-medium text-gray-700 mb-2">Expected Benefits</h5>
        <div className="bg-purple-50 border border-purple-200 rounded-lg p-3">
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            <div className="text-center">
              <div className="text-lg font-semibold text-green-600">
                {Math.round(recommendation.benefits?.time_savings_minutes || 0)}min
              </div>
              <div className="text-xs text-gray-600">Time Saved</div>
            </div>
            <div className="text-center">
              <div className="text-lg font-semibold text-blue-600">
                {recommendation.benefits?.distance_savings_km?.toFixed(1) || 0}km
              </div>
              <div className="text-xs text-gray-600">Distance Saved</div>
            </div>
            <div className="text-center">
              <div className="text-lg font-semibold text-purple-600">
                {recommendation.benefits?.fuel_efficiency_improvement || '0%'}
              </div>
              <div className="text-xs text-gray-600">Fuel Efficiency</div>
            </div>
          </div>

          {recommendation.benefits?.cost_savings && (
            <div className="mt-3 pt-3 border-t border-purple-200 text-center">
              <div className="text-sm text-gray-700">
                <strong>{recommendation.benefits.cost_savings}</strong>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* AI Reasoning */}
      {recommendation.reasoning && recommendation.reasoning.length > 0 && (
        <div className="mb-4">
          <h5 className="text-sm font-medium text-gray-700 mb-2">Why Combine These Trips?</h5>
          <div className="bg-gray-50 rounded p-3">
            <ul className="text-xs text-gray-600 space-y-1">
              {recommendation.reasoning.map((reason, idx) => (
                <li key={idx} className="flex items-start gap-2">
                  <div className="w-1.5 h-1.5 bg-purple-500 rounded-full mt-1.5 flex-shrink-0"></div>
                  <span>{reason}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {/* Route Details */}
      {recommendation.combined_route && (
        <div className="mb-4">
          <h5 className="text-sm font-medium text-gray-700 mb-2">Combined Route Details</h5>
          <div className="bg-blue-50 border border-blue-200 rounded p-3">
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-gray-600">Total Distance:</span>
                <div className="font-medium">{(recommendation.combined_route.distance / 1000).toFixed(1)} km</div>
              </div>
              <div>
                <span className="text-gray-600">Total Duration:</span>
                <div className="font-medium">{Math.round(recommendation.combined_route.duration / 60)} minutes</div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex gap-2 pt-3 border-t border-gray-100">
        <button
          onClick={onAccept}
          disabled={isProcessing}
          className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-sm font-medium"
        >
          {isProcessing ? (
            <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
          ) : (
            <CheckCircle className="h-4 w-4" />
          )}
          Combine Trips
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
          Keep Separate
        </button>
      </div>
    </div>
  );
};

export default UpcomingTripsRecommendations;