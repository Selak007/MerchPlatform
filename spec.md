# Implementation Plan: Add Dark Mode Feature

**GitHub Issue:** https://github.com/Selak007/MerchPlatform/issues/6  
**Project:** MerchPlatform (Lumina Pay) — React + Vite frontend  
**Date:** 2026-03-26

---

## 1. Problem Statement

The Lumina Pay dashboard is currently **hard-coded to a dark theme only**. The Settings page already has a theme toggle (dark/light buttons) that writes to `localStorage`, but selecting "light" does absolutely nothing — no CSS variables change, no class is applied, and every component uses hardcoded dark colors (`#fff`, `rgba(0,0,0,...)`, `rgba(255,255,255,...)`) in both CSS and inline styles.

**Goal:** Make the light/dark toggle fully functional so the entire UI switches seamlessly between dark mode and light mode.

---

## 2. Architecture & Approach

### 2.1 Theme Context (React Context API)

Create a `ThemeContext` that:
- Reads the initial theme from `localStorage` key `lumina-pay-settings` (field `theme`), defaulting to `"dark"`.
- Exposes `{ theme, setTheme }` to the entire component tree.
- On theme change, applies `data-theme="light"` or `data-theme="dark"` to `document.documentElement`.
- Persists the choice back to `localStorage`.

### 2.2 CSS Custom Properties (dual palette)

Define two complete palettes in `index.css` using the `[data-theme]` attribute selector:
- `:root, [data-theme="dark"]` — current dark palette (unchanged).
- `[data-theme="light"]` — new light palette overriding every CSS variable.

### 2.3 Eliminate hardcoded colors in JSX inline styles

Replace every hardcoded color in inline `style={{}}` objects across all components/pages with CSS variable references so they respond to the theme switch.

---

## 3. Detailed File Changes

### 3.1 NEW FILE: `frontend/src/context/ThemeContext.jsx`

```jsx
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
```

### 3.2 MODIFY: `frontend/src/main.jsx`

Wrap `<App />` with `<ThemeProvider>`.

```jsx
import { ThemeProvider } from './context/ThemeContext.jsx';
// ...
createRoot(document.getElementById('root')).render(
  <StrictMode>
    <ThemeProvider>
      <App />
    </ThemeProvider>
  </StrictMode>,
);
```

### 3.3 MODIFY: `frontend/src/index.css` — Add light theme palette

Add the following block **after** the existing `:root { ... }` block:

```css
[data-theme="light"] {
  --bg-color: #f4f6fb;
  --bg-gradient: radial-gradient(circle at 15% 50%, rgba(99, 102, 241, 0.07), transparent 30%),
                 radial-gradient(circle at 85% 30%, rgba(139, 92, 246, 0.05), transparent 30%);
  --sidebar-bg: rgba(255, 255, 255, 0.85);
  --card-bg: rgba(255, 255, 255, 0.75);
  --card-border: rgba(0, 0, 0, 0.08);

  --text-main: #1e293b;
  --text-muted: #64748b;

  --primary: #6366f1;
  --primary-glow: rgba(99, 102, 241, 0.25);
  --secondary: #8b5cf6;
  --success: #059669;
  --warning: #d97706;
  --danger: #dc2626;
  --info: #2563eb;
}
```

Additionally, introduce **new semantic CSS variables** in `:root` (dark defaults) that cover the hardcoded colors currently found in inline styles, and mirror them in `[data-theme="light"]`:

| New Variable | Dark Value | Light Value | Replaces |
|---|---|---|---|
| `--text-heading` | `#ffffff` | `#0f172a` | all `color: '#fff'` in JSX |
| `--bg-inset` | `rgba(0, 0, 0, 0.2)` | `rgba(0, 0, 0, 0.04)` | `background: 'rgba(0,0,0,0.2)'` |
| `--bg-inset-light` | `rgba(0, 0, 0, 0.3)` | `rgba(0, 0, 0, 0.06)` | `background: 'rgba(0,0,0,0.3)'` |
| `--bg-subtle` | `rgba(255,255,255,0.03)` | `rgba(0,0,0,0.02)` | `rgba(255,255,255,0.03)` |
| `--bg-subtle-hover` | `rgba(255,255,255,0.05)` | `rgba(0,0,0,0.04)` | hover backgrounds |
| `--bg-overlay` | `rgba(255,255,255,0.08)` | `rgba(0,0,0,0.06)` | button overlays |
| `--bg-overlay-light` | `rgba(255,255,255,0.1)` | `rgba(0,0,0,0.07)` | chat user msg bg |
| `--grid-stroke` | `rgba(255,255,255,0.05)` | `rgba(0,0,0,0.08)` | Recharts `CartesianGrid` stroke |
| `--bar-track` | `rgba(255,255,255,0.1)` | `rgba(0,0,0,0.08)` | progress bar tracks |
| `--shadow-card` | `0 8px 32px rgba(0,0,0,0.2)` | `0 8px 32px rgba(0,0,0,0.06)` | card box-shadow |

