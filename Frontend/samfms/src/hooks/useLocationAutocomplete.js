import { useState, useEffect } from 'react';

export const useLocationAutocomplete = () => {
  const [suggestions, setSuggestions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const getSuggestions = async (query) => {
    if (!query) {
      setSuggestions([]);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await fetch(
        `https://api.mapbox.com/geocoding/v5/mapbox.places/${encodeURIComponent(query)}.json?access_token=${process.env.REACT_APP_MAPBOX_TOKEN}&country=za`
      );
      const data = await response.json();
      setSuggestions(data.features || []);
    } catch (err) {
      setError('Failed to fetch location suggestions');
      console.error('Error fetching locations:', err);
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