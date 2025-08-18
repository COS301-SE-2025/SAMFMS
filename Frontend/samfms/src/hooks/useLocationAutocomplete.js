import { useState } from 'react';

export const useLocationAutocomplete = () => {
  const [suggestions, setSuggestions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const getSuggestions = async (query) => {
    if (!query || query.trim().length < 2) {
      setSuggestions([]);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await fetch(
        `https://nominatim.openstreetmap.org/search?` +
        `format=json` +
        `&q=${encodeURIComponent(query.trim())}` +
        `&countrycodes=za` +
        `&limit=8` +
        `&addressdetails=1` +
        `&dedupe=1` +
        `&extratags=1`,
        {
          headers: {
            'User-Agent': 'samfms/1.0' 
          }
        }
      );

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      // Transform to match what LocationAutocomplete.jsx expects
      const transformedSuggestions = data.map(item => ({
        ...item,
        display_name: item.display_name,
        lat: item.lat,
        lon: item.lon,
        place_id: item.place_id
      }));
      
      setSuggestions(transformedSuggestions);
      console.log('Transformed suggestions:', transformedSuggestions);
    } catch (err) {
      setError('Failed to fetch location suggestions');
      console.error('Error fetching locations:', err);
      setSuggestions([]);
    } finally {
      setLoading(false);
    }
  };

  const clearSuggestions = () => {
    setSuggestions([]);
  };

  const clearError = () => {
    setError(null);
  };

  return {
    suggestions,
    loading,
    error,
    getSuggestions,
    clearSuggestions,
    clearError
  };
};