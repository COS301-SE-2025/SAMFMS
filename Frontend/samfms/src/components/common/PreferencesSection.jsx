import React, {useState, useEffect} from 'react';
import PreferenceCard from './PreferenceCard';
import ToggleSwitch from './ToggleSwitch';
import {Button} from '../ui/button';
import {updatePreferences, getCurrentUser} from '../../backend/api/auth';
import {useTheme} from '../../contexts/ThemeContext';
import {useNotification} from '../../contexts/NotificationContext';

// Icon components
const ThemeIcon = () => (
  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path
      strokeLinecap="round"
      strokeLinejoin="round"
      strokeWidth={2}
      d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z"
    />
  </svg>
);

const SecurityIcon = () => (
  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path
      strokeLinecap="round"
      strokeLinejoin="round"
      strokeWidth={2}
      d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"
    />
  </svg>
);

// Theme Icons for buttons
const LightThemeIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <circle cx="12" cy="12" r="5" stroke="currentColor" strokeWidth="2" />
    <path d="M12 1v2m0 18v2M4.22 4.22l1.42 1.42m12.72 12.72l1.42 1.42M1 12h2m18 0h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
  </svg>
);

const DarkThemeIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
  </svg>
);

const AutoThemeIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <rect x="2" y="3" width="20" height="14" rx="2" ry="2" stroke="currentColor" strokeWidth="2" />
    <line x1="8" y1="21" x2="16" y2="21" stroke="currentColor" strokeWidth="2" />
    <line x1="12" y1="17" x2="12" y2="21" stroke="currentColor" strokeWidth="2" />
  </svg>
);

