import { useState } from 'react';
import { useApp } from '../../state/AppContext';
import { ReportHistoryDialog } from '../dialogs/ReportHistoryDialog';
import { SCREENS } from '../../state/screens';
import { hasAnyValue } from '../../utils/path';
import { fmtDateTime } from '../../utils/date';
import { confirmMismatches, confirmWarnings } from '../../utils/clinical';

export function SideNav() {
  const app = useApp();
  const d = app.draft;
  const [showHist, setShowHist] = useState(false);
  const ids = app.filteredReports.map((r) => r.id);
  const idx = d ? ids.indexOf(d.report.id) : -1;
  const go = (i: number) => {
    if (i >= 0 && i < ids.length && i !== idx) app.openReport(ids[i]);
  };

  return (
    <nav className="sidenav no-print">
      {SCREENS.map((s) => {
        const active = app.screen === s.key;
        const hasData = d && (s.key === 'patient' ? !!d.patient.name : s.section ? hasAnyValue(d.report[s.section]) : false);
        const disabled = s.needsRecord && !d;
        return (
          <div key={s.key} className={`nav-item ${active ? 'active' : ''} ${hasData ? 'has-data' : ''} ${disabled ? 'disabled' : ''}`}>
            <button type="button" disabled={disabled} onClick={() => app.goto(s.key)}>
              {s.label}
            </button>
            {active && s.section && d && (
              <button type="button" className="trash" title="この画面の入力内容をクリア" onClick={() => app.clearSection(s.section!)}>
                🗑
              </button>
            )}
          </div>
        );
      })}

      <div className="nav-status">
        {d ? (
          <>
            <button
              type="button"
              className={`badge ${d.report.verified ? 'badge-ok' : 'badge-ng'}`}
              title={app.can('verify') ? 'クリックで照合状態を切替' : '照合の権限がありません（医師・管理者）'}
              disabled={!app.can('verify')}
              onClick={() => app.form?.set('report.verified', !d.report.verified)}
            >
              {d.report.verified ? '照合済' : '未照合'}
            </button>
            <button
              type="button"
              className={`badge badge-status ${d.report.status === '確定' ? 'fixed' : ''}`}
              title={app.can('confirm') ? 'クリックで 入力中/確定 を切替' : '確定・確定解除の権限がありません（医師・管理者）'}
              disabled={!app.can('confirm')}
              onClick={() => {
                if (d.report.status === '確定') return app.form?.set('report.status', '入力中');
                // 確定前の確認（警告のみ。施設の決定により確定は止めない）
                const miss = confirmWarnings(d);
                const diff = confirmMismatches(d);
                if (!miss.length && !diff.length) return app.form?.set('report.status', '確定');
                app.confirm({
                  title: '確定前の確認',
                  okLabel: 'このまま確定する',
                  message: (
                    <div className="confirm-list">
                      {miss.length > 0 && (
                        <>
                          <p>次の項目が未入力です（{miss.length}件）。</p>
                          <ul>{miss.map((m) => <li key={m}>{m}</li>)}</ul>
                        </>
                      )}
                      {diff.length > 0 && (
                        <>
                          <p>自動判定と異なる入力があります。</p>
                          <ul>{diff.map((m) => <li key={m}>{m}</li>)}</ul>
                        </>
                      )}
                      <p className="muted small">「キャンセル」で入力に戻ります。このまま確定することもできます（確定後は「入力中」に戻すまで編集できません）。</p>
                    </div>
                  ),
                  onOk: () => app.form?.set('report.status', '確定'),
                });
              }}
            >
              {d.report.status}
            </button>
            {app.isNew && <div className="new-flag">新規（未保存）</div>}
          </>
        ) : (
          <div className="muted">レコード未選択</div>
        )}
      </div>

      <div className="nav-count">
        <div>
          レコード：<b>{idx >= 0 ? idx + 1 : '-'}</b>
        </div>
        <div>
          該当件数：<b>{ids.length}</b>
        </div>
      </div>
      <div className="nav-rec">
        <button type="button" title="先頭" onClick={() => go(0)}>|◀</button>
        <button type="button" title="前" onClick={() => go(idx - 1)}>◀</button>
        <button type="button" title="次" onClick={() => go(idx + 1)}>▶</button>
        <button type="button" title="最後" onClick={() => go(ids.length - 1)}>▶|</button>
      </div>

      <div className="nav-hist-title">レポート登録履歴</div>
      <button type="button" className="nav-hist-btn" disabled={!d || app.isNew} title={!d ? 'レコード未選択' : app.isNew ? '保存後に表示できます' : '誰が・いつ・どの項目を変えたか'} onClick={() => setShowHist(true)}>
        🔍 項目ごとの変更履歴
      </button>
      {showHist && <ReportHistoryDialog onClose={() => setShowHist(false)} />}
      <div className="nav-hist">
        {d?.report.history
          .slice()
          .reverse()
          .map((h, i) => (
            <div key={i} className="hist-row">
              <div>{fmtDateTime(h.at)}</div>
              <div>
                {h.by || '-'} {h.action}
              </div>
            </div>
          ))}
      </div>
    </nav>
  );
}
