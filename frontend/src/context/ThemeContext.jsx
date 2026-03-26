import React, { createContext, useContext, useState, useEffect } from 'react';

const ThemeContext = createContext(undefined);

const STORAGE_KEY = 'lumina-pay-settings';

function getInitialTheme() {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      const parsed = JSON.parse(stored);
      if (parsed.theme === 'light' || parsed.theme === 'dark') {
        return parsed.theme;
      }
    }
  } catch (_e) { /* ignore */ }
  return 'dark';
}

export function ThemeProvider({ children }) {
  const [theme, setThemeState] = useState(getInitialTheme);

  // Apply data-theme attribute on <html>
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
  }, [theme]);

  const setTheme = (newTheme) => {
    setThemeState(newTheme);
    // Also persist into the settings blob in localStorage
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      const settings = stored ? JSON.parse(stored) : {};
      settings.theme = newTheme;
      localStorage.setItem(STORAGE_KEY, JSON.stringify(settings));
    } catch (_e) { /* ignore */ }
  };

  return (
    <ThemeContext.Provider value={{ theme, setTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const ctx = useContext(ThemeContext);
  if (!ctx) throw new Error('useTheme must be used within ThemeProvider');
  return ctx;
}
