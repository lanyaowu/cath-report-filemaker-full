import { useApp } from '../state/AppContext';
import { useField, useForm, useResolve } from './FormContext';
import { getAt, hasAnyValue } from '../utils/path';

/** 同じ番号で一緒に増減する配列（例：Pressure Wire の病変 ↔ IVUS の Lesion） */
export interface Linked { path: string; create: () => unknown }

/** 連動する配列を n 件にそろえた上で、f(配列) を適用した値を返す */
function useLinked(linked: Linked[]) {
  const form = useForm();
  const resolve = useResolve();
  return (n: number, f: (arr: unknown[], l: Linked) => unknown[]) =>
    linked.map((l) => {
      const p = resolve(l.path);
      const arr = [...((getAt(form.value, p) as unknown[] | undefined) ?? [])];
      while (arr.length < n) arr.push(l.create());
      return [p, f(arr.slice(0, Math.max(arr.length, n)), l)] as [string, unknown];
    });
}

/**
 * 繰り返し項目（行・列の数が可変で、最大数あり）の追加・削除ボタン。
 * - 追加：末尾に空の行を足す。最大数に達したら押せない。
 * - 削除：その行を取り除き、後ろの行を詰める。入力がある行は確認してから削除。
 *   最後の 1 行は取り除かず、入力をクリアする（入力欄が無くならないように）。
 */
export function AddRowBtn<T>({
  path, max, create, label = '追加', disabled, title, linked = [],
}: { path: string; max: number; create: () => T; label?: string; disabled?: boolean; title?: string; linked?: Linked[] }) {
  const f = useField<T[]>(path);
  const form = useForm();
  const others = useLinked(linked);
  const list = Array.isArray(f.value) ? f.value : [];
  const full = list.length >= max;
  const off = disabled || f.readOnly || full;
  return (
    <button
      type="button"
      className="rep-add"
      disabled={off}
      title={full ? `最大 ${max} 件まで入力できます` : title ?? `${label}（最大 ${max} 件）`}
      onClick={() =>
        linked.length
          ? form.setMany([[f.full, [...list, create()]], ...others(list.length, (arr, l) => [...arr.slice(0, list.length), l.create()])])
          : f.set([...list, create()])
      }
    >
      ＋ {label}
      <span className="rep-count">{list.length}/{max}</span>
    </button>
  );
}

export function DelRowBtn<T>({
  path, index, create, what = '行', disabled, linked = [], text, note = '',
}: { path: string; index: number; create: () => T; what?: string; disabled?: boolean; linked?: Linked[]; text?: string; note?: string }) {
  const app = useApp();
  const f = useField<T[]>(path);
  const form = useForm();
  const others = useLinked(linked);
  const list = Array.isArray(f.value) ? f.value : [];
  const off = disabled || f.readOnly;
  const remove = () => {
    const one = list.length <= 1;
    const mine = one ? [create()] : list.filter((_, k) => k !== index);
    if (!linked.length) return f.set(mine);
    form.setMany([
      [f.full, mine],
      ...others(list.length, (arr, l) => (one ? [l.create()] : arr.slice(0, list.length).filter((_, k) => k !== index))),
    ]);
  };
  const filled = hasAnyValue(list[index]) || others(list.length, (arr) => arr).some(([, arr]) => hasAnyValue((arr as unknown[])[index]));
  return (
    <button
      type="button"
      className={text ? 'rep-del-text' : 'rep-del'}
      disabled={off}
      title={list.length <= 1 ? `この${what}の入力をクリア` : `この${what}を削除`}
      onClick={() => {
        if (!filled) return remove();
        app.confirm({
          title: `${what}の削除`,
          message: (list.length <= 1 ? `${what}${index + 1}の入力内容をクリアします。` : `${what}${index + 1}を削除します。後ろの${what}は前に詰めます。`) + note,
          danger: true,
          okLabel: list.length <= 1 ? 'クリア' : '削除',
          onOk: remove,
        });
      }}
    >
      {text ?? '✖'}
    </button>
  );
}

/** 表示する件数（配列の長さ。最低 1） */
export function useCount(path: string): number {
  const f = useField<unknown[]>(path);
  return Math.max(1, Array.isArray(f.value) ? f.value.length : 0);
}

export const range = (n: number) => Array.from({ length: n }, (_, i) => i);
