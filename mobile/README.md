# UnisKit Mobile App (Expo)

This directory contains the React Native mobile application for UnisKit, built using Expo.

## Prerequisites

- Ensure you have completed the root-level setup described in the main [README.md](../README.md) at the project root, including installing Node.js and `pnpm`.

## Project Structure Highlights

-   `src/app/`: Contains the application screens and layouts, using Expo Router's file-based routing conventions.
-   `src/assets/`: Static assets like fonts and images.
-   `src/shared/`: UI components (buttons, inputs, layout), context providers (Theme), and hooks specific to the mobile app but potentially reusable within it.
-   `src/features/`: Modules containing code related to specific application features (e.g., `auth`, `settings`).

For more information about the overall project structure and monorepo setup, please refer to the main [README.md](../README.md). 


## Base UI Components & Theming

This mobile application utilizes a set of base UI components located in `src/shared/components/` and a theming system powered by the shared `@/features/shared/` package and React Context.

### Theming (`src/shared/context/ThemeContext.tsx`)

-   **Theme Source:** The core theme definitions (colors, typography including font weights, spacing values like paddings and gaps) are imported from `@/features/shared/`.
-   **Context Provider:** `ThemeContext.tsx` provides the `ThemeProvider` which should wrap the application (done in `src/app/_layout.tsx`). It manages:
    -   Detecting the user's system theme preference (light/dark).
    -   Allowing the user to override the preference (light/dark/system).
    -   Providing the currently active theme object (either `lightTheme` or `darkTheme` from the shared package) and an `isDark` boolean via the `useTheme` hook.
-   **Usage:** Components can consume the theme using `const { theme, isDark } = useTheme();` to access colors, typography styles, spacing values, etc.

### Base Components (`src/shared/components/`)

These components are designed to be the building blocks for screens and features, ensuring consistency with the defined theme.

-   **`ThemedText` (`text/ThemedText.tsx`):**
    -   The foundation for all text rendering.
    -   Takes a `variant` prop (e.g., 'h1', 'body1', 'button') which corresponds to styles defined in the shared theme's typography.
    -   Automatically applies the correct font family (e.g., 'Roboto-Regular', 'Roboto-Bold') based on the `fontWeight` specified for the variant in the theme.
    -   Uses the theme's primary text color by default but can be overridden with the `color` prop.
    -   Aliases like `TextHeader`, `TextBody`, `TextButtonLabel` (in `text/index.tsx`) provide convenient shortcuts for specific variants.

-   **Layout Components (`layout/`):**
    -   Provide consistent spacing and structure (e.g., `BgView`, `PageView`).
    -   Row and Column components (`rows/`, `columns/`) like `BaseRow`, `MediumColumn`, etc., use `gap` values from the shared theme to space their children evenly.
    -   Padding values (like those in `PageView`) are also often sourced from the shared theme's `paddings` object.

-   **Input Components (`inputs/`):**
    -   Base components like `BaseInput` use theme values (`paddings`, `borderRadii`, colors) for consistent styling.

-   **Button Components (`buttons/`):**
    -   `BaseButton` applies theme-based padding, border radius, and uses `ThemedText` (often the 'button' variant) for its label, ensuring font and color consistency.
    -   Specific button types like `PrimaryButton` or `ListButton` build upon `BaseButton` and utilize theme colors and spacing.

**Using the System:**

When building new features or screens, prefer using these base components (e.g., use `TextHeader` instead of `Text style={{...}}`) to maintain consistency with the application's theme and design system. 