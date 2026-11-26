import { useApp } from '../state/AppContext';
import { ageAt, fmtDate } from '../utils/date';
import { Btn } from '../components/common/ui';

/** 心カテレポート一覧 */
export function ReportList() {
  const app = useApp();
  const f = app.filter;
  const set = (k: keyof typeof f, v: string) => app.setFilter({ ...f, [k]: v });
  const box = (v: boolean) => <span className={`cbx ${v ? 'on' : ''}`}>{v ? '✔' : ''}</span>;

  return (
    <div className="screen list-screen">
      <div className="list-toolbar">
        <div className="f">
          <label className="lbl">施行日</label>
          <input className="inp" type="date" value={f.from} onChange={(e) => set('from', e.target.value)} />
          <span>〜</span>
          <input className="inp" type="date" value={f.to} onChange={(e) => set('to', e.target.value)} />
        </div>
        <div className="f">
          <label className="lbl">検索</label>
          <input id="list-search" className="inp" style={{ width: 240 }} placeholder="ID・氏名・Cine No・疾病・術者…" value={f.q} onChange={(e) => set('q', e.target.value)} />
        </div>
        <div className="f">
          <label className="lbl">状態</label>
          <select className="inp" value={f.status} onChange={(e) => set('status', e.target.value)}>
            <option value="">すべて</option>
            <option value="入力中">入力中</option>
            <option value="確定">確定</option>
            <option value="unverified">未照合</option>
          </select>
        </div>
        <Btn small onClick={() => app.setFilter({ from: '', to: '', q: '', status: '' })}>クリア</Btn>
        <Btn small onClick={() => window.print()}>一覧印刷</Btn>
        <span className="muted">該当 {app.filteredReports.length} 件{app.loading ? '（読込中…）' : ''}</span>
      </div>

      <div className="scroll list-scroll">
        <table className="tbl list-tbl">
          <thead>
            <tr>
              <th />
              <th />
              <th>施行日</th>
              <th>Cine No</th>
              <th>PCI No</th>
              <th>ID</th>
              <th>氏名</th>
              <th>年齢</th>
              <th>性別</th>
              <th>術者</th>
              <th>主治医</th>
              <th>疾病</th>
              <th>検査項目</th>
              <th>FollowUp</th>
              <th>QCA</th>
              <th>サマリー</th>
              <th>提出</th>
              <th>秘書入力確認</th>
              <th>ステータス</th>
              <th>照合</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {app.filteredReports.map((r) => {
              const p = app.patientOf(r);
              const current = app.draft?.report.id === r.id;
              return (
                <tr key={r.id} className={current ? 'current' : ''} onDoubleClick={() => app.openReport(r.id, 'cathRecord')}>
                  <td>
                    <button type="button" className="open-btn" title="開く" onClick={() => app.openReport(r.id, 'cathRecord')}>
                      📄
                    </button>
                  </td>
                  <td className="urgent">{r.cathRecord.exam.urgency === '緊急' ? '緊急' : ''}</td>
                  <td>{fmtDate(r.header.studyDate)}</td>
                  <td>{r.header.cineNo}</td>
                  <td>{r.header.pciNo}</td>
                  <td>{p?.patientId}</td>
                  <td>{p?.name}</td>
                  <td className="num">{ageAt(p?.birthDate, r.header.studyDate)}</td>
                  <td>{p?.sex}</td>
                  <td>{r.cathRecord.doctors.operators[0]}</td>
                  <td>{r.cathRecord.doctors.attending}</td>
                  <td>{r.cathRecord.exam.disease}</td>
                  <td className="ellipsis">{r.cathRecord.exam.examItems}</td>
                  <td className="c">{box(r.cathRecord.exam.purposes.followUp)}</td>
                  <td className="c">{box(r.header.qca)}</td>
                  <td className="c">{box(r.header.summary)}</td>
                  <td className="c">{box(r.header.submitted)}</td>
                  <td className="c">{box(r.header.secretaryChecked)}</td>
                  <td className={`c status ${r.status === '確定' ? 'fixed' : ''}`}>{r.status}</td>
                  <td className="c">
                    <span className={`badge ${r.verified ? 'badge-ok' : 'badge-ng'}`}>{r.verified ? '照合済' : '未照合'}</span>
                  </td>
                  <td>
                    <button type="button" className="del-btn" title={app.can('deleteReport') ? '削除' : '削除の権限がありません'} disabled={!app.can('deleteReport')} onClick={() => app.deleteReport(r.id)}>
                      ✖
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
