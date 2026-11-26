/** ドット区切りパス（例: "report.pci.lesions.0.target"）でネストした値を読み書きするユーティリティ */

export function getAt(obj: unknown, path: string): any {
  if (!path) return obj;
  let cur: any = obj;
  for (const k of path.split('.')) {
    if (cur == null) return undefined;
    cur = cur[k];
  }
  return cur;
}

/** イミュータブルに値を設定し、新しいオブジェクトを返す */
export function setAt<T>(obj: T, path: string, value: unknown): T {
  const keys = path.split('.');
  const rec = (cur: any, i: number): any => {
    const k = keys[i];
    const isIdx = /^\d+$/.test(k);
    const base: any = cur == null ? (isIdx ? [] : {}) : Array.isArray(cur) ? [...cur] : { ...cur };
    base[k] = i === keys.length - 1 ? value : rec(cur?.[k], i + 1);
    return base;
  };
  return rec(obj, 0);
}

export const joinPath = (...parts: (string | number | undefined | null)[]) =>
  parts.filter((p) => p !== undefined && p !== null && p !== '').join('.');

export const deepEqual = (a: unknown, b: unknown) => JSON.stringify(a) === JSON.stringify(b);

export const clone = <T>(v: T): T => JSON.parse(JSON.stringify(v));

/**
 * 既定値（全項目を持つ構造）に保存済みデータを重ねる。
 * 保存データに欠けた項目は既定値で補完されるため、項目追加後の旧データも安全に読み込める。
 */
export function mergeDefaults<T>(def: T, src: any): T {
  if (src === undefined || src === null) return def;
  if (Array.isArray(def)) {
    if (!Array.isArray(src)) return def;
    if (def.length === 0) return src as any;
    const n = Math.max(def.length, src.length);
    return Array.from({ length: n }, (_, i) => (i < def.length ? mergeDefaults(def[i], src[i]) : src[i])) as any;
  }
  if (def !== null && typeof def === 'object') {
    if (typeof src !== 'object' || Array.isArray(src)) return def;
    const out: any = { ...src };
    for (const k of Object.keys(def as any)) out[k] = mergeDefaults((def as any)[k], src[k]);
    return out;
  }
  if (typeof def === 'boolean') return (typeof src === 'boolean' ? src : def) as any;
  if (typeof def === 'string') return (src == null ? def : String(src)) as any;
  return src;
}

/** 文字列・真偽値いずれかに入力がある項目を数える（サイドメニューの「入力あり」表示に使用） */
export function hasAnyValue(v: unknown): boolean {
  if (v == null) return false;
  if (typeof v === 'string') return v.trim() !== '';
  if (typeof v === 'boolean') return v;
  if (typeof v === 'number') return true;
  if (Array.isArray(v)) return v.some(hasAnyValue);
  if (typeof v === 'object') return Object.values(v as object).some(hasAnyValue);
  return false;
}
