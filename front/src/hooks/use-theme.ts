import { useCallback, useSyncExternalStore } from "react";

type Theme = "light" | "dark";

const STORAGE_KEY = "theme";

function getTheme(): Theme {
  return document.documentElement.classList.contains("dark") ? "dark" : "light";
}

function setTheme(theme: Theme) {
  if (theme === "dark") {
    document.documentElement.classList.add("dark");
  } else {
    document.documentElement.classList.remove("dark");
  }
  localStorage.setItem(STORAGE_KEY, theme);
}

// Notify subscribers when theme changes
const listeners = new Set<() => void>();
function subscribe(cb: () => void) {
  listeners.add(cb);
  return () => listeners.delete(cb);
}

function applyTheme(theme: Theme) {
  setTheme(theme);
  listeners.forEach((cb) => cb());
}

// Initialize from localStorage on module load
const stored = localStorage.getItem(STORAGE_KEY) as Theme | null;
if (stored === "dark" || stored === "light") {
  setTheme(stored);
}

export function useTheme() {
  const theme = useSyncExternalStore(subscribe, getTheme);

  const toggle = useCallback(() => {
    applyTheme(theme === "dark" ? "light" : "dark");
  }, [theme]);

  return { theme, toggle };
}
