import { describe, it, expect, beforeEach } from "vitest";
import { renderHook, act } from "@testing-library/react";

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
  it("defaults to light when no stored preference", async () => {
    const useTheme = await importUseTheme();
    const { result } = renderHook(() => useTheme());
    expect(result.current.theme).toBe("light");
    expect(document.documentElement.classList.contains("dark")).toBe(false);
  });

  it("toggles from light to dark", async () => {
    const useTheme = await importUseTheme();
    const { result } = renderHook(() => useTheme());

    act(() => {
      result.current.toggle();
    });

    expect(result.current.theme).toBe("dark");
    expect(document.documentElement.classList.contains("dark")).toBe(true);
    expect(localStorage.getItem("theme")).toBe("dark");
  });

  it("toggles from dark back to light", async () => {
    const useTheme = await importUseTheme();
    const { result } = renderHook(() => useTheme());

    act(() => result.current.toggle());
    act(() => result.current.toggle());

    expect(result.current.theme).toBe("light");
    expect(document.documentElement.classList.contains("dark")).toBe(false);
    expect(localStorage.getItem("theme")).toBe("light");
  });

  it("persists theme to localStorage", async () => {
    const useTheme = await importUseTheme();
    const { result } = renderHook(() => useTheme());

    act(() => result.current.toggle());
    expect(localStorage.getItem("theme")).toBe("dark");

    act(() => result.current.toggle());
    expect(localStorage.getItem("theme")).toBe("light");
  });
});
