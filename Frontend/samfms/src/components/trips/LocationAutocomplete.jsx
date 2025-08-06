import React, {useState, useEffect, useRef} from 'react';
import {useLocationAutocomplete} from '../../hooks/useLocationAutocomplete';

const LocationAutocomplete = ({value, onChange, placeholder, className, required}) => {
  const [inputValue, setInputValue] = useState(value || '');
  const [showSuggestions, setShowSuggestions] = useState(false);
  const {suggestions, loading: isLoading, getSuggestions} = useLocationAutocomplete();
  const debounceRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    setInputValue(value || '');
  }, [value]);

  const handleInputChange = (e) => {
    const newValue = e.target.value;
    setInputValue(newValue);

    if (debounceRef.current) {
      clearTimeout(debounceRef.current);
    }

    debounceRef.current = setTimeout(() => {
      getSuggestions(newValue);
      setShowSuggestions(true);
    }, 300);
  };

  const handleSuggestionClick = (suggestion) => {
    const address = suggestion.display_name;
    setInputValue(address);
    setShowSuggestions(false);
    onChange(address, {
      lat: parseFloat(suggestion.lat),
      lng: parseFloat(suggestion.lon),
      formatted_address: address,
      place_id: suggestion.place_id
    });
  };

  const handleBlur = () => {
    setTimeout(() => setShowSuggestions(false), 200);
  };

  const handleFocus = () => {
    if (suggestions.length > 0) {
      setShowSuggestions(true);
    }
  };

  return (
    <div className="relative">
      <input
        ref={inputRef}
        type="text"
        value={inputValue}
        onChange={handleInputChange}
        onBlur={handleBlur}
        onFocus={handleFocus}
        placeholder={placeholder}
        className={className}
        required={required}
      />

      {showSuggestions && (suggestions.length > 0 || isLoading) && (
        <div className="absolute z-10 w-full bg-white border border-gray-300 rounded-md shadow-lg mt-1 max-h-60 overflow-y-auto">
          {isLoading ? (
            <div className="p-3 text-center text-gray-500">
              <div className="inline-block animate-spin rounded-full h-4 w-4 border-b-2 border-gray-900"></div>
              <span className="ml-2">Searching...</span>
            </div>
          ) : (
            suggestions.map((suggestion, index) => (
              <div
                key={suggestion.place_id || index}
                className="p-3 hover:bg-gray-100 cursor-pointer border-b border-gray-100 last:border-b-0"
                onClick={() => handleSuggestionClick(suggestion)}
              >
                <div className="font-medium text-sm">{suggestion.display_name}</div>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
};

export default LocationAutocomplete;