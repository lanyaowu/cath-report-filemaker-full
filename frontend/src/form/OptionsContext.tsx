import { createContext, useContext } from 'react';
import { categoryOf, type Opt } from '../constants/options';
import { resolveOptions, type OptionCategory } from '../model/optionMaster';
import { useLang } from '../i18n';

/** 選択値マスタ（カテゴリコード → カテゴリ）。AppProvider が値を入れる */
const OptionsCtx = createContext<ReadonlyMap<string, OptionCategory>>(new Map());
export const OptionsProvider = OptionsCtx.Provider;

export const useOptionMap = () => useContext(OptionsCtx);

/**
 * 画面に出す選択肢。constants/options.ts の cat(...) で定義した配列ならマスタの内容に置き換える。
 * current を渡すと、使用停止・マスタに無い値でも選択肢に残す（保存済みのレポートの表示用）。
 */
export function useOptionList(list: readonly (string | Opt)[] | undefined, current?: string | null): Opt[] {
  const map = useContext(OptionsCtx);
  const lang = useLang();
  if (!list) return [];
  const code = categoryOf(list);
  return resolveOptions(code ? map.get(code) : undefined, list, current, lang);
}
