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

      setRecommendations(response.data.data || []);
      
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
  formatDateTime, 
  calculateTimeBetweenTrips 
}) => {
  return (
    <div className="border border-purple-200 rounded-lg p-4 hover:shadow-md transition-all duration-200 bg-gradient-to-r from-purple-50 to-transparent">
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div>
          <h4 className="font-medium text-gray-900 flex items-center gap-2">
            <Plus className="h-4 w-4 text-purple-600" />
            Combine {recommendation.trips.length} Trips
          </h4>
          <p className="text-sm text-gray-500">
            Efficiency Score: {recommendation.efficiency_score}%
          </p>
        </div>
        <div className="flex items-center gap-1 px-2 py-1 bg-purple-100 text-purple-800 rounded-full text-xs font-medium">
          <Brain className="h-3 w-3" />
          {recommendation.confidence}% confidence
        </div>
      </div>

      {/* Trip Details */}
      <div className="mb-4">
        <div className="flex items-center gap-2 text-sm text-gray-600 mb-3">
          <Route className="h-4 w-4" />
          <span className="font-medium">Trips to Combine</span>
        </div>
        
        <div className="space-y-3">
          {recommendation.trips.map((trip, index) => (
            <div key={trip.id}>
              <div className="bg-white border rounded-lg p-3">
                <div className="flex items-center justify-between mb-2">
                  <h5 className="font-medium text-gray-800">{trip.name}</h5>
                  <span className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded">
                    Trip {index + 1}
                  </span>
                </div>
                
                {/* Route Info */}
                <div className="flex items-center gap-2 text-sm text-gray-600 mb-2">
                  <div className="flex items-center gap-1">
                    <MapPin className="h-3 w-3 text-green-500" />
                    <span>{trip.origin?.name || 'Origin'}</span>
                  </div>
                  <ArrowRight className="h-3 w-3 text-gray-400" />
                  <div className="flex items-center gap-1">
                    <MapPin className="h-3 w-3 text-red-500" />
                    <span>{trip.destination?.name || 'Destination'}</span>
                  </div>
                </div>

                {/* Schedule and Resources */}
                <div className="grid grid-cols-2 gap-4 text-sm text-gray-600">
                  <div>
                    <div className="flex items-center gap-1 mb-1">
                      <Calendar className="h-3 w-3" />
                      <span className="text-xs font-medium">Schedule</span>
                    </div>
                    <div className="text-xs">
                      <div>Start: {formatDateTime(trip.scheduled_start_time)}</div>
                      <div>End: {formatDateTime(trip.scheduled_end_time)}</div>
                    </div>
                  </div>
                  <div>
                    <div className="flex items-center gap-1 mb-1">
                      <User className="h-3 w-3" />
                      <span className="text-xs font-medium">Resources</span>
                    </div>
                    <div className="text-xs">
                      <div>Vehicle: {trip.vehicle_name || 'TBD'}</div>
                      <div>Driver: {trip.driver_name || 'TBD'}</div>
                    </div>
                  </div>
                </div>

                {/* Distance between trips */}
                {index < recommendation.trips.length - 1 && (
                  <div className="mt-2 pt-2 border-t border-gray-100">
                    <div className="flex justify-between items-center text-xs text-gray-500">
                      <span>Distance to next trip: {recommendation.distances_between_trips[index]?.toFixed(1)} km</span>
                      <span>Travel time: {Math.round(recommendation.travel_times_between_trips[index] || 0)} min</span>
                      <span>Gap: {calculateTimeBetweenTrips(trip.scheduled_end_time, recommendation.trips[index + 1]?.scheduled_start_time)}</span>
                    </div>
                  </div>
                )}
              </div>
              
              {/* Connector arrow for visual flow */}
              {index < recommendation.trips.length - 1 && (
                <div className="flex justify-center py-2">
                  <div className="flex items-center gap-2 text-purple-600">
                    <div className="w-8 h-0.5 bg-purple-300"></div>
                    <ArrowRight className="h-4 w-4" />
                    <div className="w-8 h-0.5 bg-purple-300"></div>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Combined Trip Benefits */}
      <div className="mb-4">
        <h5 className="text-sm font-medium text-gray-700 mb-2">Proposed Combined Route</h5>
        <div className="bg-purple-50 border border-purple-200 rounded-lg p-3">
          <div className="grid md:grid-cols-2 gap-4 mb-3">
            <div>
              <div className="flex items-center gap-2 text-sm text-gray-600 mb-2">
                <Truck className="h-4 w-4 text-purple-600" />
                <span className="font-medium">Assigned Resources</span>
              </div>
              <div className="text-sm text-gray-700">
                <div>Vehicle: {recommendation.assigned_vehicle?.name || 'TBD'}</div>
                <div>Driver: {recommendation.assigned_driver?.name || 'TBD'}</div>
              </div>
            </div>
            <div>
              <div className="flex items-center gap-2 text-sm text-gray-600 mb-2">
                <Timer className="h-4 w-4 text-purple-600" />
                <span className="font-medium">Timeline</span>
              </div>
              <div className="text-sm text-gray-700">
                <div>Total Duration: {Math.round(recommendation.total_duration / 60)} hours</div>
                <div>Total Distance: {recommendation.total_distance?.toFixed(1)} km</div>
              </div>
            </div>
          </div>

          {/* Benefits */}
          {recommendation.benefits && (
            <div>
              <h6 className="text-sm font-medium text-gray-700 mb-2">Expected Benefits</h6>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                {recommendation.benefits.driver_efficiency && (
                  <div className="bg-green-100 text-green-700 px-2 py-1 rounded text-xs font-medium">
                    <Users className="h-3 w-3 inline mr-1" />
                    {recommendation.benefits.driver_efficiency}
                  </div>
                )}
                {recommendation.benefits.fuel_savings && (
                  <div className="bg-blue-100 text-blue-700 px-2 py-1 rounded text-xs font-medium">
                    <Target className="h-3 w-3 inline mr-1" />
                    {recommendation.benefits.fuel_savings}
                  </div>
                )}
                {recommendation.benefits.time_optimization && (
                  <div className="bg-purple-100 text-purple-700 px-2 py-1 rounded text-xs font-medium">
                    <Clock className="h-3 w-3 inline mr-1" />
                    {recommendation.benefits.time_optimization}
                  </div>
                )}
                {recommendation.benefits.resource_utilization && (
                  <div className="bg-orange-100 text-orange-700 px-2 py-1 rounded text-xs font-medium">
                    <TrendingUp className="h-3 w-3 inline mr-1" />
                    {recommendation.benefits.resource_utilization}
                  </div>
                )}
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

      {/* Constraints and Considerations */}
      {recommendation.constraints && recommendation.constraints.length > 0 && (
        <div className="mb-4">
          <h5 className="text-sm font-medium text-gray-700 mb-2">Important Considerations</h5>
          <div className="bg-yellow-50 border border-yellow-200 rounded p-3">
            <ul className="text-xs text-yellow-800 space-y-1">
              {recommendation.constraints.map((constraint, idx) => (
                <li key={idx} className="flex items-start gap-2">
                  <AlertCircle className="w-3 h-3 mt-0.5 flex-shrink-0" />
                  <span>{constraint}</span>
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