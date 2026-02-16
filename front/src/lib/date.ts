/**
 * Format date as relative (today) or absolute (older).
 * Uses browser locale for date/time formatting.
 *
 * @example
 * formatRelativeDate("2026-02-16T14:30:00Z") // "2 min ago" / "3 hours ago"
 * formatRelativeDate("2026-02-15T16:10:00Z") // "Feb 15, 4:10 PM" (en-US) / "15 февр., 16:10" (ru-RU)
 * formatRelativeDate("2025-12-25T09:30:00Z") // "Dec 25, 2025, 9:30 AM" (en-US)
 */
export function formatRelativeDate(dateStr: string): string {
  const date = new Date(dateStr);
  if (isNaN(date.getTime())) return dateStr;
  const now = new Date();

  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const target = new Date(date.getFullYear(), date.getMonth(), date.getDate());
  const isToday = today.getTime() === target.getTime();

  if (isToday) {
    const diffMs = now.getTime() - date.getTime();
    if (diffMs < 0) return "Just now";
    const diffMin = Math.floor(diffMs / 60_000);
    if (diffMin < 1) return "Just now";
    if (diffMin < 60) return `${diffMin} min ago`;
    const diffHours = Math.floor(diffMin / 60);
    return `${diffHours} ${diffHours === 1 ? "hour" : "hours"} ago`;
  }

  const sameYear = date.getFullYear() === now.getFullYear();
  return date.toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
    ...(sameYear ? {} : { year: "numeric" }),
  });
}
