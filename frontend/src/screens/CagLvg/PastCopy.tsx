import { useApp } from '../../state/AppContext';
import { fmtDate } from '../../utils/date';
import type { CathReport } from '../../types/model';

function usePast(filter: (r: CathReport) => boolean) {
  const app = useApp();
  const d = app.draft!;
  return app.reports
    .filter((r) => r.patientRef === d.patient.id && r.id !== d.report.id && filter(r))
    .sort((a, b) => b.header.studyDate.localeCompare(a.header.studyDate));
}

/** 過去のCAGCommentコピー：同一患者の過去レポートの CAG コメントを target パスへコピー */
export function PastCommentCopy({ target, label = '過去のCAGCommentコピー' }: { target: string; label?: string }) {
  const app = useApp();
  const past = usePast((r) => !!r.cagLvg.cag.comment);
  return (
    <span className="f past-copy">
      <span className="small">{label}</span>
      <select
        className="inp"
        value=""
        onChange={(e) => {
          const r = past.find((x) => x.id === e.target.value);
          if (r) app.form!.set(target, r.cagLvg.cag.comment);
        }}
      >
        <option value="">{past.length ? '選択…' : '（なし）'}</option>
        {past.map((r) => (
          <option key={r.id} value={r.id}>
            {fmtDate(r.header.studyDate)} {r.cagLvg.cag.comment.slice(0, 24)}
          </option>
        ))}
      </select>
    </span>
  );
}

/** 過去のCAG所見コピー：セグメント所見・側副血行路・バイパスグラフトを複写 */
export function PastCagCopy() {
  const app = useApp();
  const past = usePast((r) => Object.values(r.cagLvg.cag.segments).some((s) => s.stenosis));
  return (
    <span className="f past-copy">
      <span className="small">過去のCAG所見コピー</span>
      <select
        className="inp"
        value=""
        onChange={(e) => {
          const r = past.find((x) => x.id === e.target.value);
          if (!r) return;
          app.form!.setMany([
            ['report.cagLvg.cag.segments', r.cagLvg.cag.segments],
            ['report.cagLvg.cag.collaterals', r.cagLvg.cag.collaterals],
            ['report.cagLvg.cag.collateralsNone', r.cagLvg.cag.collateralsNone],
            ['report.cagLvg.cag.grafts', r.cagLvg.cag.grafts],
          ]);
          app.toast(`${fmtDate(r.header.studyDate)} の所見をコピーしました`);
        }}
      >
        <option value="">{past.length ? '選択…' : '（なし）'}</option>
        {past.map((r) => (
          <option key={r.id} value={r.id}>
            {fmtDate(r.header.studyDate)} {r.cathRecord.exam.examItems}
          </option>
        ))}
      </select>
    </span>
  );
}