### 3.4 MODIFY: `frontend/src/index.css` — Update existing selectors

- In `.glass-card`, `.glass-card:hover`, `.nav-item:hover`, `.nav-item.active`, `.chat-message.user`, `.alert-item`, `.skeleton`, etc., replace any remaining hardcoded `rgba(255,255,255,...)` backgrounds with the corresponding new variables.
- Update `body` selector: `color: var(--text-main)` (already correct), scrollbar colors for light mode.
- Add a light-mode scrollbar rule:
  ```css
  [data-theme="light"] ::-webkit-scrollbar-track { background: rgba(0,0,0,0.03); }
  [data-theme="light"] ::-webkit-scrollbar-thumb { background: rgba(0,0,0,0.15); }
  ```

### 3.5 MODIFY: `frontend/src/pages/Settings.jsx`

- Import `useTheme` from `../context/ThemeContext.jsx`.
- In the theme toggle buttons, call `setTheme(t)` from context **in addition to** the existing `update('theme', t)` local state call. This ensures the context and `<html>` attribute update immediately.
- Replace all inline `color: '#fff'` with `color: 'var(--text-heading)'`.
- Replace `background: 'rgba(0,0,0,0.3)'` → `background: 'var(--bg-inset-light)'`.
- Replace `background: 'rgba(255,255,255,0.08)'` → `background: 'var(--bg-overlay)'`.
- Replace `background: 'rgba(255,255,255,0.03)'` → `background: 'var(--bg-subtle)'`.
- Replace `boxShadow: '0 8px 32px rgba(0,0,0,0.2)'` → `boxShadow: 'var(--shadow-card)'`.

### 3.6 MODIFY: `frontend/src/pages/Dashboard.jsx`

Replace all inline hardcoded colors:
- `color: '#fff'` → `color: 'var(--text-heading)'`
- `stroke="rgba(255,255,255,0.05)"` on `<CartesianGrid>` → use the CSS variable via a constant `const gridStroke = 'var(--grid-stroke)'` (Recharts accepts CSS variable strings).
- `Tooltip contentStyle` `color: '#fff'` → `color: 'var(--text-heading)'`
- `background: 'rgba(255,255,255,0.05)'` → `background: 'var(--bg-subtle-hover)'`

### 3.7 MODIFY: `frontend/src/pages/Revenue.jsx`

Same pattern as Dashboard:
- Replace `color: '#fff'` → `color: 'var(--text-heading)'`
- Replace Recharts grid stroke and tooltip colors with CSS variables.
- Replace `cursor: { fill: 'rgba(255,255,255,0.05)' }` → `cursor: { fill: 'var(--grid-stroke)' }`

### 3.8 MODIFY: `frontend/src/pages/Customers.jsx`

- Replace `color: '#fff'` → `color: 'var(--text-heading)'`
- Replace Recharts colors as above.

### 3.9 MODIFY: `frontend/src/pages/Risk.jsx`

- Replace `color: '#fff'` → `color: 'var(--text-heading)'`
- Replace `background: 'rgba(255,255,255,0.1)'` → `background: 'var(--bar-track)'`
- Replace `background: 'rgba(255,255,255,0.03)'` → `background: 'var(--bg-subtle)'`
- Replace `background: 'rgba(255,255,255,0.08)'` → `background: 'var(--bg-overlay)'`
- Replace Recharts grid/tooltip/cursor colors.

### 3.10 MODIFY: `frontend/src/pages/Insights.jsx`

- Replace `color: '#fff'` → `color: 'var(--text-heading)'`
- Replace `rgba(255,255,255,0.05)` → `var(--grid-stroke)`

### 3.11 MODIFY: `frontend/src/pages/Assistant.jsx`

- Replace `color: '#fff'` → `color: 'var(--text-heading)'`
- Replace `background: 'rgba(0,0,0,0.2)'` → `background: 'var(--bg-inset)'`

### 3.12 MODIFY: `frontend/src/components/TopHeader.jsx`

- Replace `color: '#fff'` → `color: 'var(--text-heading)'`
- Replace `background: 'rgba(0,0,0,0.3)'` → `background: 'var(--bg-inset-light)'`
- Replace `background: 'rgba(255,255,255,0.05)'` → `background: 'var(--bg-subtle-hover)'`

### 3.13 MODIFY: `frontend/src/components/Sidebar.jsx`

- The sidebar logo uses `color="white"` on the icon — change to `color="var(--text-heading)"` or keep white since it's on a primary-colored badge (acceptable).
- No other changes needed — already uses CSS classes with variables.

### 3.14 MODIFY: `frontend/src/components/NotificationDropdown.jsx`

- Audit for hardcoded colors and replace with CSS variables (same pattern).

### 3.15 MODIFY: `frontend/src/components/AIAssistantPanel.jsx`

- Audit and replace hardcoded colors with CSS variables.

### 3.16 MODIFY: `frontend/src/App.css`

