import { useEffect, useState, type CSSProperties, type ReactNode } from 'react';

const cx = (...c: (string | false | undefined | null)[]) => c.filter(Boolean).join(' ');

/** 見出しバー付きパネル */
export function Panel({ title, tone = 'slate', right, children, className, style, bodyStyle }: {
  title?: ReactNode; tone?: 'slate' | 'tan' | 'teal' | 'plain'; right?: ReactNode; children: ReactNode; className?: string; style?: CSSProperties; bodyStyle?: CSSProperties;
}) {
  return (
    <section className={cx('panel', `tone-${tone}`, className)} style={style}>
      {title !== undefined && (
        <header className="ph">
          <span>{title}</span>
          {right && <span className="ph-right">{right}</span>}
        </header>
      )}
      <div className="pb" style={bodyStyle}>
        {children}
      </div>
    </section>
  );
}

export interface TabDef { key: string; label: ReactNode; hasData?: boolean; arrow?: boolean }

export function Tabs({ tabs, active, onChange, small }: { tabs: TabDef[]; active: string; onChange: (k: string) => void; small?: boolean }) {
  return (
    <div className={cx('tabs', small && 'tabs-sm')} role="tablist">
      {tabs.map((t) => (
        <button
          key={t.key}
          type="button"
          role="tab"
          aria-selected={t.key === active}
          className={cx('tab', t.key === active && 'active', t.hasData && 'has-data')}
          onClick={() => onChange(t.key)}
        >
          {t.label}
          {t.arrow && <span className="tab-arrow">▶</span>}
        </button>
      ))}
    </div>
  );
}

/** 画面内タブ。初期値付きの useState をまとめたもの */
export function useTab(initial: string) {
  return useState(initial);
}

export function Modal({ title, children, footer, onClose, width = 520 }: { title: ReactNode; children: ReactNode; footer?: ReactNode; onClose?: () => void; width?: number | string }) {
  useEffect(() => {
    const h = (e: KeyboardEvent) => e.key === 'Escape' && onClose?.();
    window.addEventListener('keydown', h);
    return () => window.removeEventListener('keydown', h);
  }, [onClose]);
  return (
    <div className="modal-back" role="dialog" aria-modal="true">
      <div className="modal" style={{ width }}>
        <header className="modal-h">
          <span>{title}</span>
          {onClose && (
            <button type="button" className="x" onClick={onClose} aria-label="閉じる">
              ×
            </button>
          )}
        </header>
        <div className="modal-b">{children}</div>
        {footer && <footer className="modal-f">{footer}</footer>}
      </div>
    </div>
  );
}

export function Btn({ children, onClick, kind = 'normal', className, title, disabled, small, type = 'button' }: {
  children: ReactNode; onClick?: () => void; kind?: 'normal' | 'primary' | 'danger' | 'save' | 'dirty' | 'ghost'; className?: string; title?: string; disabled?: boolean; small?: boolean; type?: 'button' | 'submit';
}) {
  return (
    <button type={type} className={cx('btn', `btn-${kind}`, small && 'btn-sm', className)} onClick={onClick} title={title} disabled={disabled}>
      {children}
    </button>
  );
}

export function Toast({ msg, kind, id }: { msg: string; kind: 'ok' | 'err'; id: number }) {
  const [show, setShow] = useState(true);
  useEffect(() => {
    setShow(true);
    const t = setTimeout(() => setShow(false), kind === 'err' ? 5000 : 2200);
    return () => clearTimeout(t);
  }, [id, kind]);
  if (!show) return null;
  return <div className={cx('toast', `toast-${kind}`)}>{msg}</div>;
}

/** 注意書き（赤字） */
export const Note = ({ children, color = 'red', style }: { children: ReactNode; color?: string; style?: CSSProperties }) => (
  <div className="note" style={{ color, ...style }}>
    {children}
  </div>
);

export const Row = ({ children, gap = 6, style, wrap = true, align = 'center' }: { children: ReactNode; gap?: number; style?: CSSProperties; wrap?: boolean; align?: CSSProperties['alignItems'] }) => (
  <div style={{ display: 'flex', gap, flexWrap: wrap ? 'wrap' : 'nowrap', alignItems: align, ...style }}>{children}</div>
);

export const Col = ({ children, gap = 3, style }: { children: ReactNode; gap?: number; style?: CSSProperties }) => (
  <div style={{ display: 'flex', flexDirection: 'column', gap, ...style }}>{children}</div>
);

export const Empty = ({ children }: { children: ReactNode }) => <div className="empty">{children}</div>;
