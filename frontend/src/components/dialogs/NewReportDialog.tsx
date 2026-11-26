import { useMemo, useState } from 'react';
import { useApp } from '../../state/AppContext';
import { Btn, Modal } from '../common/ui';
import { ageAt, fmtDate } from '../../utils/date';

/** 新規作成：既存患者を選択 or 新規患者 */
export function NewReportDialog({ onClose }: { onClose: () => void }) {
  const app = useApp();
  const [q, setQ] = useState('');
  const list = useMemo(() => {
    const s = q.trim().toLowerCase();
    return app.patients.filter((p) => !s || `${p.patientId} ${p.name} ${p.kana}`.toLowerCase().includes(s));
  }, [app.patients, q]);

  return (
    <Modal
      title="新規カテレポート作成"
      onClose={onClose}
      width={620}
      footer={
        <>
          <Btn
            kind="primary"
            onClick={() => {
              onClose();
              app.newReport(null);
            }}
          >
            新規患者で作成
          </Btn>
          <Btn onClick={onClose}>閉じる</Btn>
        </>
      }
    >
      <div className="f" style={{ marginBottom: 6 }}>
        <label className="lbl">患者検索</label>
        <input className="inp" style={{ width: 300 }} autoFocus placeholder="ID・氏名・フリガナ" value={q} onChange={(e) => setQ(e.target.value)} />
      </div>
      <div className="scroll" style={{ maxHeight: 340 }}>
        <table className="tbl">
          <thead>
            <tr>
              <th>ID</th>
              <th>氏名</th>
              <th>フリガナ</th>
              <th>性別</th>
              <th>生年月日</th>
              <th>年齢</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {list.map((p) => (
              <tr key={p.id}>
                <td>{p.patientId}</td>
                <td>{p.name}</td>
                <td>{p.kana}</td>
                <td>{p.sex}</td>
                <td>{fmtDate(p.birthDate)}</td>
                <td>{ageAt(p.birthDate)}</td>
                <td>
                  <Btn
                    small
                    kind="primary"
                    onClick={() => {
                      onClose();
                      app.newReport(p);
                    }}
                  >
                    選択
                  </Btn>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Modal>
  );
}
