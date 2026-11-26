/**
 * React 版の多言語表示（日本語・English・中文）。translator.ts（DOM の文言を辞書で置き換える）を 1 つだけ作って使う。
 * 言語は Local Storage（cath.lang）に覚える。
 */
import { useEffect, useState } from 'react';
import { createTranslator, isLang, LANGS, type Dictionary, type Lang } from './translator';
import en from './en.json';
import zh from './zh-CN.json';

export type { Lang } from './translator';
export { LANGS } from './translator';

export const i18n = createTranslator({ en: en as unknown as Dictionary, 'zh-CN': zh as unknown as Dictionary });
const KEY = 'cath.lang';
const listeners = new Set<(l: Lang) => void>();

export function savedLang(): Lang {
  try {
    const v = localStorage.getItem(KEY);
    if (isLang(v)) return v;
  } catch {
    /* Local Storage が使えない環境 */
  }
  return 'ja';
}

export function setLang(l: Lang) {
  try {
    localStorage.setItem(KEY, l);
  } catch {
    /* 覚えられなくても切替はする */
  }
  i18n.setLang(l);
  listeners.forEach((f) => f(l));
}

/** 文字列の翻訳（画面の外に出る文言：CSV の見出し・ダウンロード名など） */
export const t = (s: string) => i18n.t(s);

/** 指定した言語での訳（選択値マスタの入力欄の見本など。画面の言語は変えない） */
const others = new Map<Lang, ReturnType<typeof createTranslator>>();
export function tIn(l: Lang, s: string): string {
  if (l === 'ja') return s;
  let tr = others.get(l);
  if (!tr) {
    tr = createTranslator({ en: en as unknown as Dictionary, 'zh-CN': zh as unknown as Dictionary });
    tr.select(l);
    others.set(l, tr);
  }
  return tr.t(s);
}

/** 現在の言語（切り替えると再描画） */
export function useLang(): Lang {
  const [l, set] = useState<Lang>(i18n.lang);
  useEffect(() => {
    listeners.add(set);
    return () => {
      listeners.delete(set);
    };
  }, []);
  return l;
}

/** 言語の切替（ヘッダー・ログイン画面） */
export function LangSwitch({ className }: { className?: string }) {
  const lang = useLang();
  return (
    <select
      className={`inp lang-switch${className ? ' ' + className : ''}`}
      data-no-i18n=""
      aria-label="言語 / 语言"
      title="言語 / 语言"
      value={lang}
      onChange={(e) => setLang(e.target.value as Lang)}
    >
      {LANGS.map((o) => (
        <option key={o.code} value={o.code}>
          {o.label}
        </option>
      ))}
    </select>
  );
}
