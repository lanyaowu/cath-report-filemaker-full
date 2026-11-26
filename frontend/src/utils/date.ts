export const pad2 = (n: number) => String(n).padStart(2, '0');

export function today(): string {
  const d = new Date();
  return `${d.getFullYear()}-${pad2(d.getMonth() + 1)}-${pad2(d.getDate())}`;
}

export function nowIso(): string {
  return new Date().toISOString();
}

/** YYYY-MM-DD → YYYY/MM/DD */
export function fmtDate(s?: string): string {
  return s ? s.replace(/-/g, '/') : '';
}

export function fmtDateTime(iso?: string): string {
  if (!iso) return '';
  const d = new Date(iso);
  if (isNaN(d.getTime())) return iso;
  return `${d.getFullYear()}/${pad2(d.getMonth() + 1)}/${pad2(d.getDate())} ${pad2(d.getHours())}:${pad2(d.getMinutes())}`;
}

/** 基準日時点の満年齢 */
export function ageAt(birth?: string, at?: string): string {
  if (!birth) return '';
  const b = new Date(birth);
  const a = at ? new Date(at) : new Date();
  if (isNaN(b.getTime()) || isNaN(a.getTime())) return '';
  let age = a.getFullYear() - b.getFullYear();
  const m = a.getMonth() - b.getMonth();
  if (m < 0 || (m === 0 && a.getDate() < b.getDate())) age--;
  return age >= 0 ? String(age) : '';
}

/** 日数差（to - from）。どちらかが空なら '' */
export function diffDays(from?: string, to?: string): string {
  if (!from || !to) return '';
  const f = new Date(from);
  const t = new Date(to);
  if (isNaN(f.getTime()) || isNaN(t.getTime())) return '';
  return String(Math.round((t.getTime() - f.getTime()) / 86400000));
}

function toMs(date?: string, time?: string): number | null {
  if (!date || !time) return null;
  const d = new Date(`${date}T${time}`);
  return isNaN(d.getTime()) ? null : d.getTime();
}

/** 2つの日時の差を分で返す */
export function diffMinutes(a: { date: string; time: string }, b: { date: string; time: string }): number | null {
  const x = toMs(a.date, a.time);
  const y = toMs(b.date, b.time);
  if (x == null || y == null) return null;
  return Math.round((y - x) / 60000);
}

export function fmtMinutes(min: number | null): string {
  if (min == null) return '';
  const sign = min < 0 ? '-' : '';
  const m = Math.abs(min);
  return `${sign}${Math.floor(m / 60)}:${pad2(m % 60)} (${min}分)`;
}
