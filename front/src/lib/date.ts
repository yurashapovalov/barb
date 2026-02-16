/**
 * Format date as relative or short.
 *
 * @example
 * formatRelativeDate("2026-02-16T...") // "Today"
 * formatRelativeDate("2026-02-15T...") // "Yesterday"
 * formatRelativeDate("2026-02-10T...") // "Feb 10"
 * formatRelativeDate("2025-12-25T...") // "Dec 25, 2025"
 */
export function formatRelativeDate(dateStr: string): string {
  const date = new Date(dateStr);
  const now = new Date();

  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const target = new Date(date.getFullYear(), date.getMonth(), date.getDate());
  const diffDays = Math.round((today.getTime() - target.getTime()) / (1000 * 60 * 60 * 24));

  if (diffDays === 0) return "Today";
  if (diffDays === 1) return "Yesterday";

  const sameYear = date.getFullYear() === now.getFullYear();
  return date.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    ...(sameYear ? {} : { year: "numeric" }),
  });
}
