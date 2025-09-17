import { useState, useCallback, useRef, useEffect } from 'react';
import { WebView } from 'react-native-webview';
import { getLocation, getVehiclePolyline, getLiveTripData } from '../utils/api';

interface VehicleLocation {
  id: string;
  position: [number, number];
  speed: number | null;
  heading: number | null;
  lastUpdated: Date;
}

interface VehicleDataHookReturn {
  vehicleLocation: VehicleLocation | null;
  mapCenter: [number, number];
  isWebViewLoaded: boolean;
  liveInstruction: string;
  liveInstructionDistance: number | null;
  liveSpeed: number | null;
  liveSpeedLimit: number | null;
  currentRoadName: string | null;
  setIsWebViewLoaded: (loaded: boolean) => void;
  fetchVehicleData: () => Promise<void>;
  handleWebViewLoad: () => void;
  webViewRef: React.RefObject<WebView | null>;
}

export const useVehicleData = (
  activeTrip: any,
  currentSpeed: number,
  _directions: any[],
  _currentDirectionIndex: number
): VehicleDataHookReturn => {
  const [vehicleLocation, setVehicleLocation] = useState<VehicleLocation | null>(null);
  const [mapCenter, setMapCenter] = useState<[number, number]>([37.7749, -122.4194]);
  const [isWebViewLoaded, setIsWebViewLoaded] = useState(false);
  const [liveInstruction, setLiveInstruction] = useState<string>('');
  const [liveInstructionDistance, setLiveInstructionDistance] = useState<number | null>(null);
  const [liveSpeed, setLiveSpeed] = useState<number | null>(null);
  const [liveSpeedLimit, setLiveSpeedLimit] = useState<number | null>(null);
  const [currentRoadName, setCurrentRoadName] = useState<string | null>(null);
  const [_previousVehicleLocation, setPreviousVehicleLocation] = useState<{
    latitude: number;
    longitude: number;
    timestamp: number;
  } | null>(null);

  const webViewRef = useRef<WebView>(null);
  const webViewLoadAttempts = useRef(0);

  const fetchVehicleData = useCallback(async () => {
    // First try to use live tracking if we have a trip ID
    if (activeTrip?.id || activeTrip?._id) {
      const tripId = activeTrip.id || activeTrip._id;

      try {
        // Use the new live tracking endpoint
        const liveDataResponse = await getLiveTripData(tripId);

        if (liveDataResponse?.data?.data) {
          const liveData = liveDataResponse.data.data;
          console.log('Live tracking data received:', liveData); // Debug log
          console.log('Current instruction from API:', liveData.current_instruction); // Debug current instruction specifically

          // Extract current position from live data
          let location = null;
          if (liveData.current_position) {
            const pos = liveData.current_position;
            location = {
              id: liveData.vehicle_id,
              position: [pos.latitude, pos.longitude] as [number, number],
              speed: pos.speed || null,
              heading: pos.bearing || null,
              lastUpdated: new Date(pos.timestamp || Date.now()),
            };

            // DEBUG: Log the live vehicle position being sent to map
            console.log('🚗 LIVE VEHICLE POSITION (sent to map):', {
              latitude: pos.latitude,
              longitude: pos.longitude,
              coordinates: [pos.latitude, pos.longitude],
              speed: pos.speed,
              timestamp: pos.timestamp,
            });
          }

          // Extract route polyline - prefer remaining polyline for live navigation
          let polyline = null;

          if (liveData.remaining_polyline && Array.isArray(liveData.remaining_polyline)) {
            polyline = liveData.remaining_polyline.map((point: any) => [
              point[0], // latitude
              point[1], // longitude
            ]);
          } else if (liveData.route_polyline && Array.isArray(liveData.route_polyline)) {
            polyline = liveData.route_polyline.map((point: any) => [
              point[0], // latitude
              point[1], // longitude
            ]);
          }

          // Update state and WebView with live data (only if values actually changed)
          if (location) {
            // Only update if location has actually changed significantly
            const hasSignificantChange =
              !vehicleLocation ||
              Math.abs(location.position[0] - vehicleLocation.position[0]) > 0.0001 ||
              Math.abs(location.position[1] - vehicleLocation.position[1]) > 0.0001 ||
              Math.abs((location.speed || 0) - (vehicleLocation.speed || 0)) > 1;

            if (hasSignificantChange) {
              setVehicleLocation(location);
              setMapCenter(location.position as [number, number]);
              // Extract and set live speed from current position
              setLiveSpeed(location.speed);
            }
          }

          // Extract and set speed limit from current instruction (only if changed)
          if (liveData.current_instruction && liveData.current_instruction.speed_limit) {
            const newSpeedLimit = liveData.current_instruction.speed_limit;
            if (newSpeedLimit !== liveSpeedLimit) {
              setLiveSpeedLimit(newSpeedLimit);
            }
          }

          console.log('Live speed and speed limit extracted:', {
            speed: location?.speed,
            speedLimit: liveData.current_instruction?.speed_limit,
          }); // Debug log

          console.log('WebView state:', {
            webViewRefCurrent: webViewRef.current,
            isWebViewLoaded,
            hasLocation: !!location,
            hasPolyline: !!polyline,
          }); // Debug log

          // Send update to WebView with live data
          if (webViewRef.current && isWebViewLoaded && (location || polyline)) {
            console.log('Sending update to WebView:', {
              location,
              polyline,
              webViewRef: webViewRef.current,
            }); // Debug log
            let script = '';

            if (location) {
              const vehicleHeading = location.heading || 0;

              script += `
                try {
                  window.ReactNativeWebView.postMessage(JSON.stringify({
                    type: 'debug',
                    message: 'Updating vehicle marker with position: [${location.position[0]}, ${
                location.position[1]
              }]'
                  }));
                  
                  if (typeof vehicleMarker !== 'undefined' && vehicleMarker && typeof map !== 'undefined') {
                    vehicleMarker.setLatLng([${location.position[0]}, ${location.position[1]}]);
                    vehicleMarker.setPopupContent('<b>Live Vehicle Position</b><br>Speed: ${Math.round(
                      location.speed || 0
                    )} km/h<br>Heading: ${vehicleHeading}°');
                    
                    // Rotate the vehicle marker to show direction of travel
                    if (typeof vehicleMarker.setRotationAngle === 'function') {
                      vehicleMarker.setRotationAngle(${vehicleHeading});
                    } else if (vehicleMarker._icon) {
                      // Fallback: rotate the marker icon using CSS
                      vehicleMarker._icon.style.transform = 'rotate(${vehicleHeading}deg)';
                      vehicleMarker._icon.style.transformOrigin = 'center';
                    }
                    
                    map.setView([${location.position[0]}, ${location.position[1]}], 16, {
                      animate: true,
                      duration: 1.0
                    });
                    
                    window.ReactNativeWebView.postMessage(JSON.stringify({
                      type: 'debug',
                      message: 'Vehicle marker updated successfully'
                    }));
                  } else {
                    window.ReactNativeWebView.postMessage(JSON.stringify({
                      type: 'error',
                      message: 'vehicleMarker or map not available - vehicleMarker: ' + (typeof vehicleMarker !== 'undefined' ? 'defined' : 'undefined') + ', map: ' + (typeof map !== 'undefined' ? 'defined' : 'undefined')
                    }));
                  }
                } catch (error) {
                  window.ReactNativeWebView.postMessage(JSON.stringify({
                    type: 'error',
                    message: 'Error updating vehicle marker: ' + error.message
                  }));
                }
              `;
            }

            if (polyline) {
              script += `
                try {
                  window.ReactNativeWebView.postMessage(JSON.stringify({
                    type: 'debug',
                    message: 'Updating route polyline with ' + ${
                      JSON.stringify(polyline).length
                    } + ' coordinates'
                  }));
                  
                  if (typeof routePolyline !== 'undefined' && routePolyline) {
                    routePolyline.setLatLngs(${JSON.stringify(polyline)});
                    window.ReactNativeWebView.postMessage(JSON.stringify({
                      type: 'debug',
                      message: 'Route polyline updated successfully'
                    }));
                  } else {
                    window.ReactNativeWebView.postMessage(JSON.stringify({
                      type: 'error',
                      message: 'routePolyline not available'
                    }));
                  }
                } catch (error) {
                  window.ReactNativeWebView.postMessage(JSON.stringify({
                    type: 'error',
                    message: 'Error updating route polyline: ' + error.message
                  }));
                }
              `;
            }

            // Update directions from live data
            if (liveData.current_instruction) {
              const instruction = liveData.current_instruction;
              console.log('Live instruction data received:', {
                text: instruction.text,
                type: instruction.type,
                distance_to_instruction: instruction.distance_to_instruction,
                road_name: instruction.road_name,
                speed_limit: instruction.speed_limit,
                fullInstruction: instruction,
              });

              // Use instruction text if available, otherwise show current road
              const displayInstruction =
                instruction.text ||
                (instruction.road_name ? `Continue on ${instruction.road_name}` : 'Continue');

              setLiveInstruction(displayInstruction);
              setCurrentRoadName(instruction.road_name || null);
              setLiveSpeedLimit(instruction.speed_limit || null);
              setLiveInstructionDistance(
                instruction.distance_to_instruction
                  ? instruction.distance_to_instruction * 1000
                  : null
              );
            }

            if (script) {
              console.log('About to inject script:', script.substring(0, 200) + '...');
              webViewRef.current.injectJavaScript(`
                try {
                  window.ReactNativeWebView.postMessage(JSON.stringify({
                    type: 'debug',
                    message: 'Script execution started in WebView'
                  }));
                  ${script}
                  window.ReactNativeWebView.postMessage(JSON.stringify({
                    type: 'debug',
                    message: 'Script execution completed in WebView'
                  }));
                } catch (error) {
                  window.ReactNativeWebView.postMessage(JSON.stringify({
                    type: 'error',
                    message: 'Script execution error: ' + error.message
                  }));
                }
              `);
            }
          }

          // If live tracking worked, return early
          return;
        }
      } catch (err) {
        // Silently fallback to vehicle location API if live tracking fails
      }
    }

    // Fallback to original implementation if live tracking fails or no trip ID
    if (!activeTrip?.vehicle_id && !activeTrip?.vehicleId) return;

    const vehicleId = activeTrip.vehicle_id || activeTrip.vehicleId;
    if (!vehicleId) return;

    try {
      // Inline vehicle location fetching to avoid dependency issues
      const locationResponse = await getLocation(vehicleId);
      let location = null;
      if (locationResponse && locationResponse.data.data) {
        const locationData = locationResponse.data.data;
        location = {
          id: vehicleId,
          position: [
            locationData.latitude || locationData.lat,
            locationData.longitude || locationData.lng,
          ] as [number, number],
          speed: locationData.speed || null,
          heading: locationData.heading || locationData.direction || null,
          lastUpdated: new Date(locationData.timestamp || Date.now()),
        };
      }

      // Inline polyline fetching
      const polylineResponse = await getVehiclePolyline(vehicleId);
      let polyline = null;
      let polylineStatus = 'live'; // 'live', 'fallback', or 'mock'

      if (polylineResponse && polylineResponse.data) {
        const polylineData = polylineResponse.data.data || polylineResponse.data;
        if (Array.isArray(polylineData)) {
          polyline = polylineData.map((point: any) => [
            point.latitude || point.lat || point[0],
            point.longitude || point.lng || point[1],
          ]);

          // Check if this is fallback data
          if (polylineResponse.fallback) {
            polylineStatus =
              polylineResponse.fallback_reason === 'no_previous_polyline' ? 'mock' : 'fallback';
          }
        }
      }

      // Update state for UI display
      if (location) {
        setVehicleLocation(location);
        setMapCenter(location.position as [number, number]);

        // Calculate speed using vehicle timestamps
        const vehicleTimestamp =
          location.lastUpdated instanceof Date
            ? location.lastUpdated.getTime()
            : new Date(location.lastUpdated).getTime();

        // Get current previous location state
        setPreviousVehicleLocation(prev => {
          if (!prev) {
            // Set initial vehicle location without calculating speed
            return {
              latitude: location.position[0], // latitude
              longitude: location.position[1], // longitude
              timestamp: vehicleTimestamp,
            };
          } else {
            // Return new previous location for next calculation
            return {
              latitude: location.position[0], // latitude
              longitude: location.position[1], // longitude
              timestamp: vehicleTimestamp,
            };
          }
        });
      }

      // Send update to WebView using injectJavaScript for more reliable delivery
      if (webViewRef.current && isWebViewLoaded && (location || polyline)) {
        let script = '';

        if (location) {
          // Calculate rotation for vehicle marker only
          const vehicleHeading = location.heading || 0;

          script += `
            if (typeof vehicleMarker !== 'undefined' && vehicleMarker && typeof map !== 'undefined') {
              vehicleMarker.setLatLng([${location.position[0]}, ${location.position[1]}]);
              vehicleMarker.setPopupContent('<b>Vehicle Position</b><br>Speed: ${Math.round(
                currentSpeed
              )} km/h<br>Heading: ${location.heading || 0}°');
              
              // Rotate the vehicle marker to show direction of travel
              if (typeof vehicleMarker.setRotationAngle === 'function') {
                vehicleMarker.setRotationAngle(${vehicleHeading});
              } else if (vehicleMarker._icon) {
                // Fallback: rotate the marker icon using CSS
                vehicleMarker._icon.style.transform = 'rotate(${vehicleHeading}deg)';
                vehicleMarker._icon.style.transformOrigin = 'center';
              }
              
              // Center map on vehicle location (keep map north-up orientation)
              map.setView([${location.position[0]}, ${location.position[1]}], 16, {
                animate: true,
                duration: 1.0
              });
              
            }
          `;
        }

        if (polyline) {
          const polylineString = JSON.stringify(polyline);
          script += `
            if (typeof routePolyline !== 'undefined' && routePolyline) {
              routePolyline.setLatLngs(${polylineString});
            }
          `;
        }

        // Update polyline status indicator
        script += `
          if (typeof updatePolylineStatusIndicator === 'function') {
            updatePolylineStatusIndicator('${polylineStatus}', ${
          polylineStatus === 'fallback' ? polylineResponse.fallback_age_minutes || 0 : 0
        });
          }
        `;

        if (script) {
          webViewRef.current.injectJavaScript(script);
        }
      } else {
        webViewLoadAttempts.current += 1;
        const currentAttempts = webViewLoadAttempts.current;

        // If we've tried 3 times and WebView still not loaded, force it
        if (currentAttempts >= 3 && !isWebViewLoaded) {
          setIsWebViewLoaded(true);
          // Retry sending the update
          if (webViewRef.current && (location || polyline)) {
            let script = '';

            if (location) {
              // Calculate rotation for vehicle marker only
              const vehicleHeading = location.heading || 0;
              script += `
                if (typeof vehicleMarker !== 'undefined' && vehicleMarker && typeof map !== 'undefined') {
                  vehicleMarker.setLatLng([${location.position[0]}, ${location.position[1]}]);
                  vehicleMarker.setPopupContent('<b>Vehicle Position</b><br>Speed: ${Math.round(
                    currentSpeed
                  )} km/h<br>Heading: ${location.heading || 0}°');
                  
                  // Rotate the vehicle marker to show direction of travel
                  if (typeof vehicleMarker.setRotationAngle === 'function') {
                    vehicleMarker.setRotationAngle(${vehicleHeading});
                  } else if (vehicleMarker._icon) {
                    // Fallback: rotate the marker icon using CSS
                    vehicleMarker._icon.style.transform = 'rotate(${vehicleHeading}deg)';
                    vehicleMarker._icon.style.transformOrigin = 'center';
                  }
                  
                  // Center map on vehicle location (keep map north-up orientation)
                  map.setView([${location.position[0]}, ${location.position[1]}], 16, {
                    animate: true,
                    duration: 1.0
                  });
                  
                }
              `;
            }

            if (polyline) {
              const polylineString = JSON.stringify(polyline);
              script += `
                if (typeof routePolyline !== 'undefined' && routePolyline) {
                  routePolyline.setLatLngs(${polylineString});
                }
              `;
            }

            // Update polyline status indicator in retry logic too
            script += `
              if (typeof updatePolylineStatusIndicator === 'function') {
                updatePolylineStatusIndicator('${polylineStatus}', ${
              polylineStatus === 'fallback' ? polylineResponse.fallback_age_minutes || 0 : 0
            });
              }
            `;

            if (script) {
              webViewRef.current.injectJavaScript(script);
            }
          }
        }
      }
    } catch (err) {
      // Silently handle vehicle data fetch errors
    }
  }, [
    activeTrip?.id,
    activeTrip?._id,
    activeTrip?.vehicle_id,
    activeTrip?.vehicleId,
    isWebViewLoaded,
    currentSpeed,
    liveSpeedLimit,
    vehicleLocation,
  ]);

  // Handle WebView load - fetch initial vehicle data
  const handleWebViewLoad = useCallback(() => {
    setIsWebViewLoaded(true);
    // Fetch initial vehicle data when WebView is ready
    setTimeout(() => {
      fetchVehicleData();
    }, 500); // Small delay to ensure WebView is fully initialized
  }, [fetchVehicleData]);

  // Backup mechanism - if WebView doesn't load within 10 seconds, force it to be ready
  useEffect(() => {
    const backupTimer = setTimeout(() => {
      if (!isWebViewLoaded) {
        console.log('Forcing WebView to be ready due to timeout');
        setIsWebViewLoaded(true);
        // Try to fetch vehicle data anyway
        fetchVehicleData();
      }
    }, 10000); // 10 seconds timeout

    return () => clearTimeout(backupTimer);
  }, [isWebViewLoaded, fetchVehicleData]);

  return {
    vehicleLocation,
    mapCenter,
    isWebViewLoaded,
    liveInstruction,
    liveInstructionDistance,
    liveSpeed,
    liveSpeedLimit,
    currentRoadName,
    setIsWebViewLoaded,
    fetchVehicleData,
    handleWebViewLoad,
    webViewRef,
  };
};
