// Theme utility functions for immediate theme application
import { getCookie } from '../lib/cookies';

/**
 * Apply user theme preference immediately after login
 * This function should be called after successful login to ensure
 * the theme is applied before any UI renders
 */
export const applyUserThemePreference = () => {
  try {
    const preferencesStr = getCookie('preferences');
    if (preferencesStr) {
      const preferences = JSON.parse(preferencesStr);
      if (preferences.theme) {
        // Apply theme immediately to the document
        const root = window.document.documentElement;
        root.classList.remove('light', 'dark');

        let appliedTheme = preferences.theme;

        // Handle auto theme
        if (preferences.theme === 'auto') {
          const systemPrefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
          appliedTheme = systemPrefersDark ? 'dark' : 'light';
        }

        root.classList.add(appliedTheme);

        // Also update localStorage for consistency
        localStorage.setItem('theme', preferences.theme);

        console.log('Applied user theme preference:', appliedTheme);
        return appliedTheme;
      }
    }
  } catch (error) {
    console.error('Error applying user theme preference:', error);
  }

  return null;
};

/**
 * Get the current effective theme (resolving 'auto' to actual theme)
 */
export const getEffectiveTheme = theme => {
  if (theme === 'auto') {
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  }
  return theme;
};
