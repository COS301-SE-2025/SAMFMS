import React, { createContext, useState, useEffect, useContext } from 'react';

// Create the theme context
export const ThemeContext = createContext({
  theme: 'light',
  setTheme: () => {},
  toggleTheme: () => {},
});

// Theme provider component
export const ThemeProvider = ({ children }) => {
  // Initialize theme from localStorage or default to light
  const [theme, setTheme] = useState(() => {
    if (typeof window !== 'undefined') {
      // Check localStorage first, then default to light
      const savedTheme = localStorage.getItem('theme');
      return savedTheme || 'light';
    }
    return 'light';
  });

  // Toggle between light and dark themes
  const toggleTheme = () => {
    setTheme(theme === 'light' ? 'dark' : 'light');
  }; // Apply theme to document and save to localStorage
  useEffect(() => {
    const root = window.document.documentElement;
    root.classList.remove('light', 'dark');

    let appliedTheme = theme;

    // Handle auto theme
    if (theme === 'auto') {
      const systemPrefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      appliedTheme = systemPrefersDark ? 'dark' : 'light';

      // Listen for system theme changes
      const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
      const handleChange = e => {
        const newTheme = e.matches ? 'dark' : 'light';
        root.classList.remove('light', 'dark');
        root.classList.add(newTheme);
      };

      mediaQuery.addEventListener('change', handleChange);

      // Cleanup listener
      return () => mediaQuery.removeEventListener('change', handleChange);
    }

    // Apply the theme class
    root.classList.add(appliedTheme);

    // Save to localStorage
    localStorage.setItem('theme', theme);
  }, [theme]);

  return (
    <ThemeContext.Provider value={{ theme, setTheme, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  );
};

// Custom hook for using the theme context
export const useTheme = () => useContext(ThemeContext);

export default ThemeProvider;
