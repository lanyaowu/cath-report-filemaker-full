import { useMemo } from 'react';
import { useApp } from '../state/AppContext';
import { Panel } from '../components/common/ui';
import { amiTimes } from './Pci/AmiTab';

function Bars({ data }: { data: [string, number][] }) {
  const max = Math.max(1, ...data.map(([, v]) => v));
  return (
    <table className="bars">
      <tbody>
        {data.map(([k, v]) => (
          <tr key={k}>
            <th>{k}</th>
            <td>
              <div className="bar" style={{ width: `${(v / max) * 100}%` }} />
            </td>
            <td className="num">{v}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

/** 集計（一覧の絞込条件に連動） */
export function StatsScreen() {
  const app = useApp();
  const rs = app.filteredReports;
  const s = useMemo(() => {
    const byMonth = new Map<string, number>();
    const byDisease = new Map<string, number>();
    const byItem = new Map<string, number>();
    let pci = 0, urgent = 0, fixed = 0, verified = 0, lesions = 0, success = 0;
    const d2b: number[] = [];
    for (const r of rs) {
      const m = r.header.studyDate.slice(0, 7) || '不明';
      byMonth.set(m, (byMonth.get(m) ?? 0) + 1);
      const dz = r.cathRecord.exam.disease || '未入力';
      byDisease.set(dz, (byDisease.get(dz) ?? 0) + 1);
      for (const it of r.cathRecord.exam.examItems.split(/[,、\s]+/).filter(Boolean)) byItem.set(it, (byItem.get(it) ?? 0) + 1);
      if (r.cathRecord.exam.purposes.PCI || r.pci.lesions.some((l) => l.target)) pci++;
      if (r.cathRecord.exam.urgency === '緊急') urgent++;
      if (r.status === '確定') fixed++;
      if (r.verified) verified++;
      for (const l of r.pci.lesions) {
        if (!l.target) continue;
        lesions++;
        if (l.success === 'Success' || l.device.result === 'Success') success++;
      }
      const t = amiTimes(r.pci.ami).d2b;
      if (t != null) d2b.push(t);
    }
    const sort = (m: Map<string, number>) => [...m.entries()].sort((a, b) => b[1] - a[1]);
    return {
      byMonth: [...byMonth.entries()].sort((a, b) => a[0].localeCompare(b[0])),
      byDisease: sort(byDisease),
      byItem: sort(byItem).slice(0, 12),
      pci, urgent, fixed, verified, lesions, success,
      d2bMedian: d2b.length ? d2b.sort((a, b) => a - b)[Math.floor(d2b.length / 2)] : null,
    };
  }, [rs]);

  const kpi = (label: string, v: string | number) => (
    <div className="kpi">
      <div className="kpi-v">{v}</div>
      <div className="kpi-l">{label}</div>
    </div>
  );

  return (
    <div className="screen">
      <div className="kpis">
        {kpi('検査件数', rs.length)}
        {kpi('PCI件数', s.pci)}
        {kpi('緊急', s.urgent)}
        {kpi('確定', s.fixed)}
        {kpi('照合済', s.verified)}
        {kpi('PCI病変数', s.lesions)}
        {kpi('病変成功率', s.lesions ? `${Math.round((s.success / s.lesions) * 100)}%` : '-')}
        {kpi('D2B中央値', s.d2bMedian != null ? `${s.d2bMedian}分` : '-')}
      </div>
      <div className="cols">
        <Panel title="月別件数"><Bars data={s.byMonth} /></Panel>
        <Panel title="疾病別"><Bars data={s.byDisease} /></Panel>
        <Panel title="検査項目別（上位）"><Bars data={s.byItem} /></Panel>
      </div>
      <p className="muted small">※一覧画面の絞込条件（施行日・検索・状態）が反映されます。</p>
    </div>
  );
}
