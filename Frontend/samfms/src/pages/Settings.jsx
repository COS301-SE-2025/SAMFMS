import React, { useState, useEffect } from 'react';
import { Button } from '../components/ui/button';
import ThemeToggle from '../components/ThemeToggle';
import { getCurrentUser, updatePreferences } from '../backend/api/auth';
import { getCookie } from '../lib/cookies';

const Settings = () => {
  const [settings, setSettings] = useState({
    theme: 'light',
    animations: 'true',
    'email-alerts': 'true',
    'push-notifications': 'true',
    timezone: 'UTC-5 (Eastern Time)',
    'date-format': 'MM/DD/YYYY',
    'two-factor': 'false',
    'activity-log': 'true',
    'session-timeout': '30 minutes',
  });
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  // Load user preferences on component mount
  useEffect(() => {
    // Get preferences from cookie
    const preferencesCookie = getCookie('preferences');
    if (preferencesCookie) {
      try {
        const preferences = JSON.parse(preferencesCookie);
        console.log('Loaded preferences from cookie:', preferences);

        // Convert snake_case keys from backend/cookies to kebab-case for frontend display
        const formattedPreferences = {};
        Object.keys(preferences).forEach(key => {
          const kebabKey = key.replace(/_/g, '-');
          formattedPreferences[kebabKey] = preferences[key];
        });

        setSettings(prevSettings => ({
          ...prevSettings,
          ...formattedPreferences,
        }));
      } catch (error) {
        console.error('Error parsing preferences cookie:', error);
      }
    }
  }, []);

  const handleSettingChange = (key, value) => {
    setSettings(prev => ({
      ...prev,
      [key]: value,
    }));
  };
  const handleSaveSettings = async () => {
    setLoading(true);
    setMessage('');

    try {
      const user = getCurrentUser();
      if (!user) {
        throw new Error('User not authenticated');
      }

      // Convert settings object for backend format
      // Note: The backend expects snake_case keys while frontend uses kebab-case
      const preferencesData = {};
      Object.keys(settings).forEach(key => {
        // Replace all dashes with underscores for complete conversion from kebab-case to snake_case
        preferencesData[key.replace(/-/g, '_')] = settings[key];
      }); // Use the updatePreferences function from auth.js
      await updatePreferences(preferencesData);
      setMessage('Settings saved successfully!');

      // The updatePreferences function updates the cookies
      // We should update our local state to reflect the saved preferences
      // This ensures any changes in key format (kebab-case vs snake_case) are properly handled
      const preferencesCookie = getCookie('preferences');
      if (preferencesCookie) {
        try {
          const updatedPreferences = JSON.parse(preferencesCookie);
          console.log('Updated preferences from cookie:', updatedPreferences);

          // Convert snake_case keys back to kebab-case for frontend display
          const formattedPreferences = {};
          Object.keys(updatedPreferences).forEach(key => {
            const kebabKey = key.replace(/_/g, '-');
            formattedPreferences[kebabKey] = updatedPreferences[key];
          });

          setSettings(prevSettings => ({
            ...prevSettings,
            ...formattedPreferences,
          }));
        } catch (error) {
          console.error('Error parsing updated preferences cookie:', error);
        }
      }
    } catch (error) {
      setMessage('Error saving settings: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleResetDefaults = () => {
    setSettings({
      theme: 'light',
      animations: 'true',
      'email-alerts': 'true',
      'push-notifications': 'true',
      timezone: 'UTC-5 (Eastern Time)',
      'date-format': 'MM/DD/YYYY',
      'two-factor': 'false',
      'activity-log': 'true',
      'session-timeout': '30 minutes',
    });
    setMessage('Settings reset to defaults');
  };
  return (
    <div className="container mx-auto py-8">
      <header className="mb-8">
        <h1 className="text-4xl font-bold">Settings</h1>
        <p className="text-muted-foreground">Configure system preferences and options</p>
      </header>
      <div className="grid grid-cols-1 gap-8">
        {' '}
        <div className="bg-card rounded-lg shadow-md p-6 border border-border">
          <h2 className="text-xl font-semibold mb-2">Appearance</h2>
          <p className="text-muted-foreground mb-6">Customize how SAMFMS looks and feels</p>{' '}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <label htmlFor="theme" className="block text-sm font-medium">
                  Theme
                </label>
                <p className="text-sm text-muted-foreground">Switch between light and dark mode</p>
              </div>
              <ThemeToggle />
            </div>{' '}
            <div className="flex items-center justify-between">
              <div>
                <label htmlFor="animations" className="block text-sm font-medium">
                  Animations
                </label>
                <p className="text-sm text-muted-foreground">Enable or disable UI animations</p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  className="sr-only peer"
                  checked={settings.animations === 'true'}
                  onChange={e =>
                    handleSettingChange('animations', e.target.checked ? 'true' : 'false')
                  }
                />
                <div className="w-11 h-6 bg-muted rounded-full peer peer-checked:bg-primary"></div>
              </label>
            </div>
          </div>
        </div>{' '}
        <SettingsSection
          title="Notifications"
          description="Manage your notification preferences"
          settings={settings}
          handleSettingChange={handleSettingChange}
          options={[
            { id: 'email-alerts', label: 'Email Alerts', type: 'toggle' },
            { id: 'push-notifications', label: 'Push Notifications', type: 'toggle' },
          ]}
        />{' '}
        <SettingsSection
          title="Regional"
          description="Configure regional settings"
          settings={settings}
          handleSettingChange={handleSettingChange}
          options={[
            {
              id: 'timezone',
              label: 'Timezone',
              type: 'select',
              choices: [
                'UTC-5 (Eastern Time)',
                'UTC-6 (Central Time)',
                'UTC-7 (Mountain Time)',
                'UTC-8 (Pacific Time)',
              ],
            },
            {
              id: 'date-format',
              label: 'Date Format',
              type: 'select',
              choices: ['MM/DD/YYYY', 'DD/MM/YYYY', 'YYYY-MM-DD'],
            },
          ]}
        />{' '}
        <SettingsSection
          title="Privacy & Security"
          description="Manage your privacy and security settings"
          settings={settings}
          handleSettingChange={handleSettingChange}
          options={[
            { id: 'two-factor', label: 'Two-factor Authentication', type: 'toggle' },
            { id: 'activity-log', label: 'Activity Logging', type: 'toggle' },
            {
              id: 'session-timeout',
              label: 'Session Timeout',
              type: 'select',
              choices: ['15 minutes', '30 minutes', '1 hour', '4 hours'],
            },
          ]}
        />
      </div>{' '}
      {message && (
        <div
          className={`mb-4 p-3 rounded-md ${
            message.includes('Error') ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700'
          }`}
        >
          {message}
        </div>
      )}
      <div className="flex justify-end mt-8">
        <Button variant="outline" className="mr-4" onClick={handleResetDefaults}>
          Reset to Defaults
        </Button>
        <Button onClick={handleSaveSettings} disabled={loading}>
          {loading ? 'Saving...' : 'Save Settings'}
        </Button>
      </div>
    </div>
  );
};

// A section component for grouping related settings

const SettingsSection = ({ title, description, options, settings, handleSettingChange }) => {
  return (
    <div className="bg-card rounded-lg shadow-md p-6 border border-border">
      <h2 className="text-xl font-semibold mb-2">{title}</h2>
      <p className="text-muted-foreground mb-6">{description}</p>

      <div className="space-y-4">
        {options.map(option => (
          <div
            key={option.id}
            className="flex items-center justify-between py-2 border-b border-border last:border-0"
          >
            <div>
              <label htmlFor={option.id} className="font-medium">
                {option.label}
              </label>
            </div>
            <div>
              {option.type === 'toggle' ? (
                <div className="relative inline-block w-12 h-6 rounded-full bg-secondary">
                  <input
                    type="checkbox"
                    id={option.id}
                    checked={settings[option.id] === 'true'}
                    onChange={e =>
                      handleSettingChange(option.id, e.target.checked ? 'true' : 'false')
                    }
                    className="sr-only peer"
                  />
                  <span
                    className={`absolute left-1 top-1 w-4 h-4 rounded-full transition-all duration-200 ${
                      settings[option.id] === 'true' ? 'bg-primary translate-x-6' : 'bg-foreground'
                    }`}
                  ></span>
                </div>
              ) : option.type === 'select' ? (
                <select
                  id={option.id}
                  value={settings[option.id] || option.choices[0]}
                  onChange={e => handleSettingChange(option.id, e.target.value)}
                  className="p-1 border rounded-md"
                >
                  {option.choices.map(choice => (
                    <option key={choice} value={choice}>
                      {choice}
                    </option>
                  ))}
                </select>
              ) : null}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default Settings;
