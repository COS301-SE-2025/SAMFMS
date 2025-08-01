import React from 'react';

const ToggleSwitch = ({ enabled, onChange, label, description, disabled = false, id }) => {
  return (
    <div className="flex items-center justify-between py-2">
      <div className="flex-1">
        {label && (
          <label
            htmlFor={id}
            className={`block text-sm font-medium ${
              disabled ? 'text-muted-foreground' : 'text-foreground'
            }`}
          >
            {label}
          </label>
        )}
        {description && <p className="text-xs text-muted-foreground mt-1">{description}</p>}
      </div>

      <button
        id={id}
        type="button"
        disabled={disabled}
        onClick={() => onChange(!enabled)}
        className={`
          relative inline-flex h-6 w-11 items-center rounded-full transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2
          ${enabled ? 'bg-primary' : 'bg-muted'}
          ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
        `}
        role="switch"
        aria-checked={enabled}
      >
        <span
          className={`
            inline-block h-4 w-4 transform rounded-full bg-white transition duration-200 ease-in-out
            ${enabled ? 'translate-x-6' : 'translate-x-1'}
          `}
        />
      </button>
    </div>
  );
};

export default ToggleSwitch;