const PreferencesSection = () => {
  const {setTheme} = useTheme();
  const {showSuccess, showError} = useNotification();
  const [preferences, setPreferences] = useState({
    theme: 'light',
    animations: 'true',
    two_factor: 'false',
    activity_log: 'true',
    session_timeout: 30, // in minutes
  });

  const [loading, setLoading] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);
  const [originalPreferences, setOriginalPreferences] = useState({}); // Load preferences from current user
  useEffect(() => {
    const currentUser = getCurrentUser();
    if (currentUser && currentUser.preferences) {
      const userPrefs = {
        ...currentUser.preferences,
        session_timeout: convertTimeoutToMinutes(currentUser.preferences.session_timeout)
      };
      setPreferences(userPrefs);
      setOriginalPreferences(userPrefs);

      // Sync theme with context on mount
      if (userPrefs.theme) {
        setTheme(userPrefs.theme);
      }
    }
  }, [setTheme]); // Include setTheme in dependencies

  // Track changes
  useEffect(() => {
    const changed = JSON.stringify(preferences) !== JSON.stringify(originalPreferences);
    setHasChanges(changed);
  }, [preferences, originalPreferences]);
  const handlePreferenceChange = (key, value) => {
    setPreferences(prev => ({
      ...prev,
      [key]: value,
    }));

    // Immediately apply theme changes
    if (key === 'theme') {
      console.log('Theme changing to:', value); // Debug log
      setTheme(value);
    }
  };
  const handleSavePreferences = async () => {
    try {
      setLoading(true);

      console.log('Saving preferences:', preferences); // Debug log
      await updatePreferences(preferences);

      setOriginalPreferences(preferences);
      setHasChanges(false);

      // Force theme update after successful save
      if (preferences.theme) {
        console.log('Forcing theme update to:', preferences.theme); // Debug log
        setTheme(preferences.theme);
      }

      showSuccess('Preferences updated successfully');
    } catch (err) {
      console.error('Error updating preferences:', err);
      showError(err.message || 'Failed to update preferences');
    } finally {
      setLoading(false);
    }
  };

  const handleResetPreferences = () => {
    setPreferences(originalPreferences);
  };

  // Helper function to convert string boolean to actual boolean
  const toBool = value => value === 'true' || value === true;

  // Helper function to format timeout display
  const formatTimeout = (minutes) => {
    if (minutes < 60) return `${minutes}min`;
    const hours = Math.floor(minutes / 60);
    const remainingMinutes = minutes % 60;
    if (remainingMinutes === 0) return `${hours}hr`;
    return `${hours}hr ${remainingMinutes}min`;
  };

  // Helper function to convert string timeout to minutes
  const convertTimeoutToMinutes = (timeoutString) => {
    if (typeof timeoutString === 'number') return timeoutString;
    if (!timeoutString || typeof timeoutString !== 'string') return 30;

    if (timeoutString.includes('hour')) {
      const hours = parseInt(timeoutString);
      return hours * 60;
    } else if (timeoutString.includes('minute')) {
      return parseInt(timeoutString);
    }
    return 30; // default
  };
  return (
    <>
      <style jsx>{`
        .timeout-slider {
          -webkit-appearance: none;
          height: 8px;
          border-radius: 4px;
          background: hsl(var(--border));
          outline: none;
          transition: background 0.2s;
        }
        .timeout-slider:hover {
          background: hsl(var(--border));
        }
        .timeout-slider::-webkit-slider-thumb {
          -webkit-appearance: none;
          appearance: none;
          width: 20px;
          height: 20px;
          border-radius: 50%;
          background: hsl(var(--primary));
          cursor: pointer;
          border: 2px solid hsl(var(--background));
          box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }
        .timeout-slider::-webkit-slider-thumb:hover {
          background: hsl(var(--primary));
          transform: scale(1.1);
        }
        .timeout-slider::-moz-range-thumb {
          width: 20px;
          height: 20px;
          border-radius: 50%;
          background: hsl(var(--primary));
          cursor: pointer;
          border: 2px solid hsl(var(--background));
          box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }
      `}</style>
      <div className="space-y-6">
        {/* Second row: Theme & Appearance and Privacy & Security in 2 columns */}
        <div className="grid grid-cols-1 gap-6">
          {/* Theme & Appearance */}
          <div className="max-w-md mx-auto w-full">
            <PreferenceCard title="Theme & Appearance" icon={<ThemeIcon />}>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-2 text-foreground">Theme</label>
                  <div className="grid grid-cols-3 gap-2">
                    <button
                      onClick={() => handlePreferenceChange('theme', 'dark')}
                      className={`flex items-center justify-center gap-2 px-4 py-9 rounded-md border transition-colors ${preferences.theme === 'dark'
                        ? 'bg-primary text-primary-foreground border-primary'
                        : 'bg-background text-foreground border-border hover:bg-muted'
                        }`}
                    >
                      <DarkThemeIcon />
                      Dark
                    </button>
                    <button
                      onClick={() => handlePreferenceChange('theme', 'auto')}
                      className={`flex items-center justify-center gap-2 px-4 py-9 rounded-md border transition-colors ${preferences.theme === 'auto'
                        ? 'bg-primary text-primary-foreground border-primary'
                        : 'bg-background text-foreground border-border hover:bg-muted'
                        }`}
                    >
                      <AutoThemeIcon />
                      Auto
                    </button>
                    <button
                      onClick={() => handlePreferenceChange('theme', 'light')}
                      className={`flex items-center justify-center gap-2 px-4 py-9 rounded-md border transition-colors ${preferences.theme === 'light'
                        ? 'bg-primary text-primary-foreground border-primary'
                        : 'bg-background text-foreground border-border hover:bg-muted'
                        }`}
                    >
                      <LightThemeIcon />
                      Light
                    </button>
                  </div>
                </div>{' '}
              </div>
            </PreferenceCard>
          </div>
        </div>

        {/* Save Actions */}
        {hasChanges && (
          <div className="flex items-center justify-between p-4 bg-muted/50 rounded-lg border border-border">
            <div>
              <p className="text-sm font-medium text-foreground">You have unsaved changes</p>
              <p className="text-xs text-muted-foreground">
                Save your preferences to apply the changes
              </p>
            </div>

            <div className="flex space-x-3">
              <Button variant="outline" onClick={handleResetPreferences} disabled={loading}>
                Reset
              </Button>
              <Button onClick={handleSavePreferences} disabled={loading}>
                {loading ? 'Saving...' : 'Save Changes'}
              </Button>
            </div>
          </div>
        )}
      </div>
    </>
  );
};

export default PreferencesSection;
