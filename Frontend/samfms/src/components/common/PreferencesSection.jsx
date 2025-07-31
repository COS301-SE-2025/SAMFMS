import React, { useState, useEffect } from 'react';
import PreferenceCard from './PreferenceCard';
import ToggleSwitch from './ToggleSwitch';
import { Button } from '../ui/button';
import { updatePreferences, getCurrentUser } from '../../backend/api/auth';
import { useTheme } from '../../contexts/ThemeContext';
import { useNotification } from '../../contexts/NotificationContext';

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

const NotificationIcon = () => (
  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path
      strokeLinecap="round"
      strokeLinejoin="round"
      strokeWidth={2}
      d="M15 17h5l-5 5v-5zM4.868 19.304A7.5 7.5 0 0019.304 4.868l-.304-.304m-2.121 2.121A4.5 4.5 0 004.197 19.683l13.49-13.49z"
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

const PreferencesSection = () => {
  const { setTheme } = useTheme();
  const { showSuccess, showError } = useNotification();
  const [preferences, setPreferences] = useState({
    theme: 'light',
    animations: 'true',
    email_alerts: 'true',
    push_notifications: 'true',
    two_factor: 'false',
    activity_log: 'true',
    session_timeout: '30 minutes',
  });

  const [loading, setLoading] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);
  const [originalPreferences, setOriginalPreferences] = useState({}); // Load preferences from current user
  useEffect(() => {
    const currentUser = getCurrentUser();
    if (currentUser && currentUser.preferences) {
      const userPrefs = currentUser.preferences;
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
  return (
    <div className="space-y-6">
      {/* Theme & Appearance */}
      <PreferenceCard title="Theme & Appearance" icon={<ThemeIcon />}>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-2 text-foreground">Theme</label>
            <select
              value={preferences.theme}
              onChange={e => handlePreferenceChange('theme', e.target.value)}
              className="w-full p-2 border border-border rounded-md bg-background text-foreground focus:ring-primary focus:border-primary"
            >
              <option value="light">Light</option>
              <option value="dark">Dark</option>
              <option value="auto">Auto (System)</option>
            </select>
          </div>{' '}
          <ToggleSwitch
            id="animations"
            enabled={toBool(preferences.animations)}
            onChange={enabled => handlePreferenceChange('animations', enabled.toString())}
            label="Enable Animations"
          />
        </div>
      </PreferenceCard>{' '}
      {/* Notifications */}
      <PreferenceCard title="Notifications" icon={<NotificationIcon />}>
        <div className="space-y-4">
          {' '}
          <ToggleSwitch
            id="email_alerts"
            enabled={toBool(preferences.email_alerts)}
            onChange={enabled => handlePreferenceChange('email_alerts', enabled.toString())}
            label="Email Alerts"
          />{' '}
          <ToggleSwitch
            id="push_notifications"
            enabled={toBool(preferences.push_notifications)}
            onChange={enabled => handlePreferenceChange('push_notifications', enabled.toString())}
            label="Push Notifications"
          />
        </div>
      </PreferenceCard>{' '}
      {/* Security */}
      <PreferenceCard title="Security & Privacy" icon={<SecurityIcon />}>
        <div className="space-y-4">
          {' '}
          <ToggleSwitch
            id="two_factor"
            enabled={toBool(preferences.two_factor)}
            onChange={enabled => handlePreferenceChange('two_factor', enabled.toString())}
            label="Two-Factor Authentication"
          />{' '}
          <ToggleSwitch
            id="activity_log"
            enabled={toBool(preferences.activity_log)}
            onChange={enabled => handlePreferenceChange('activity_log', enabled.toString())}
            label="Activity Logging"
          />
          <div>
            <label className="block text-sm font-medium mb-2 text-foreground">
              Session Timeout
            </label>
            <select
              value={preferences.session_timeout}
              onChange={e => handlePreferenceChange('session_timeout', e.target.value)}
              className="w-full p-2 border border-border rounded-md bg-background text-foreground focus:ring-primary focus:border-primary"
            >
              <option value="15 minutes">15 minutes</option>
              <option value="30 minutes">30 minutes</option>
              <option value="1 hour">1 hour</option>
              <option value="2 hours">2 hours</option>
              <option value="4 hours">4 hours</option>
              <option value="8 hours">8 hours</option>
            </select>
          </div>
        </div>
      </PreferenceCard>
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
  );
};

export default PreferencesSection;
