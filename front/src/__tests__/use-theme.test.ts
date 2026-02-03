import { describe, it, expect, beforeEach } from "vitest";
import { renderHook, act } from "@testing-library/react";

// jsdom doesn't implement matchMedia — stub it
Object.defineProperty(window, "matchMedia", {
  writable: true,
  value: (query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addEventListener: () => {},
    removeEventListener: () => {},
    dispatchEvent: () => false,
    addListener: () => {},
    removeListener: () => {},
  }),
});

// Reset DOM and localStorage before each test, then import fresh module
beforeEach(() => {
  document.documentElement.classList.remove("dark");
  localStorage.clear();
});

async function importUseTheme() {
  // Force fresh module to reset module-level initialization
  const mod = await import("@/hooks/use-theme");
  return mod.useTheme;
}

describe("useTheme", () => {
  it("defaults to system when no stored preference", async () => {
    const useTheme = await importUseTheme();
    const { result } = renderHook(() => useTheme());
    expect(result.current.preference).toBe("system");
  });

  it("toggle switches from system to explicit theme", async () => {
    const useTheme = await importUseTheme();
    const { result } = renderHook(() => useTheme());

    act(() => {
      result.current.toggle();
    });

    // In jsdom, matchMedia defaults to not matching (light), so toggle goes to dark
    expect(result.current.preference).toBe("dark");
    expect(document.documentElement.classList.contains("dark")).toBe(true);
    expect(localStorage.getItem("theme")).toBe("dark");
  });

  it("toggles from dark back to light", async () => {
    const useTheme = await importUseTheme();
    const { result } = renderHook(() => useTheme());

    act(() => result.current.set("dark"));
    act(() => result.current.toggle());

    expect(result.current.preference).toBe("light");
    expect(document.documentElement.classList.contains("dark")).toBe(false);
    expect(localStorage.getItem("theme")).toBe("light");
  });

  it("set explicitly chooses a theme", async () => {
    const useTheme = await importUseTheme();
    const { result } = renderHook(() => useTheme());

    act(() => result.current.set("dark"));
    expect(result.current.preference).toBe("dark");
    expect(document.documentElement.classList.contains("dark")).toBe(true);

    act(() => result.current.set("light"));
    expect(result.current.preference).toBe("light");
    expect(document.documentElement.classList.contains("dark")).toBe(false);

    act(() => result.current.set("system"));
    expect(result.current.preference).toBe("system");
    expect(localStorage.getItem("theme")).toBe("system");
  });
});
