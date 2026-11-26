import { useState } from 'react';
import { useApp } from '../../state/AppContext';
import { Btn } from '../common/ui';
import { NewReportDialog } from '../dialogs/NewReportDialog';
import { SettingsDialog } from '../dialogs/SettingsDialog';
import { MasterDialog } from '../dialogs/MasterDialog';
import { AuditDialog } from '../dialogs/AuditDialog';
import { OptionMasterDialog } from '../dialogs/OptionMasterDialog';
import { ROLE_LABEL } from '../../auth/permissions';
import { LangSwitch } from '../../i18n';

export function TopBar() {
  const app = useApp();
  const [dlg, setDlg] = useState<'' | 'new' | 'settings' | 'master' | 'audit' | 'options'>('');

  return (
    <div className="topbar no-print">
      <button className="tb tb-home" title="一覧へ戻る" onClick={() => app.goto('list')}>
        <svg className="tb-home-ic" viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M5 12H3l9-9 9 9h-2"/><path d="M5 12v7a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-7"/><path d="M9 21v-6a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2v6"/></svg>
        <span>一覧</span>
      </button>
      <button className="tb tb-beige" disabled={!app.can('edit')} title={app.can('edit') ? undefined : '閲覧のみ'} onClick={() => setDlg('new')}>✎ 新規作成</button>
      <button
        className="tb tb-beige"
        onClick={() => {
          app.goto('list');
          setTimeout(() => document.getElementById('list-search')?.focus(), 50);
        }}
      >
        検索
      </button>
      <button
        className="tb tb-beige"
        onClick={() => {
          app.setFilter({ from: '', to: '', q: '', status: '' });
          app.goto('list');
        }}
      >
        全レコード
      </button>
      <span className="tb-spacer" />
      <span className="tb-registrant">
        登録者
        {app.form ? (
          <select
            className="inp"
            value={app.draft?.report.header.registrant ?? ''}
            onChange={(e) => app.form?.set('report.header.registrant', e.target.value)}
          >
            <option value="" />
            {app.masters.doctors.map((d) => (
              <option key={d}>{d}</option>
            ))}
          </select>
        ) : (
          <span className="calc" style={{ width: 90 }} />
        )}
      </span>
      <button className="tb tb-beige" title="保存先の切替" onClick={() => setDlg('settings')}>
        {app.settings.kind === 'local' ? '💾 Local' : '🌐 Remote DB'}
      </button>
      <button className="tb tb-beige" disabled={!app.can('masters')} title={app.can('masters') ? undefined : '管理者のみ'} onClick={() => setDlg('master')}>マスタ</button>
      <button className="tb tb-beige" disabled={!app.can('masters')} title={app.can('masters') ? '画面の選択肢（アプローチ部位・造影剤・デバイス種別など）の編集' : '管理者のみ'} onClick={() => setDlg('options')}>選択値</button>
      <button className="tb tb-beige" disabled={!app.can('audit')} title={app.can('audit') ? '誰が・いつ・何を変えたかの記録' : '管理者のみ'} onClick={() => setDlg('audit')}>監査ログ</button>
      <button className="tb tb-beige" disabled={!app.draft} title={app.draft ? '表示中のレポートを検査報告書（A4）で表示・印刷' : 'レコード未選択'} onClick={() => app.setPrinting(true)}>🖨 検査報告書</button>
      <LangSwitch />
      {app.user && (
        <span className="tb-user" title={`${app.user.username}（${app.user.roles.map((r) => ROLE_LABEL[r] ?? r).join('・')}）`}>
          👤 {app.user.displayName}
          <button type="button" className="tb tb-beige tb-logout" onClick={() => app.logout()}>ログアウト</button>
        </span>
      )}
      <Btn kind={app.isDirty ? 'dirty' : 'save'} className="tb-save" disabled={!app.draft || !app.can('edit')} onClick={() => void app.save()} title="Ctrl+S">
        保存{app.isDirty ? ' ●' : ''}
      </Btn>
      {dlg === 'new' && <NewReportDialog onClose={() => setDlg('')} />}
      {dlg === 'settings' && <SettingsDialog onClose={() => setDlg('')} />}
      {dlg === 'master' && <MasterDialog onClose={() => setDlg('')} />}
      {dlg === 'audit' && <AuditDialog onClose={() => setDlg('')} />}
      {dlg === 'options' && <OptionMasterDialog onClose={() => setDlg('')} />}
    </div>
  );
}
