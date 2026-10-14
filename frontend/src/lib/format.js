export const STATUSES = ['SCHEDULED', 'CHECKED_IN', 'COMPLETED', 'CANCELLED'];

export function statusLabel(status) {
  return status
    .toLowerCase()
    .split('_')
    .map((word) => word[0].toUpperCase() + word.slice(1))
    .join(' ');
}

// The next action a receptionist can take for an appointment, or null if it's final.
export function nextStatus(status) {
  return { SCHEDULED: 'CHECKED_IN', CHECKED_IN: 'COMPLETED' }[status] ?? null;
}

export function initials(name) {
  return name
    .replace(/^Dr\.?\s+/i, '')
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0].toUpperCase())
    .join('');
}

export function formatTime(iso, locale) {
  return new Date(iso).toLocaleTimeString(locale, { hour: '2-digit', minute: '2-digit' });
}

export function formatDay(iso, locale) {
  return new Date(iso).toLocaleDateString(locale, { weekday: 'short', day: 'numeric', month: 'short' });
}

// <input type="datetime-local"> gives local wall-clock time; the API stores UTC.
export function localInputToIso(value) {
  return new Date(value).toISOString();
}

// Default booking slot: the next half hour from now, as a datetime-local string.
export function nextHalfHourInput(now = new Date()) {
  const d = new Date(now);
  d.setSeconds(0, 0);
  d.setMinutes(d.getMinutes() < 30 ? 30 : 60);
  const pad = (n) => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

export function greeting(now = new Date()) {
  const hour = now.getHours();
  if (hour < 12) return 'Good morning';
  if (hour < 17) return 'Good afternoon';
  return 'Good evening';
}
