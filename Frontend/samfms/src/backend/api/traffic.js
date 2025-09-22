import { httpClient } from '../services/httpClient';
import { API_ENDPOINTS } from '../../config/apiConfig';

const TRAFFICENDPOINTS = {
  recommendations: API_ENDPOINTS.TRIPS.TRAFFIC.RECOMMENDATIONS,
  recommendation: API_ENDPOINTS.TRIPS.TRAFFIC.RECOMMENDATION,
  accept: API_ENDPOINTS.TRIPS.TRAFFIC.ACCEPT,
  reject: API_ENDPOINTS.TRIPS.TRAFFIC.REJECT,
  startmonitor: API_ENDPOINTS.TRIPS.TRAFFIC.STARTMONITOR,
  stopmonitor: API_ENDPOINTS.TRIPS.TRAFFIC.STOPMONITOR,
  getstatus: API_ENDPOINTS.TRIPS.TRAFFIC.GETSTATUS,
  runcycle: API_ENDPOINTS.TRIPS.TRAFFIC.RUNCYCLE,
  analysi: API_ENDPOINTS.TRIPS.TRAFFIC.ANALYSIS,
  dashboard: API_ENDPOINTS.TRIPS.TRAFFIC.DASHBOARD
};

export const getRouteRecommendations = async () => {
  try {
    const response = await httpClient.get(TRAFFICENDPOINTS.recommendations)
    return response
  } catch (error) {
    console.log('Error fetching recommendations: ', error);
    throw error;
  }
}

export const acceptRouteRecommendation = async (tripId, recommendationId) => {
  try {
    const data = {
      recommendation_id: recommendationId,
      trip_id: tripId
    }
    const response = await httpClient.post(TRAFFICENDPOINTS.acceptRouteRecommendation,data)
    return response
  } catch (error) {
    console.log(`Error accepting recommendations: ${recommendationId}`, error);
    throw error;
  }
}

export const rejectRouteRecommendation = async (tripId, recommendationId) => {
  try {
    const data = {
      recommendation_id: recommendationId,
      trip_id: tripId
    }
    const response = await httpClient.post(TRAFFICENDPOINTS.rejectRouteRecommendation,data)
    return response
  } catch (error) {
    console.log(`Error rejecting recommendations: ${recommendationId}`, error);
    throw error;
  }
}