- Replace any `var(--border)` references if they exist (they reference a non-existent variable). This file appears to be leftover Vite scaffolding and may not need changes if unused.

---

## 4. Light Theme Color Palette (Design Reference)

| Element | Dark Mode | Light Mode |
|---|---|---|
| Page background | `#0d0f1a` | `#f4f6fb` |
| Sidebar background | `rgba(18,20,31,0.6)` | `rgba(255,255,255,0.85)` |
| Card background | `rgba(26,28,43,0.5)` | `rgba(255,255,255,0.75)` |
| Card border | `rgba(255,255,255,0.08)` | `rgba(0,0,0,0.08)` |
| Primary text | `#f0f2f5` | `#1e293b` |
| Heading text | `#ffffff` | `#0f172a` |
| Muted text | `#94a3b8` | `#64748b` |
| Card shadow | `rgba(0,0,0,0.2)` | `rgba(0,0,0,0.06)` |
| Page title gradient | `#fff → #a5b4fc` | `#0f172a → #6366f1` |

---

## 5. CSS Variable Strategy for `.page-title` Gradient

Add to `:root`:
```css
--title-gradient-from: #fff;
--title-gradient-to: #a5b4fc;
```
Add to `[data-theme="light"]`:
```css
--title-gradient-from: #0f172a;
--title-gradient-to: #6366f1;
```
Update `.page-title`:
```css
background: linear-gradient(90deg, var(--title-gradient-from), var(--title-gradient-to));
```

---

## 6. Implementation Order

| Step | Task | Files |
|---|---|---|
| 1 | Create `ThemeContext` | `frontend/src/context/ThemeContext.jsx` (new) |
| 2 | Wrap app in `ThemeProvider` | `frontend/src/main.jsx` |
| 3 | Add light CSS palette & new semantic variables | `frontend/src/index.css` |
| 4 | Wire Settings page toggle to context | `frontend/src/pages/Settings.jsx` |
| 5 | Replace hardcoded colors in `Dashboard.jsx` | `frontend/src/pages/Dashboard.jsx` |
| 6 | Replace hardcoded colors in `Revenue.jsx` | `frontend/src/pages/Revenue.jsx` |
| 7 | Replace hardcoded colors in `Customers.jsx` | `frontend/src/pages/Customers.jsx` |
| 8 | Replace hardcoded colors in `Risk.jsx` | `frontend/src/pages/Risk.jsx` |
| 9 | Replace hardcoded colors in `Insights.jsx` | `frontend/src/pages/Insights.jsx` |
| 10 | Replace hardcoded colors in `Assistant.jsx` | `frontend/src/pages/Assistant.jsx` |
| 11 | Replace hardcoded colors in `TopHeader.jsx` | `frontend/src/components/TopHeader.jsx` |
| 12 | Replace hardcoded colors in `AIAssistantPanel.jsx` | `frontend/src/components/AIAssistantPanel.jsx` |
| 13 | Replace hardcoded colors in `NotificationDropdown.jsx` | `frontend/src/components/NotificationDropdown.jsx` |
| 14 | Update `.page-title` gradient in CSS | `frontend/src/index.css` |
| 15 | Smoke test: toggle between dark/light on every page | manual |

---

## 7. Files Summary

| Action | File |
|---|---|
| **CREATE** | `frontend/src/context/ThemeContext.jsx` |
| **MODIFY** | `frontend/src/main.jsx` |
| **MODIFY** | `frontend/src/index.css` |
| **MODIFY** | `frontend/src/pages/Settings.jsx` |
| **MODIFY** | `frontend/src/pages/Dashboard.jsx` |
| **MODIFY** | `frontend/src/pages/Revenue.jsx` |
| **MODIFY** | `frontend/src/pages/Customers.jsx` |
| **MODIFY** | `frontend/src/pages/Risk.jsx` |
| **MODIFY** | `frontend/src/pages/Insights.jsx` |
| **MODIFY** | `frontend/src/pages/Assistant.jsx` |
| **MODIFY** | `frontend/src/components/TopHeader.jsx` |
| **MODIFY** | `frontend/src/components/AIAssistantPanel.jsx` |
| **MODIFY** | `frontend/src/components/NotificationDropdown.jsx` |

**Total: 1 new file, 12 modified files.**

---

## 8. Acceptance Criteria

1. Clicking the "☀️ light" button on the Settings page immediately switches the entire UI to a light color scheme.
2. Clicking "🌙 dark" restores the original dark theme.
3. The chosen theme persists across page reloads (stored in `localStorage`).
4. Every page (Dashboard, Revenue, Customers, Risk, Insights, Assistant, Settings) renders correctly in both modes with no illegible text, invisible elements, or broken contrast.
5. Recharts charts (tooltips, grid lines, bar fills) adapt to the active theme.
6. Sidebar, top header, notifications dropdown, and AI assistant panel all respect the theme.
7. No regressions — all existing functionality continues to work.
