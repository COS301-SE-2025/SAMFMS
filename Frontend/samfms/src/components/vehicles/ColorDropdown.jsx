import React, { useState, useRef, useEffect } from 'react';
import { ChevronDown } from 'lucide-react';

const ColorDropdown = ({
  value,
  onChange,
  colors,
  colorMap,
  placeholder = 'Select Color',
  className = '',
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

  const handleSelect = color => {
    onChange(color);
    setIsOpen(false);
  };

  const getDisplayValue = () => {
    if (!value) return placeholder;
    return value === 'Specify' ? 'Specify' : value;
  };

  const renderColorOption = color => (
    <div
      key={color}
      className="flex items-center px-3 py-2 hover:bg-accent cursor-pointer"
      onClick={() => handleSelect(color)}
    >
      {color !== 'Specify' && colorMap[color] && (
        <div
          className="w-4 h-4 rounded-full mr-3 flex-shrink-0"
          style={{
            backgroundColor: colorMap[color],
            border: color === 'White' ? '1px solid #ccc' : 'none',
          }}
        />
      )}
      <span className="flex-1">{color}</span>
    </div>
  );

  return (
    <div className={`relative ${className}`} ref={dropdownRef}>
      <div
        className="w-full px-3 py-2 border border-input rounded-md bg-background cursor-pointer flex items-center justify-between"
        onClick={() => setIsOpen(!isOpen)}
      >
        <div className="flex items-center">
          {value && value !== 'Specify' && colorMap[value] && (
            <div
              className="w-4 h-4 rounded-full mr-3 flex-shrink-0"
              style={{
                backgroundColor: colorMap[value],
                border: value === 'White' ? '1px solid #ccc' : 'none',
              }}
            />
          )}
          <span className={value ? 'text-foreground' : 'text-muted-foreground'}>
            {getDisplayValue()}
          </span>
        </div>
        <ChevronDown
          size={16}
          className={`transform transition-transform ${isOpen ? 'rotate-180' : ''}`}
        />
      </div>

      {isOpen && (
        <div className="absolute z-50 w-full mt-1 bg-background border border-input rounded-md shadow-lg max-h-40 overflow-y-auto">
          <div
            className="px-3 py-2 hover:bg-accent cursor-pointer text-muted-foreground"
            onClick={() => handleSelect('')}
          >
            {placeholder}
          </div>
          {/* Specify option at top */}
          {renderColorOption('Specify')}
          {/* Other color options */}
          {colors.filter(color => color !== 'Specify').map(color => renderColorOption(color))}
        </div>
      )}
    </div>
  );
};

export default ColorDropdown;
