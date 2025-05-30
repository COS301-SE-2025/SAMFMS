import React, { useState, useRef, useEffect } from 'react';
import { ChevronDown } from 'lucide-react';

const CustomDropdown = ({
  value,
  onChange,
  options,
  placeholder = 'Select option',
  className = '',
  disabled = false,
  maxVisibleOptions = 5,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef(null);

  useEffect(() => {
    const handleClickOutside = event => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  const handleSelect = optionValue => {
    onChange(optionValue);
    setIsOpen(false);
  };

  const getDisplayValue = () => {
    if (!value) return placeholder;
    const option = options.find(opt => opt.value === value);
    return option ? option.label : value;
  };

  // Calculate the height based on number of visible options
  const optionHeight = 40; // Approximate height of each option in pixels
  const maxHeight = Math.min(options.length, maxVisibleOptions) * optionHeight;

  return (
    <div className={`relative ${className}`} ref={dropdownRef}>
      <div
        className={`w-full px-3 py-2 border border-input rounded-md bg-background cursor-pointer flex items-center justify-between ${
          disabled ? 'opacity-50 cursor-not-allowed' : ''
        }`}
        onClick={() => !disabled && setIsOpen(!isOpen)}
      >
        <span className={value ? 'text-foreground' : 'text-muted-foreground'}>
          {getDisplayValue()}
        </span>
        <ChevronDown
          size={16}
          className={`transform transition-transform ${isOpen ? 'rotate-180' : ''}`}
        />
      </div>

      {isOpen && !disabled && (
        <div
          className="absolute z-50 w-full mt-1 bg-background border border-input rounded-md shadow-lg overflow-y-auto"
          style={{ maxHeight: `${maxHeight}px` }}
        >
          {options.map(option => (
            <div
              key={option.value}
              className="px-3 py-2 hover:bg-accent cursor-pointer flex items-center"
              onClick={() => handleSelect(option.value)}
              style={{ minHeight: `${optionHeight}px` }}
            >
              <span className="flex-1">{option.label}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default CustomDropdown;
