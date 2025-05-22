import React from 'react';
import { Button } from '../components/ui/button';

const Settings = () => {
  return (
    <div className="container mx-auto py-8">
      <header className="mb-8">
        <h1 className="text-4xl font-bold">Settings</h1>
        <p className="text-muted-foreground">Configure system preferences and options</p>
      </header>

      <div className="grid grid-cols-1 gap-8">
        <SettingsSection
          title="Appearance"
          description="Customize how SAMFMS looks and feels"
          options={[
            {
              id: 'theme',
              label: 'Theme',
              value: 'Light',
              type: 'select',
              choices: ['Light', 'Dark', 'System'],
            },
            {
              id: 'density',
              label: 'Density',
              value: 'Comfortable',
              type: 'select',
              choices: ['Comfortable', 'Compact'],
            },
            { id: 'animations', label: 'Animations', value: true, type: 'toggle' },
          ]}
        />

        <SettingsSection
          title="Notifications"
          description="Manage your notification preferences"
          options={[
            { id: 'email-alerts', label: 'Email Alerts', value: true, type: 'toggle' },
            { id: 'push-notifications', label: 'Push Notifications', value: true, type: 'toggle' },
            { id: 'sms', label: 'SMS Notifications', value: false, type: 'toggle' },
            {
              id: 'notification-sound',
              label: 'Notification Sound',
              value: 'Standard',
              type: 'select',
              choices: ['None', 'Standard', 'Alert'],
            },
          ]}
        />

        <SettingsSection
          title="Regional"
          description="Configure regional settings"
          options={[
            {
              id: 'language',
              label: 'Language',
              value: 'English',
              type: 'select',
              choices: ['English', 'Spanish', 'French', 'German'],
            },
            {
              id: 'timezone',
              label: 'Timezone',
              value: 'UTC-5 (Eastern Time)',
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
              value: 'MM/DD/YYYY',
              type: 'select',
              choices: ['MM/DD/YYYY', 'DD/MM/YYYY', 'YYYY-MM-DD'],
            },
            {
              id: 'distance-unit',
              label: 'Distance Unit',
              value: 'Miles',
              type: 'select',
              choices: ['Kilometers', 'Miles'],
            },
            {
              id: 'fuel-unit',
              label: 'Fuel Unit',
              value: 'Gallons',
              type: 'select',
              choices: ['Liters', 'Gallons'],
            },
          ]}
        />

        <SettingsSection
          title="Privacy & Security"
          description="Manage your privacy and security settings"
          options={[
            { id: 'two-factor', label: 'Two-factor Authentication', value: false, type: 'toggle' },
            { id: 'data-sharing', label: 'Data Sharing', value: true, type: 'toggle' },
            { id: 'activity-log', label: 'Activity Logging', value: true, type: 'toggle' },
            {
              id: 'session-timeout',
              label: 'Session Timeout',
              value: '30 minutes',
              type: 'select',
              choices: ['15 minutes', '30 minutes', '1 hour', '4 hours'],
            },
          ]}
        />
      </div>

      <div className="flex justify-end mt-8">
        <Button variant="outline" className="mr-4">
          Reset to Defaults
        </Button>
        <Button>Save Settings</Button>
      </div>
    </div>
  );
};

// A section component for grouping related settings
const SettingsSection = ({ title, description, options }) => {
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
                    defaultChecked={option.value}
                    className="sr-only peer"
                  />
                  <span
                    className={`absolute left-1 top-1 w-4 h-4 rounded-full transition-all duration-200 ${
                      option.value ? 'bg-primary translate-x-6' : 'bg-foreground'
                    }`}
                  ></span>
                </div>
              ) : option.type === 'select' ? (
                <select
                  id={option.id}
                  defaultValue={option.value}
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
