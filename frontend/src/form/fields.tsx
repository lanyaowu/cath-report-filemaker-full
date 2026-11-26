import { useId, type CSSProperties, type ReactNode } from 'react';
import { useField, useForm } from './FormContext';
import { screenName } from '../model/ownership';
import type { Opt } from '../constants/options';
import { useOptionList } from './OptionsContext';

const cx = (...c: (string | false | undefined | null)[]) => c.filter(Boolean).join(' ');

/** 右寄せラベル付きの入力行 */
export function Fld({ label, lw, children, className, style, title }: { label?: ReactNode; lw?: number | string; children: ReactNode; className?: string; style?: CSSProperties; title?: string }) {
  return (
    <div className={cx('f', className)} style={style} title={title}>
      {label !== undefined && (
        <label className="lbl" style={lw !== undefined ? { width: lw, minWidth: lw } : undefined}>
          {label}
        </label>
      )}
      {children}
    </div>
  );
}

interface BaseProps {
  path: string;
  label?: ReactNode;
  lw?: number | string;
  w?: number | string;
  unit?: ReactNode;
  className?: string;
  readOnly?: boolean;
  title?: string;
}

type TextProps = BaseProps & {
  type?: 'text' | 'date' | 'time' | 'number';
  placeholder?: string;
  list?: (string | Opt)[];
  abnormal?: boolean;
  align?: 'left' | 'right' | 'center';
  required?: boolean;
};

export function TextF({ path, label, lw, w, unit, className, readOnly, type = 'text', placeholder, list, abnormal, align, required, title }: TextProps) {
  const f = useField<string>(path);
  const listId = useId();
  const listOpts = useOptionList(list);
  return (
    <Fld label={label} lw={lw}>
      <input
        className={cx('inp', f.changed && 'changed', abnormal && 'abn', required && !f.value && !f.readOnly && 'req', f.ref && 'ref', className)}
        title={f.refTitle ?? title}
        style={{ width: w, textAlign: align }}
        type={type}
        value={f.value ?? ''}
        placeholder={placeholder}
        readOnly={readOnly || f.readOnly}
        list={list ? listId : undefined}
        onChange={(e) => f.set(e.target.value)}
        data-path={f.full}
      />
      {list && (
        <datalist id={listId}>
          {listOpts.map((o) => (
            <option key={o.value} value={o.value}>
              {o.label}
            </option>
          ))}
        </datalist>
      )}
      {unit && <span className="unit">{unit}</span>}
    </Fld>
  );
}

export const NumF = (p: Omit<TextProps, 'type'>) => <TextF align="right" w={56} {...p} />;
export const DateF = (p: Omit<TextProps, 'type'>) => <TextF type="date" w={128} {...p} />;
export const TimeF = (p: Omit<TextProps, 'type'>) => <TextF type="time" w={104} {...p} />;

export function SelectF({ path, label, lw, w, unit, className, options, blank = true }: BaseProps & { options: (string | Opt)[]; blank?: boolean }) {
  const f = useField<string>(path);
  const opts = useOptionList(options, f.value);
  return (
    <Fld label={label} lw={lw}>
      <select
        className={cx('inp', f.changed && 'changed', f.ref && 'ref', className)}
        title={f.refTitle}
        style={{ width: w }}
        value={f.value ?? ''}
        disabled={f.readOnly}
        onChange={(e) => f.set(e.target.value)}
        data-path={f.full}
      >
        {blank && <option value="" />}
        {opts.map((o) => (
          <option key={o.value} value={o.value}>
            {o.label}
          </option>
        ))}
      </select>
      {unit && <span className="unit">{unit}</span>}
    </Fld>
  );
}

export function TextAreaF({ path, label, lw, w, rows = 3, className }: BaseProps & { rows?: number }) {
  const f = useField<string>(path);
  return (
    <Fld label={label} lw={lw} className="f-top">
      <textarea
        className={cx('inp', f.changed && 'changed', f.ref && 'ref', className)}
        title={f.refTitle}
        style={{ width: w ?? '100%' }}
        rows={rows}
        value={f.value ?? ''}
        readOnly={f.readOnly}
        onChange={(e) => f.set(e.target.value)}
        data-path={f.full}
      />
    </Fld>
  );
}

export function CheckF({ path, label, className, title }: { path: string; label?: ReactNode; className?: string; title?: string }) {
  const f = useField<boolean>(path);
  return (
    <label className={cx('chk', f.changed && 'changed', f.ref && 'ref', className)} title={f.refTitle ?? title}>
      <input type="checkbox" checked={!!f.value} disabled={f.readOnly} onChange={(e) => f.set(e.target.checked)} data-path={f.full} />
      {label !== undefined && <span>{label}</span>}
    </label>
  );
}

/** ラジオボタン群。選択中の項目をもう一度クリックすると未選択に戻る */
export function RadioF({ path, label, lw, options, className, compact }: { path: string; label?: ReactNode; lw?: number | string; options: (string | Opt)[]; className?: string; compact?: boolean }) {
  const f = useField<string>(path);
  const name = useId();
  const opts = useOptionList(options, f.value);
  return (
    <Fld label={label} lw={lw}>
      <span className={cx('radios', compact && 'compact', f.changed && 'changed', f.ref && 'ref', className)} data-path={f.full} title={f.refTitle}>
        {opts.map((o) => (
          <label key={o.value} className="rd">
            <input
              type="radio"
              name={name}
              value={o.value}
              checked={f.value === o.value}
              disabled={f.readOnly}
              onChange={() => f.set(o.value)}
              onClick={() => {
                if (f.value === o.value) f.set('');
              }}
            />
            <span>{o.label}</span>
          </label>
        ))}
      </span>
    </Fld>
  );
}

/** 収縮期/拡張期/平均 の3値入力 */
export function TripleF({ path, label, lw, w = 40 }: { path: string; label?: ReactNode; lw?: number | string; w?: number }) {
  return (
    <Fld label={label} lw={lw} className="triple">
      <TextF path={`${path}.s`} w={w} align="right" title="収縮期" />
      <span className="sep">/</span>
      <TextF path={`${path}.d`} w={w} align="right" title="拡張期" />
      <span className="sep">/</span>
      <TextF path={`${path}.m`} w={w} align="right" title="平均" />
    </Fld>
  );
}

/** 計算結果などの表示専用欄 */
export function Calc({ label, lw, value, w = 64, unit, className }: { label?: ReactNode; lw?: number | string; value: ReactNode; w?: number | string; unit?: ReactNode; className?: string }) {
  return (
    <Fld label={label} lw={lw}>
      <span className={cx('calc', className)} style={{ width: w }}>
        {value}
      </span>
      {unit && <span className="unit">{unit}</span>}
    </Fld>
  );
}

/** 日付＋時刻 */
export function DateTimeF({ path, label, lw }: { path: string; label?: ReactNode; lw?: number | string }) {
  return (
    <Fld label={label} lw={lw}>
      <DateF path={`${path}.date`} />
      <TimeF path={`${path}.time`} />
    </Fld>
  );
}

/** 参照項目の編集先へのリンク（例：「カテ記録で編集 →」） */
export function RefLink({ to, children }: { to: import('../state/screens').ScreenKey; children?: ReactNode }) {
  const f = useForm();
  if (f.screen === to) return null;
  return (
    <button type="button" className="ref-link" onClick={() => f.goto(to)} title="編集する画面へ移動">
      {children ?? `${screenName(to)}で編集`} →
    </button>
  );
}
