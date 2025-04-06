import React, {
  createContext,
  useContext,
  useState,
  useEffect,
  useMemo,
  useCallback,
} from 'react';
import {
  lightTheme,
  darkTheme,
  Theme,
  ThemePreference,
  ThemeContextType,
} from '@uniskit/shared';

function applyThemeVariables(theme: Theme) {
  const root = document.documentElement;
  if (!root) return;

  Object.entries(theme.colors.brand).forEach(([key, value]) => {
    root.style.setProperty(`--color-brand-${key}`, value);
  });
  Object.entries(theme.colors.layout).forEach(([key, value]) => {
    root.style.setProperty(`--color-layout-${key}`, value);
  });
  Object.entries(theme.colors.indicators).forEach(([key, value]) => {
    root.style.setProperty(`--color-indicators-${key}`, value);
  });
  Object.entries(theme.colors.text).forEach(([key, value]) => {
    root.style.setProperty(`--color-text-${key}`, value);
  });

  root.setAttribute('data-theme', theme.mode);
}

const STORAGE_KEY = 'themePreference';

const defaultContextValue: ThemeContextType = {
  theme: lightTheme,
  isDark: false,
  themePreference: 'system',
  setThemePreference: () => { console.warn('ThemeProvider not mounted'); },
};

const ThemeContext = createContext<ThemeContextType>(defaultContextValue);

export const ThemeProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [themePreference, _setThemePreference] = useState<ThemePreference>(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored && ['light', 'dark', 'system'].includes(stored)) {
        return stored as ThemePreference;
      }
    } catch (e) {
      console.error('Failed to load theme preference from localStorage', e);
    }
    return 'system';
  });

  const prefersDarkQuery = useMemo(() => 
    typeof window !== 'undefined' ? window.matchMedia('(prefers-color-scheme: dark)') : null
  , []);
  
  const [systemPrefersDark, setSystemPrefersDark] = useState(prefersDarkQuery?.matches ?? false);

  useEffect(() => {
    if (!prefersDarkQuery) return;
    const listener = (e: MediaQueryListEvent) => setSystemPrefersDark(e.matches);
    prefersDarkQuery.addEventListener('change', listener);
    return () => prefersDarkQuery.removeEventListener('change', listener);
  }, [prefersDarkQuery]);

  const effectiveMode = useMemo(() => {
    return themePreference === 'system'
      ? (systemPrefersDark ? 'dark' : 'light')
      : themePreference;
  }, [themePreference, systemPrefersDark]);

  const theme = useMemo(() => (effectiveMode === 'dark' ? darkTheme : lightTheme), [effectiveMode]);
  const isDark = theme.mode === 'dark';

  useEffect(() => {
    applyThemeVariables(theme);
  }, [theme]);

  const setThemePreference = useCallback((preference: ThemePreference) => {
    try {
      localStorage.setItem(STORAGE_KEY, preference);
      _setThemePreference(preference);
    } catch (e) {
      console.error('Failed to save theme preference to localStorage', e);
    }
  }, []);

  const contextValue = useMemo(() => ({
    theme,
    isDark,
    themePreference,
    setThemePreference,
  }), [theme, isDark, themePreference, setThemePreference]);

  return (
    <ThemeContext.Provider value={contextValue}>
      {children}
    </ThemeContext.Provider>
  );
};

export const useTheme = () => useContext(ThemeContext); 