import { useState, useEffect } from 'react';

export const useLocationAutocomplete = () => {
  const [suggestions, setSuggestions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const getSuggestions = async (query) => {
    if (!query || query.length < 3) {
      setSuggestions([]);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await fetch(
        `https://nominatim.openstreetmap.org/search?format=json&addressdetails=1&limit=5&countrycodes=za&q=${encodeURIComponent(query)}`,
        {
          headers: {
            'User-Agent': 'YourAppName/1.0' // Replace with your app name
          }
        }
      );

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      
      // Nominatim already returns data in the format your component expects
      setSuggestions(data);
    } catch (err) {
      setError('Failed to fetch location suggestions');
      console.error('Error fetching locations:', err);
      setSuggestions([]);
    } finally {
      setLoading(false);
    }
  };

  return {
    suggestions,
    loading,
    error,
    getSuggestions
  };
};