import { Fragment, useCallback, useEffect, useState } from 'react';
import { useApp } from '../../state/AppContext';
import { Btn, Modal } from '../common/ui';
import { fmtDateTime } from '../../utils/date';
import { AUDIT_ACTION_LABEL, actionLabel, auditCsv, TARGET_LABEL, type AuditEntry, type AuditQuery } from '../../audit/model';
import { pathLabel, valueText } from '../../audit/labels';

const today = () => new Date(Date.now() + 9 * 3600_000).toISOString().slice(0, 10);
const daysAgo = (n: number) => new Date(Date.now() + 9 * 3600_000 - n * 86400_000).toISOString().slice(0, 10);

/** 変わった項目の表（監査ログ画面・レポートの変更履歴で共通） */
export function ChangeTable({ entry }: { entry: AuditEntry }) {
  if (!entry.changes?.length) return <div className="muted audit-nochange">変わった項目はありません</div>;
  return (
    <table className="tbl audit-changes">
      <thead>
        <tr>
          <th style={{ width: '42%' }}>項目</th>
          <th>変更前</th>
          <th>変更後</th>
        </tr>
      </thead>
      <tbody>
        {entry.changes.map((c) => (
          <tr key={c.path}>
            <td>
              <div>{pathLabel(c.path, entry.targetType)}</div>
              <div className="audit-path">{c.path}</div>
            </td>
            <td className={c.before === '' ? 'audit-empty' : 'audit-before'}>{valueText(c.before)}</td>
            <td className={c.after === '' ? 'audit-empty' : 'audit-after'}>{valueText(c.after)}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

export function downloadText(name: string, text: string, type = 'text/csv') {
  const url = URL.createObjectURL(new Blob([text], { type }));
  const a = document.createElement('a');
  a.href = url;
  a.download = name;
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

/** 監査ログ（管理者のみ）：期間・利用者・操作・対象で絞り込み、変わった項目を確かめる。CSV で出力 */
export function AuditDialog({ onClose }: { onClose: () => void }) {
  const app = useApp();
  const [q, setQ] = useState<AuditQuery>({ from: daysAgo(30), to: today(), username: '', action: '', targetType: '', targetId: '', limit: 500 });
  const [list, setList] = useState<AuditEntry[] | null>(null);
  const [open, setOpen] = useState<Set<string>>(new Set());
  const [err, setErr] = useState('');

  const search = useCallback(async (x: AuditQuery) => {
    setErr('');
    try {
      setList(await app.adapter.listAudit({ ...x, withChanges: true }));
      setOpen(new Set());
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
      setList([]);
    }
  }, [app.adapter]);

  useEffect(() => {
    void search(q);
    // 開いた時に 1 回だけ検索する
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const set = (k: keyof AuditQuery) => (e: { target: { value: string } }) => setQ({ ...q, [k]: e.target.value });
  const toggle = (id: string) => setOpen((s) => {
    const n = new Set(s);
    if (n.has(id)) n.delete(id);
    else n.add(id);
    return n;
  });
  const patientName = (e: AuditEntry) => {
    if (e.targetType === 'patient') return app.patients.find((p) => p.id === e.targetId)?.name ?? '';
    if (e.targetType === 'report') {
      const r = app.reports.find((x) => x.id === e.targetId);
      const p = r && app.patients.find((x) => x.id === r.patientRef);
      return p ? `${p.name}（${r!.header.studyDate}）` : '';
    }
    return '';
  };

  return (
    <Modal
      title="監査ログ"
      onClose={onClose}
      width={1180}
      footer={
        <>
          <Btn
            disabled={!list?.length}
            onClick={() => list && downloadText(`audit_${q.from || 'all'}_${q.to || ''}.csv`, auditCsv(list, pathLabel))}
            title="表示中の記録を CSV で保存（変わった項目は 1 項目 1 行）"
          >
            CSV 出力
          </Btn>
          <Btn onClick={onClose}>閉じる</Btn>
        </>
      }
    >
      <form
        className="audit-filter"
        onSubmit={(e: { preventDefault: () => void }) => {
          e.preventDefault();
          void search(q);
        }}
      >
        <label>期間 <input type="date" className="inp" value={q.from} onChange={set('from')} aria-label="開始日" /></label>〜
        <input type="date" className="inp" value={q.to} onChange={set('to')} aria-label="終了日" />
        <label>利用者 <input className="inp" style={{ width: 90 }} value={q.username} onChange={set('username')} placeholder="ユーザー名" /></label>
        <label>
          操作{' '}
          <select className="inp" value={q.action} onChange={set('action')}>
            <option value="">（すべて）</option>
            {Object.entries(AUDIT_ACTION_LABEL).map(([k, v]) => (
              <option key={k} value={k}>{v}</option>
            ))}
          </select>
        </label>
        <label>
          対象{' '}
          <select className="inp" value={q.targetType} onChange={set('targetType')}>
            <option value="">（すべて）</option>
            <option value="report">レポート</option>
            <option value="patient">患者</option>
            <option value="user">利用者</option>
            <option value="masters">マスタ</option>
          </select>
        </label>
        <label>対象ID <input className="inp" style={{ width: 120 }} value={q.targetId} onChange={set('targetId')} placeholder="rp-… / pt-…" /></label>
        <Btn kind="primary" type="submit" small>検索</Btn>
        <span className="muted">{list ? `${list.length} 件${list.length >= (q.limit ?? 500) ? `（上限 ${q.limit} 件）` : ''}` : '検索中…'}</span>
      </form>
      {err && <div className="audit-err">{err}</div>}
      <div className="scroll audit-scroll">
        <table className="tbl audit-list">
          <thead>
            <tr>
              <th style={{ width: 128 }}>日時</th>
              <th style={{ width: 110 }}>利用者</th>
              <th style={{ width: 120 }}>操作</th>
              <th>対象</th>
              <th style={{ width: 64 }}>変更項目</th>
              <th style={{ width: 150 }}>詳細</th>
            </tr>
          </thead>
          <tbody>
            {list?.map((e) => (
              <Fragment key={e.id}>
                <tr className={e.changeCount ? 'audit-row has-changes' : 'audit-row'} onClick={() => e.changeCount && toggle(e.id)} data-id={e.id}>
                  <td>{fmtDateTime(e.at)}</td>
                  <td title={e.username}>{e.displayName || e.username || '-'}</td>
                  <td className={`audit-act act-${e.action.split('_')[0].toLowerCase()}`}>{actionLabel(e.action)}</td>
                  <td>
                    {TARGET_LABEL[e.targetType] ?? e.targetType} <span className="audit-path">{e.targetId}</span> {patientName(e)}
                  </td>
                  <td className="num">{e.changeCount ? <button type="button" className="linkish">{open.has(e.id) ? '▼' : '▶'} {e.changeCount}</button> : ''}</td>
                  <td>{e.detail}</td>
                </tr>
                {open.has(e.id) && (
                  <tr className="audit-detail">
                    <td colSpan={6}><ChangeTable entry={e} /></td>
                  </tr>
                )}
              </Fragment>
            ))}
            {list && !list.length && (
              <tr>
                <td colSpan={6} className="c muted">該当する記録はありません</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
      {app.adapter.kind === 'local' && <div className="muted small">Local Storage（体験用）：記録はこのブラウザ内だけに残り、最新 2,000 件までです。</div>}
    </Modal>
  );
}
