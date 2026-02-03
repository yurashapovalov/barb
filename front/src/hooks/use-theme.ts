import { useSyncExternalStore } from "react";

export type ThemePreference = "system" | "light" | "dark";

const STORAGE_KEY = "theme";

function getSystemTheme(): "light" | "dark" {
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

function resolve(pref: ThemePreference): "light" | "dark" {
  return pref === "system" ? getSystemTheme() : pref;
}

function applyToDOM(theme: "light" | "dark") {
  document.documentElement.classList.toggle("dark", theme === "dark");
}

function getPreference(): ThemePreference {
  const stored = localStorage.getItem(STORAGE_KEY);
  if (stored === "light" || stored === "dark" || stored === "system") return stored;
  return "system";
}

const listeners = new Set<() => void>();
function subscribe(cb: () => void) {
  listeners.add(cb);
  return () => listeners.delete(cb);
}

function setPreference(pref: ThemePreference) {
  localStorage.setItem(STORAGE_KEY, pref);
  applyToDOM(resolve(pref));
  listeners.forEach((cb) => cb());
}

// Initialize on module load
applyToDOM(resolve(getPreference()));

// React to OS theme changes when in system mode
window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", () => {
  if (getPreference() === "system") {
    applyToDOM(getSystemTheme());
  }
});

export function useTheme() {
  const preference = useSyncExternalStore(subscribe, getPreference);

  return {
    preference,
    set: setPreference,
    toggle: () => {
      const current = resolve(preference);
      setPreference(current === "dark" ? "light" : "dark");
    },
  };
}
