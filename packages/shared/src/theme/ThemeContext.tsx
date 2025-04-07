import React, {
  createContext,
  useContext,
  useState,
  useEffect,
  useMemo,
  useCallback,
} from 'react';
import { Platform, Appearance, ColorSchemeName } from 'react-native';
import {
  lightTheme,
  darkTheme,
  Theme,
  // ThemePreference, // Define below
  // ThemeContextType, // Define below
} from './theme'; // Import from shared theme index
import { StorageInterface } from '../storage/StorageInterface';

// --- Define missing types --- 
export type ThemePreference = 'light' | 'dark' | 'system';

export type ThemeContextType = {
  theme: Theme;
  isDark: boolean;
  themePreference: ThemePreference;
  setThemePreference: (preference: ThemePreference) => void; // Keep it simple, async handled internally
};

const THEME_STORAGE_KEY = 'themePreference';

// --- Helper to apply theme variables for web --- 
function applyThemeVariablesWeb(theme: Theme) {
  if (Platform.OS !== 'web') return;
  const root = document.documentElement;
  if (!root) return;

  // Clear previous theme variables (optional but safer)
  // Consider removing only variables with a specific prefix if needed
  // Array.from(root.style).forEach(key => {
  //   if (key.startsWith('--color-') || key.startsWith('--brand-') /* ...etc */) {
  //     root.style.removeProperty(key);
  //   }
  // });

  // Set root data attribute for global CSS targeting
  root.setAttribute('data-theme', theme.mode);

  // Flatten theme colors and set CSS variables
  const setVariables = (obj: Record<string, any>, prefix = '' ) => {
    Object.entries(obj).forEach(([key, value]) => {
      const cssVarName = `--${prefix}${prefix ? '-' : ''}${key}`.toLowerCase();
      if (typeof value === 'object' && value !== null) {
        // Skip nested objects like button styles for now, handle if needed
        if(prefix !== 'colors' || key !== 'button') {
           setVariables(value, `${prefix}${prefix ? '-' : ''}${key}`);
        }
      } else if (typeof value === 'string' || typeof value === 'number'){
        root.style.setProperty(cssVarName, String(value));
        // Set RGB version for colors if possible (needed for box-shadow)
        if (typeof value === 'string' && value.startsWith('#')) {
          const rgb = hexToRgb(value);
          if (rgb) {
            root.style.setProperty(`${cssVarName}-rgb`, rgb);
          }
        }
      }
    });
  };
  
  setVariables(theme.colors, 'color'); // e.g., --color-brand-primary
  // Add spacing, typography vars if desired (using theme.spacing, theme.typography)
  // setVariables(theme.spacing, 'spacing'); 
  // setVariables(theme.typography, 'typography');
}

function hexToRgb(hex: string): string | null {
  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
  return result
    ? `${parseInt(result[1], 16)}, ${parseInt(result[2], 16)}, ${parseInt(result[3], 16)}`
    : null;
}
// --- End Web Helper ---

// --- Default Context Value ---
const defaultContextValue: ThemeContextType = {
  theme: lightTheme,
  isDark: false,
  themePreference: 'system',
  setThemePreference: () => { console.warn('ThemeProvider not mounted'); },
};

const ThemeContext = createContext<ThemeContextType>(defaultContextValue);

// --- ThemeProvider Component --- 
interface ThemeProviderProps {
  children: React.ReactNode;
  /** Platform-specific storage implementation */
  storage?: StorageInterface; 
  /** Initial preference if storage is not available or empty */
  initialPreference?: ThemePreference;
}

export const ThemeProvider: React.FC<ThemeProviderProps> = ({
  children,
  storage, // Use injected storage
  initialPreference = 'system',
}) => {
  const [themePreference, _setThemePreference] = useState<ThemePreference>(initialPreference);
  const [isSystemDark, setIsSystemDark] = useState<boolean | null>(null); // null = unknown initially

  // Effect to load initial preference from storage
  useEffect(() => {
    let isMounted = true;
    const loadPreference = async () => {
      if (!storage) return;
      try {
        const stored = await storage.getItem(THEME_STORAGE_KEY);
        if (isMounted && stored && ['light', 'dark', 'system'].includes(stored)) {
          _setThemePreference(stored as ThemePreference);
        } else if (isMounted) {
          _setThemePreference(initialPreference); // Fallback if nothing stored
        }
      } catch (e) {
        console.error('Failed to load theme preference from storage', e);
         if (isMounted) _setThemePreference(initialPreference); // Fallback on error
      }
    };
    loadPreference();
    return () => { isMounted = false; }; // Cleanup
  }, [storage, initialPreference]);

  // Effect to detect system theme changes
  useEffect(() => {
    let colorScheme: ColorSchemeName;
    let subscription: ReturnType<typeof Appearance.addChangeListener> | null = null;
    let mediaQueryList: MediaQueryList | null = null;
    let mediaQueryListener: ((e: MediaQueryListEvent) => void) | null = null;

    if (Platform.OS === 'web') {
      mediaQueryList = window.matchMedia('(prefers-color-scheme: dark)');
      colorScheme = mediaQueryList.matches ? 'dark' : 'light';
      setIsSystemDark(colorScheme === 'dark');
      mediaQueryListener = (e: MediaQueryListEvent) => {
        setIsSystemDark(e.matches);
      };
      mediaQueryList.addEventListener('change', mediaQueryListener);
    } else {
      colorScheme = Appearance.getColorScheme();
      setIsSystemDark(colorScheme === 'dark');
      subscription = Appearance.addChangeListener(({ colorScheme: newColorScheme }) => {
        setIsSystemDark(newColorScheme === 'dark');
      });
    }

    return () => {
      if (Platform.OS === 'web' && mediaQueryList && mediaQueryListener) {
        mediaQueryList.removeEventListener('change', mediaQueryListener);
      } else {
        subscription?.remove();
      }
    };
  }, []);

  // Determine effective theme mode
  const effectiveMode = useMemo(() => {
    if (isSystemDark === null) return 'light'; // Default to light until detected
    return themePreference === 'system'
      ? (isSystemDark ? 'dark' : 'light')
      : themePreference;
  }, [themePreference, isSystemDark]);

  // Memoize theme object
  const theme = useMemo(() => (effectiveMode === 'dark' ? darkTheme : lightTheme), [effectiveMode]);
  const isDark = theme.mode === 'dark';

  // Effect to apply theme changes (CSS vars for web)
  useEffect(() => {
    if (Platform.OS === 'web') {
      applyThemeVariablesWeb(theme);
    }
    // Native components get theme via context value below
  }, [theme]);

  // Callback to set preference and save to storage
  const setThemePreference = useCallback(async (preference: ThemePreference) => {
    _setThemePreference(preference); // Update state immediately
    if (storage) {
      try {
        await storage.setItem(THEME_STORAGE_KEY, preference);
      } catch (e) {
        console.error('Failed to save theme preference to storage', e);
      }
    } else {
      console.warn('Theme preference not persisted: No storage provided.');
    }
  }, [storage]);

  // Final context value
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

// --- useTheme Hook --- 
export const useTheme = (): ThemeContextType => {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  // Return default value if context is somehow still the initial default object
  // This can happen in rare cases or tests if provider isn't properly mounted
  if (context.setThemePreference === defaultContextValue.setThemePreference) {
     console.warn('useTheme called outside of a fully initialized ThemeProvider?');
     return defaultContextValue;
  }
  return context;
}; 