import { createContext, useContext, type ReactNode } from 'react';
import { getAt, joinPath } from '../utils/path';
import { ownerOf, screenName, type Ownership } from '../model/ownership';
import type { ScreenKey } from '../state/screens';

/**
 * フォームバインディング。
 * - 入力コンポーネントは path（ドット区切り）だけを受け取り、値の取得・更新・変更判定を行う。
 * - <Scope path="report.cathRecord"> で相対パスの起点を指定できる。
 * - "/" で始まるパスは絶対パス（スコープを無視）。画面間で共有する項目に使用する。
 * - highlight=true（遷移ダイアログで「キャンセル」選択時）は、保存値から変更された項目を黄色表示する。
 */
export interface FormApi {
  value: unknown;
  original: unknown;
  set: (path: string, v: unknown) => void;
  setMany: (entries: [string, unknown][]) => void;
  highlight: boolean;
  /** レポート確定済み（全項目ロック） */
  readOnly: boolean;
  /** 表示中の画面（共有項目の編集可否判定に使用） */
  screen: ScreenKey;
  goto: (s: ScreenKey) => void;
}

const FormContext = createContext<FormApi | null>(null);
const ScopeContext = createContext<string>('');

export function FormProvider({ api, children }: { api: FormApi; children: ReactNode }) {
  return <FormContext.Provider value={api}>{children}</FormContext.Provider>;
}

export function Scope({ path, children }: { path: string; children: ReactNode }) {
  const parent = useContext(ScopeContext);
  return <ScopeContext.Provider value={resolvePath(parent, path)}>{children}</ScopeContext.Provider>;
}

export function resolvePath(scope: string, path: string): string {
  if (path.startsWith('/')) return path.slice(1);
  return joinPath(scope, path);
}

export function useForm(): FormApi {
  const f = useContext(FormContext);
  if (!f) throw new Error('FormProvider がありません');
  return f;
}

export function useScope() {
  return useContext(ScopeContext);
}

/** スコープ相対のパスを絶対パスへ */
export function useResolve() {
  const scope = useScope();
  return (p: string) => resolvePath(scope, p);
}

export function useField<T = string>(path: string) {
  const f = useForm();
  const scope = useScope();
  const full = resolvePath(scope, path);
  const value = getAt(f.value, full) as T;
  const orig = getAt(f.original, full);
  const isChanged =
    typeof value === 'object' && value !== null ? JSON.stringify(value) !== JSON.stringify(orig) : (value ?? '') !== (orig ?? '');
  const own = ownerOf(full);
  const ref: Ownership | null = own && !own.owner.includes(f.screen) ? own : null;
  return {
    full,
    value,
    set: (v: T) => f.set(full, v),
    changed: f.highlight && isChanged,
    readOnly: f.readOnly || !!ref,
    /** 参照表示（他画面が主） */
    ref,
    refTitle: ref ? `参照のみ：「${ref.owner.map(screenName).join('」「')}」画面で編集します` : f.readOnly ? '確定済みのため編集できません' : undefined,
  };
}

/** 値の読み取り専用（スコープ相対） */
export function useVal<T = any>(path: string): T {
  const f = useForm();
  const scope = useScope();
  return getAt(f.value, resolvePath(scope, path)) as T;
}
